"""Capability-aware, privacy-aware routing across configured model providers."""

from __future__ import annotations

import ipaddress
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, TypeVar
from urllib.parse import urlparse

from .providers import EmbeddingResponse, LLMProvider, LLMRequest, LLMResponse, MediaRequest, MediaResponse, ProviderError, ProviderRegistry, StreamChunk

CAPABILITIES = {"text", "code", "vision", "image_generation", "video_generation", "audio", "embeddings", "streaming", "structured_output", "tool_calling"}


def validate_endpoint(url: str, *, local: bool = False) -> str:
    """Validate a user-supplied endpoint without making a network request."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("endpoint must use http or https")
    if not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("endpoint must have a host and must not contain credentials or fragments")
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ValueError("endpoint port must be between 1 and 65535")
    if not local and parsed.scheme != "https":
        raise ValueError("non-local endpoints must use https")
    return parsed.geturl().rstrip("/")


@dataclass(frozen=True)
class RoutingRequest:
    required_capabilities: frozenset[str] = frozenset({"text"})
    preferred_provider_ids: tuple[str, ...] = ()
    local_only: bool = False
    allow_fallback: bool = True
    require_healthy: bool = False
    privacy_class: str | None = None

    def __post_init__(self) -> None:
        unknown = set(self.required_capabilities) - CAPABILITIES
        if unknown:
            raise ValueError(f"unknown capabilities: {sorted(unknown)}")
        if self.privacy_class is not None and self.privacy_class not in {"local_only", "cloud_approved", "restricted"}:
            raise ValueError("privacy_class must be local_only, cloud_approved, or restricted")


@dataclass(frozen=True)
class RoutingAttempt:
    provider_id: str
    success: bool
    error: str | None = None
    retry_count: int = 0


_T = TypeVar("_T")


@dataclass(frozen=True)
class RoutingResult:
    provider_id: str
    attempts: tuple[RoutingAttempt, ...]


class ProviderRouter:
    """Select providers by capability and execute with controlled fallback."""

    def __init__(
        self,
        registry: ProviderRegistry,
        *,
        failure_threshold: int = 3,
        cooldown_seconds: float = 30.0,
        retry_attempts: int = 2,
        backoff_base_seconds: float = 0.5,
        backoff_max_seconds: float = 8.0,
        sleep_fn: Callable[[float], None] = time.sleep,
        policy_store: object | None = None,
        rate_limit_store: object | None = None,
        usage_store: object | None = None,
        circuit_store: object | None = None,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be positive")
        if cooldown_seconds <= 0:
            raise ValueError("cooldown_seconds must be positive")
        if retry_attempts < 0:
            raise ValueError("retry_attempts must not be negative")
        if backoff_base_seconds < 0 or backoff_max_seconds < backoff_base_seconds:
            raise ValueError("backoff limits are invalid")
        self.registry = registry
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.retry_attempts = retry_attempts
        self.backoff_base_seconds = backoff_base_seconds
        self.backoff_max_seconds = backoff_max_seconds
        self.sleep_fn = sleep_fn
        self.policy_store = policy_store
        self.rate_limit_store = rate_limit_store
        self.usage_store = usage_store
        self.circuit_store = circuit_store
        self._failures: dict[str, tuple[int, float]] = {}

    def discover_capabilities(self, provider_id: str) -> dict[str, bool]:
        provider = next((item for item in self.registry.providers() if item.config.provider_id == provider_id), None)
        if provider is None:
            raise KeyError(f"provider not found: {provider_id}")
        health = provider.health_check()
        discovered = health.get("capabilities") if isinstance(health, dict) else None
        return dict(discovered or provider.config.capabilities.to_dict())

    def _is_open(self, provider_id: str) -> bool:
        if self.circuit_store is not None:
            return self.circuit_store.state(
                provider_id,
                failure_threshold=self.failure_threshold,
                cooldown_seconds=self.cooldown_seconds,
            ) == "open"
        failures, opened_at = self._failures.get(provider_id, (0, 0.0))
        return failures >= self.failure_threshold and (time.monotonic() - opened_at) < self.cooldown_seconds

    def _record_failure(self, provider_id: str) -> None:
        if self.circuit_store is not None:
            self.circuit_store.record_failure(provider_id)
            return
        failures, _ = self._failures.get(provider_id, (0, 0.0))
        self._failures[provider_id] = (failures + 1, time.monotonic())

    def _record_success(self, provider_id: str) -> None:
        if self.circuit_store is not None:
            self.circuit_store.record_success(provider_id)
            return
        self._failures.pop(provider_id, None)

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """Classify transient failures without exposing provider response bodies."""
        if isinstance(exc, (TimeoutError, OSError, ConnectionError)):
            return True
        message = str(exc).lower()
        return any(marker in message for marker in (
            "timeout", "timed out", "temporarily", "temporary", "rate limit",
            "rate_limit", "429", "502", "503", "504", "unavailable", "overloaded",
            "connection", "network", "try again",
        ))

    def _call_with_retries(self, operation: Callable[[], _T]) -> tuple[_T, int]:
        retries = 0
        while True:
            try:
                return operation(), retries
            except (ProviderError, OSError, TimeoutError) as exc:
                if retries >= self.retry_attempts or not self._is_retryable(exc):
                    raise
                delay = min(self.backoff_base_seconds * (2 ** retries), self.backoff_max_seconds)
                if delay:
                    self.sleep_fn(delay)
                retries += 1

    def circuit_state(self, provider_id: str) -> str:
        """Return closed, open, or half_open without performing a provider call."""
        if self.circuit_store is not None:
            return self.circuit_store.state(
                provider_id,
                failure_threshold=self.failure_threshold,
                cooldown_seconds=self.cooldown_seconds,
            )
        failures, opened_at = self._failures.get(provider_id, (0, 0.0))
        if failures < self.failure_threshold:
            return "closed"
        return "open" if (time.monotonic() - opened_at) < self.cooldown_seconds else "half_open"

    def candidates(self, request: RoutingRequest) -> list[LLMProvider]:
        providers = list(self.registry.providers())
        preferred = {provider_id: index for index, provider_id in enumerate(request.preferred_provider_ids)}
        eligible = []
        policy = self.policy_store.get(request.privacy_class) if self.policy_store and request.privacy_class else None
        if request.privacy_class in {"local_only", "restricted"} or (policy and policy.local_only):
            request = RoutingRequest(required_capabilities=request.required_capabilities, preferred_provider_ids=request.preferred_provider_ids, local_only=True, allow_fallback=request.allow_fallback, require_healthy=request.require_healthy, privacy_class=request.privacy_class)
        for provider in providers:
            config = provider.config
            if policy and policy.allowed_provider_ids and config.provider_id not in policy.allowed_provider_ids:
                continue
            provider_type = config.provider_type.lower().replace("_", "-")
            local_provider_types = {"ollama", "custom-local", "custom-local-ollama", "ollama-compatible", "openai-compatible-local", "llama-cpp", "transformers"}
            if request.local_only and provider_type not in local_provider_types:
                continue
            if self._is_open(config.provider_id):
                continue
            capabilities = config.capabilities.to_dict()
            if request.require_healthy:
                try:
                    health = provider.health_check()
                except (ProviderError, OSError, TimeoutError):
                    continue
                if isinstance(health, dict) and health.get("status") not in {None, "ok", "healthy", "available"}:
                    continue
                discovered = health.get("capabilities") if isinstance(health, dict) else None
                if isinstance(discovered, dict):
                    capabilities.update({key: bool(value) for key, value in discovered.items() if key in CAPABILITIES})
            if not request.required_capabilities.issubset({key for key, enabled in capabilities.items() if enabled}):
                continue
            eligible.append(provider)
        def priority(provider: LLMProvider) -> tuple[int, int]:
            provider_id = provider.config.provider_id
            provider_type = provider.config.provider_type.lower().replace("_", "-")
            if preferred.get(provider_id) is not None:
                return (0, preferred[provider_id])
            if provider_type in {"blackbox-relay", "managed-blackbox", "orville-blackbox-relay"} or provider_id == "blackbox-managed":
                return (1, 0)
            if provider_type == "blackbox":
                return (2, 0)
            if provider_type in {"ollama", "custom-local", "custom-local-ollama", "ollama-compatible", "openai-compatible-local"}:
                return (4, 0)
            return (3, 0)

        return sorted(eligible, key=priority)

    def generate(self, llm_request: LLMRequest, routing: RoutingRequest = RoutingRequest()) -> tuple[LLMResponse, RoutingResult]:
        providers = self.candidates(routing)
        if not providers:
            raise ProviderError("no configured provider satisfies the requested capabilities and privacy policy")
        attempts = []
        for index, provider in enumerate(providers):
            if index and not routing.allow_fallback:
                break
            try:
                if self.rate_limit_store:
                    allowed, reason = self.rate_limit_store.admit(provider.config.provider_id, calls=1)
                    if not allowed:
                        raise ProviderError(reason)
                started = time.perf_counter()
                response, retry_count = self._call_with_retries(lambda: provider.generate(llm_request))
                if self.usage_store:
                    usage = response.usage or {}
                    self.usage_store.record(scope=f"provider:{provider.config.provider_id}", category="llm_generation", provider_id=provider.config.provider_id, units=1, input_tokens=int(usage.get("input_tokens", 0)), output_tokens=int(usage.get("output_tokens", 0)), latency_ms=(time.perf_counter() - started) * 1000, status="success")
                self._record_success(provider.config.provider_id)
                attempts.append(RoutingAttempt(provider.config.provider_id, True, retry_count=retry_count))
                return response, RoutingResult(provider.config.provider_id, tuple(attempts))
            except (ProviderError, OSError, TimeoutError, PermissionError) as exc:
                if self.usage_store:
                    self.usage_store.record(scope=f"provider:{provider.config.provider_id}", category="llm_generation", provider_id=provider.config.provider_id, units=1, latency_ms=0, status="failed", metadata={"error": type(exc).__name__})
                self._record_failure(provider.config.provider_id)
                attempts.append(RoutingAttempt(provider.config.provider_id, False, str(exc), retry_count=self.retry_attempts if self._is_retryable(exc) else 0))
        raise ProviderError("all eligible providers failed: " + "; ".join(f"{item.provider_id}: {item.error}" for item in attempts))

    def generate_media(self, media_request: MediaRequest, routing: RoutingRequest) -> tuple[MediaResponse, RoutingResult]:
        providers = self.candidates(routing)
        if not providers:
            raise ProviderError("no configured provider satisfies the requested media capability and privacy policy")
        attempts: list[RoutingAttempt] = []
        for index, provider in enumerate(providers):
            if index and not routing.allow_fallback:
                break
            try:
                method = getattr(provider, "generate_media", None)
                if method is None:
                    raise ProviderError(f"provider {provider.config.provider_id} has no media-generation adapter")
                response, retry_count = self._call_with_retries(lambda: method(media_request))
                self._record_success(provider.config.provider_id)
                attempts.append(RoutingAttempt(provider.config.provider_id, True, retry_count=retry_count))
                return response, RoutingResult(provider.config.provider_id, tuple(attempts))
            except (ProviderError, OSError, TimeoutError) as exc:
                self._record_failure(provider.config.provider_id)
                attempts.append(RoutingAttempt(provider.config.provider_id, False, str(exc)))
        raise ProviderError("all eligible media providers failed: " + "; ".join(f"{item.provider_id}: {item.error}" for item in attempts))

    def stream(self, llm_request: LLMRequest, routing: RoutingRequest = RoutingRequest()) -> Iterable[StreamChunk]:
        providers = self.candidates(routing)
        if not providers:
            raise ProviderError("no configured provider satisfies the requested streaming capabilities and privacy policy")
        attempts: list[RoutingAttempt] = []
        for index, provider in enumerate(providers):
            if index and not routing.allow_fallback:
                break
            try:
                chunks = provider.stream(llm_request)
                first = True
                for chunk in chunks:
                    first = False
                    yield chunk
                self._record_success(provider.config.provider_id)
                attempts.append(RoutingAttempt(provider.config.provider_id, True))
                return
            except (ProviderError, OSError, TimeoutError) as exc:
                self._record_failure(provider.config.provider_id)
                attempts.append(RoutingAttempt(provider.config.provider_id, False, str(exc)))
                if not first:
                    raise ProviderError(f"stream failed after partial output from {provider.config.provider_id}: {exc}") from exc
        raise ProviderError("all eligible streaming providers failed: " + "; ".join(f"{item.provider_id}: {item.error}" for item in attempts))

    def embed(self, inputs: str | list[str], routing: RoutingRequest | None = None) -> tuple[EmbeddingResponse, RoutingResult]:
        routing = routing or RoutingRequest(required_capabilities=frozenset({"embeddings"}))
        providers = self.candidates(routing)
        attempts = []
        if not providers:
            raise ProviderError("no configured provider satisfies the requested embedding capabilities")
        for index, provider in enumerate(providers):
            if index and not routing.allow_fallback:
                break
            try:
                response, retry_count = self._call_with_retries(lambda: provider.embed(inputs))
                self._record_success(provider.config.provider_id)
                attempts.append(RoutingAttempt(provider.config.provider_id, True, retry_count=retry_count))
                return response, RoutingResult(provider.config.provider_id, tuple(attempts))
            except (ProviderError, OSError, TimeoutError) as exc:
                self._record_failure(provider.config.provider_id)
                attempts.append(RoutingAttempt(provider.config.provider_id, False, str(exc)))
        raise ProviderError("all eligible embedding providers failed: " + "; ".join(f"{item.provider_id}: {item.error}" for item in attempts))
