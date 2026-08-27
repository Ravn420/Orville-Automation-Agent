import unittest

from orville_core import (
    LLMRequest,
    LLMResponse,
    ModelCapabilities,
    ProviderConfig,
    ProviderError,
    ProviderRegistry,
    ProviderRouter,
    RoutingRequest,
    validate_endpoint,
)


class FakeProvider:
    def __init__(self, config, text="ok", error=None):
        self.config = config
        self.text = text
        self.error = error

    def generate(self, request):
        if self.error:
            raise ProviderError(self.error)
        return LLMResponse(self.config.provider_id, self.config.model, self.text, {})

    def stream(self, request):
        if self.error:
            raise ProviderError(self.error)
        yield type("Chunk", (), {"text": self.text})()

    def embed(self, inputs):
        if self.error:
            raise ProviderError(self.error)
        return type("Embedding", (), {"embeddings": [[1.0]]})()

    def health_check(self):
        return {"ok": not self.error}


class RoutingTests(unittest.TestCase):
    def test_endpoint_validation_requires_https_for_non_local(self):
        self.assertEqual(validate_endpoint("http://localhost:11434", local=True), "http://localhost:11434")
        self.assertEqual(validate_endpoint("https://example.com/api"), "https://example.com/api")
        with self.assertRaises(ValueError):
            validate_endpoint("http://example.com")
        with self.assertRaises(ValueError):
            validate_endpoint("https://user:pass@example.com")

    def test_router_filters_by_capability_and_preference(self):
        registry = ProviderRegistry()
        registry.register(FakeProvider(ProviderConfig("text", "ollama", "text", "http://localhost", capabilities=ModelCapabilities(text=True))))
        registry.register(FakeProvider(ProviderConfig("vision", "ollama", "vision", "http://localhost", capabilities=ModelCapabilities(vision=True))))
        router = ProviderRouter(registry)
        candidates = router.candidates(RoutingRequest(frozenset({"vision"})))
        self.assertEqual([provider.config.provider_id for provider in candidates], ["vision"])

    def test_router_falls_back_after_provider_failure(self):
        registry = ProviderRegistry()
        registry.register(FakeProvider(ProviderConfig("first", "ollama", "one", "http://localhost"), error="offline"))
        registry.register(FakeProvider(ProviderConfig("second", "ollama", "two", "http://localhost"), text="fallback"))
        response, result = ProviderRouter(registry).generate(LLMRequest([{"role": "user", "content": "hi"}]))
        self.assertEqual(response.text, "fallback")
        self.assertEqual(result.provider_id, "second")
        self.assertFalse(result.attempts[0].success)
        self.assertTrue(result.attempts[1].success)

    def test_local_only_excludes_cloud_provider(self):
        registry = ProviderRegistry()
        registry.register(FakeProvider(ProviderConfig("cloud", "gemini", "gemini", "https://example.com")))
        registry.register(FakeProvider(ProviderConfig("local", "ollama", "llama", "http://localhost")))
        candidates = ProviderRouter(registry).candidates(RoutingRequest(local_only=True))
        self.assertEqual([provider.config.provider_id for provider in candidates], ["local"])

    def test_local_only_accepts_gateway_runtime_provider(self):
        registry = ProviderRegistry()
        registry.register(FakeProvider(ProviderConfig("gateway", "openai-compatible-local", "local-model", "http://localhost:8000/v1")))
        registry.register(FakeProvider(ProviderConfig("cloud", "openai", "remote", "https://example.com")))
        candidates = ProviderRouter(registry).candidates(RoutingRequest(local_only=True))
        self.assertEqual([provider.config.provider_id for provider in candidates], ["gateway"])

    def test_capability_discovery_uses_provider_health_metadata(self):
        registry = ProviderRegistry()
        provider = FakeProvider(ProviderConfig("local", "ollama", "model", "http://localhost"))
        provider.health_check = lambda: {"ok": True, "capabilities": {"text": True, "vision": True}}
        registry.register(provider)
        self.assertTrue(ProviderRouter(registry).discover_capabilities("local")["vision"])

    def test_circuit_breaker_suppresses_repeated_failures(self):
        registry = ProviderRegistry()
        failing = FakeProvider(ProviderConfig("bad", "ollama", "model", "http://localhost"), error="offline")
        registry.register(failing)
        router = ProviderRouter(registry, failure_threshold=2, cooldown_seconds=60)
        request = LLMRequest([{"role": "user", "content": "hi"}])
        for _ in range(2):
            with self.assertRaises(ProviderError):
                router.generate(request)
        self.assertEqual(router.candidates(RoutingRequest()), [])

    def test_stream_and_embedding_route(self):
        registry = ProviderRegistry()
        registry.register(FakeProvider(ProviderConfig("local", "ollama", "model", "http://localhost", capabilities=ModelCapabilities(embeddings=True, streaming=True))))
        router = ProviderRouter(registry)
        chunks = list(router.stream(LLMRequest([{"role": "user", "content": "hi"}]), RoutingRequest(frozenset({"streaming"}))))
        self.assertEqual(chunks[0].text, "ok")
        embeddings, result = router.embed("hello")
        self.assertEqual(embeddings.embeddings, [[1.0]])
        self.assertEqual(result.provider_id, "local")


if __name__ == "__main__":
    unittest.main()


class ProviderResilienceTests(unittest.TestCase):
    def _registry(self, first, second=None):
        registry = ProviderRegistry()
        registry.register(first)
        if second is not None:
            registry.register(second)
        return registry

    def test_retryable_failure_uses_exponential_backoff_before_success(self):
        class Flaky(FakeProvider):
            def __init__(self, config):
                super().__init__(config)
                self.calls = 0

            def generate(self, request):
                self.calls += 1
                if self.calls < 3:
                    raise ProviderError("temporary upstream outage")
                return LLMResponse(self.config.provider_id, self.config.model, "recovered", {})

        delays = []
        provider = Flaky(ProviderConfig("flaky", "ollama", "model", "http://localhost"))
        router = ProviderRouter(
            self._registry(provider),
            retry_attempts=2,
            backoff_base_seconds=0.25,
            backoff_max_seconds=1.0,
            sleep_fn=delays.append,
        )
        response, result = router.generate(LLMRequest([{"role": "user", "content": "hi"}]))
        self.assertEqual(response.text, "recovered")
        self.assertEqual(provider.calls, 3)
        self.assertEqual(delays, [0.25, 0.5])
        self.assertEqual(result.attempts[0].retry_count, 2)

    def test_non_retryable_failure_falls_back_without_sleep(self):
        delays = []
        first = FakeProvider(ProviderConfig("first", "ollama", "one", "http://localhost"), error="invalid request")
        second = FakeProvider(ProviderConfig("second", "ollama", "two", "http://localhost"), text="fallback")
        router = ProviderRouter(self._registry(first, second), retry_attempts=3, sleep_fn=delays.append)
        response, result = router.generate(LLMRequest([{"role": "user", "content": "hi"}]))
        self.assertEqual(response.text, "fallback")
        self.assertEqual(delays, [])
        self.assertEqual([item.provider_id for item in result.attempts], ["first", "second"])

    def test_circuit_transitions_open_then_half_open_after_cooldown(self):
        provider = FakeProvider(ProviderConfig("bad", "ollama", "model", "http://localhost"), error="temporary outage")
        router = ProviderRouter(self._registry(provider), failure_threshold=1, cooldown_seconds=30, retry_attempts=0)
        request = LLMRequest([{"role": "user", "content": "hi"}])
        with self.assertRaises(ProviderError):
            router.generate(request)
        self.assertEqual(router.circuit_state("bad"), "open")
        router._failures["bad"] = (1, time.monotonic() - 31)
        self.assertEqual(router.circuit_state("bad"), "half_open")
        self.assertEqual(router.candidates(RoutingRequest())[0].config.provider_id, "bad")

    def test_local_only_privacy_never_falls_back_to_cloud(self):
        local = FakeProvider(ProviderConfig("local", "ollama", "local", "http://localhost"), error="temporary outage")
        cloud = FakeProvider(ProviderConfig("cloud", "gemini", "cloud", "https://example.com"), text="must-not-use")
        router = ProviderRouter(self._registry(local, cloud), retry_attempts=0)
        with self.assertRaises(ProviderError) as error:
            router.generate(
                LLMRequest([{"role": "user", "content": "private"}]),
                RoutingRequest(privacy_class="local_only"),
            )
        self.assertIn("local", str(error.exception))
        self.assertNotIn("cloud", str(error.exception))

    def test_router_rejects_invalid_resilience_limits(self):
        registry = ProviderRegistry()
        with self.assertRaises(ValueError):
            ProviderRouter(registry, retry_attempts=-1)
        with self.assertRaises(ValueError):
            ProviderRouter(registry, backoff_base_seconds=2, backoff_max_seconds=1)


import time


if __name__ == "__main__":
    unittest.main()
