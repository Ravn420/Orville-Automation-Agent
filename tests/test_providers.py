import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orville_core.providers import OpenAICompatibleAdapter
from orville_core import (
    CustomLocalAdapter,
    GeminiAdapter,
    HuggingFaceAdapter,
    LLMRequest,
    LLMResponse,
    LocalModelCatalog,
    MediaRequest,
    ModelCapabilities,
    OllamaAdapter,
    ProviderConfig,
    ProviderError,
    StableHordeAdapter,
    create_provider,
)


class FakeHttp:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def stream_json(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        for response in self.responses:
            if isinstance(response, Exception):
                raise response
            yield response
        self.responses = []


class ProviderTests(unittest.TestCase):
    def test_ollama_generation_normalizes_response(self):
        http = FakeHttp([{"message": {"content": "hello", "tool_calls": []}, "done_reason": "stop", "prompt_eval_count": 3, "eval_count": 5}])
        config = ProviderConfig("local", "ollama", "llama3", "http://localhost:11434")
        response = OllamaAdapter(config, http).generate(LLMRequest([{"role": "user", "content": "hi"}]))
        self.assertEqual(response.text, "hello")
        self.assertEqual(response.usage["output_tokens"], 5)
        self.assertIn("/api/chat", http.calls[0][1])

    def test_ollama_structured_output_and_tools_are_sent(self):
        http = FakeHttp([{"message": {"content": "{}"}}])
        config = ProviderConfig("local", "ollama", "model", "http://localhost:11434")
        OllamaAdapter(config, http).generate(LLMRequest(
            [{"role": "user", "content": "return json"}],
            response_schema={"type": "object"},
            tools=[{"type": "function", "function": {"name": "lookup"}}],
        ))
        payload = http.calls[0][2]["payload"]
        self.assertEqual(payload["format"], {"type": "object"})
        self.assertEqual(payload["tools"][0]["type"], "function")

    def test_gemini_generation_builds_contents_and_schema(self):
        http = FakeHttp([{"candidates": [{"content": {"parts": [{"text": "{}"}]}, "finishReason": "STOP"}], "usageMetadata": {"promptTokenCount": 4, "candidatesTokenCount": 2}}])
        config = ProviderConfig("cloud", "gemini", "gemini-test", "https://generativelanguage.googleapis.com", api_key="secret")
        response = GeminiAdapter(config, http).generate(LLMRequest(
            [{"role": "system", "content": "be concise"}, {"role": "user", "content": "return json"}], response_schema={"type": "object"}
        ))
        self.assertEqual(response.text, "{}")
        self.assertEqual(response.usage["input_tokens"], 4)
        self.assertIn("generateContent", http.calls[0][1])
        self.assertIn("systemInstruction", http.calls[0][2]["payload"])
        self.assertNotIn("secret", config.redacted().values())

    def test_health_checks_report_model_availability(self):
        http = FakeHttp([{"models": [{"name": "llama3"}]}])
        config = ProviderConfig("local", "ollama", "llama3", "http://localhost:11434")
        self.assertTrue(OllamaAdapter(config, http).health_check()["ok"])

    def test_huggingface_chat_uses_router_and_bearer_token(self):
        http = FakeHttp([{"choices": [{"message": {"content": "hello"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 2, "completion_tokens": 3}}])
        config = ProviderConfig("hf", "huggingface", "Qwen/Qwen2.5-Coder-32B-Instruct", "https://router.huggingface.co/v1", api_key="hf-secret")
        response = HuggingFaceAdapter(config, http).generate(LLMRequest([{"role": "user", "content": "hi"}]))
        self.assertEqual(response.text, "hello")
        self.assertIn("/v1/chat/completions", http.calls[0][1])
        self.assertEqual(http.calls[0][2]["headers"]["Authorization"], "Bearer hf-secret")

    def test_huggingface_image_and_video_clients_normalize_assets(self):
        class FakeInferenceClient:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def text_to_image(self, prompt, **kwargs):
                return b"png-bytes"
            def text_to_video(self, prompt, **kwargs):
                return b"mp4-bytes"
        fake_module = type("HuggingFaceModule", (), {"InferenceClient": FakeInferenceClient})
        with patch.dict(sys.modules, {"huggingface_hub": fake_module}):
            image_config = ProviderConfig("hf-image", "huggingface", "black-forest-labs/FLUX.1-schnell", "https://router.huggingface.co", api_key="hf-secret", capabilities=ModelCapabilities(text=True, image_generation=True))
            image = HuggingFaceAdapter(image_config, FakeHttp([])).generate_media(MediaRequest("A signal room"))
            self.assertEqual(image.assets[0]["mime_type"], "image/png")
            video_config = ProviderConfig("hf-video", "huggingface", "Lightricks/LTX-Video", "https://router.huggingface.co", api_key="hf-secret", capabilities=ModelCapabilities(text=True, video_generation=True))
            video = HuggingFaceAdapter(video_config, FakeHttp([])).generate_media(MediaRequest("A moving signal room", modality="video"))
            self.assertEqual(video.assets[0]["mime_type"], "video/mp4")

    def test_stable_horde_code_generation_submits_and_polls(self):
        http = FakeHttp([
            {"id": "req-123", "message": "Request queued"},
            {"id": "req-123", "done": False, "queue_position": 1},
            {"id": "req-123", "done": True, "generations": [{"text": "def add(a, b):\\n    return a + b"}]},
        ])
        config = ProviderConfig("horde", "stable-horde", "aphrodite", "https://aihorde.net/api", api_key="horde-key", timeout_seconds=10)
        with patch("orville_core.providers.time.sleep"):
            response = StableHordeAdapter(config, http).generate(LLMRequest([{"role": "user", "content": "Write an add function"}], max_tokens=200, temperature=0.2))
        self.assertIn("def add", response.text)
        submit = http.calls[0]
        self.assertEqual(submit[0], "POST")
        self.assertIn("/v2/generate/text/async", submit[1])
        self.assertEqual(submit[2]["headers"]["apikey"], "horde-key")
        self.assertEqual(submit[2]["payload"]["models"], ["aphrodite"])
        self.assertEqual(submit[2]["payload"]["params"]["max_length"], 200)
        self.assertIn("Write an add function", submit[2]["payload"]["prompt"])

    def test_stable_horde_image_generation_submits_and_polls(self):
        http = FakeHttp([
            {"id": "img-123", "message": "Request queued"},
            {"id": "img-123", "done": True, "generations": [{"img": "ZmFrZS1pbWFnZQ==", "seed": 42}]},
        ])
        config = ProviderConfig("horde", "stable-horde", "stable_diffusion", "https://aihorde.net/api", api_key="horde-key", timeout_seconds=10, capabilities=ModelCapabilities(text=True, code=True, image_generation=True))
        with patch("orville_core.providers.time.sleep"):
            response = StableHordeAdapter(config, http).generate_media(MediaRequest("A copper signal room", options={"width": 640, "height": 384, "number": 1, "poll_interval_seconds": 0.1}))
        self.assertEqual(response.modality, "image")
        self.assertEqual(response.assets[0]["data"], "ZmFrZS1pbWFnZQ==")
        self.assertIn("/v2/generate/async", http.calls[0][1])
        self.assertEqual(http.calls[0][2]["payload"]["params"]["width"], 640)
        self.assertEqual(http.calls[0][2]["payload"]["params"]["height"], 384)

    def test_stable_horde_rejects_video_without_false_support(self):
        config = ProviderConfig("horde", "stable-horde", "model", "https://aihorde.net/api", capabilities=ModelCapabilities(text=True, image_generation=True))
        with self.assertRaisesRegex(ProviderError, "not video generation"):
            StableHordeAdapter(config, FakeHttp([])).generate_media(MediaRequest("A moving signal room", modality="video"))

    def test_stable_horde_health_and_factory(self):
        http = FakeHttp([{"message": "OK"}, [{"name": "aphrodite"}]])
        config = ProviderConfig("horde", "ai-horde", "aphrodite", "https://aihorde.net/api", api_key="horde-key")
        self.assertTrue(StableHordeAdapter(config, http).health_check()["ok"])
        self.assertIsInstance(create_provider(config), StableHordeAdapter)

    def test_registry_factory_supports_custom_local(self):
        config = ProviderConfig("custom", "custom-local", "my-model", "http://127.0.0.1:9000")
        self.assertIsInstance(create_provider(config), CustomLocalAdapter)
        with self.assertRaises(ValueError):
            create_provider(ProviderConfig("bad", "unknown", "model", "http://localhost"))

    def test_ollama_streaming_yields_normalized_chunks(self):
        http = FakeHttp([
            {"message": {"content": "hel"}, "done": False},
            {"message": {"content": "lo"}, "done": True, "done_reason": "stop"},
        ])
        config = ProviderConfig("local", "ollama", "llama3", "http://localhost:11434")
        chunks = list(OllamaAdapter(config, http).stream(LLMRequest([{"role": "user", "content": "hi"}])))
        self.assertEqual([chunk.text for chunk in chunks], ["hel", "lo"])
        self.assertTrue(chunks[-1].raw["done"])

    def test_gemini_multimodal_payload_uses_inline_data(self):
        http = FakeHttp([{"candidates": [{"content": {"parts": [{"text": "seen"}]}}]}])
        config = ProviderConfig("cloud", "gemini", "vision-model", "https://generativelanguage.googleapis.com", api_key="secret")
        GeminiAdapter(config, http).generate(LLMRequest([{"role": "user", "content": [
            {"type": "text", "text": "What is this?"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,ZmFrZQ=="}},
        ]}]))
        parts = http.calls[0][2]["payload"]["contents"][0]["parts"]
        self.assertEqual(parts[1]["inlineData"]["mimeType"], "image/png")
        self.assertEqual(parts[1]["inlineData"]["data"], "ZmFrZQ==")

    def test_ollama_embeddings_normalize_vectors(self):
        http = FakeHttp([{"embeddings": [[0.1, 0.2], [0.3, 0.4]]}])
        config = ProviderConfig("local", "ollama", "embed-model", "http://localhost:11434")
        response = OllamaAdapter(config, http).embed(["one", "two"])
        self.assertEqual(response.embeddings, [[0.1, 0.2], [0.3, 0.4]])
        self.assertEqual(http.calls[0][2]["payload"]["input"], ["one", "two"])

    def test_gemini_embeddings_normalize_vectors(self):
        http = FakeHttp([{"embedding": {"values": [0.1, 0.2]}}, {"embedding": {"values": [0.3, 0.4]}}])
        config = ProviderConfig("cloud", "gemini", "embed-model", "https://generativelanguage.googleapis.com", api_key="secret")
        response = GeminiAdapter(config, http).embed(["one", "two"])
        self.assertEqual(response.embeddings, [[0.1, 0.2], [0.3, 0.4]])

    def test_local_catalog_imports_and_hashes_a_downloaded_model(self):
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory, "model.gguf")
            model_path.write_bytes(b"fake model weights")
            catalog = LocalModelCatalog(Path(directory, "catalog.json"))
            record = catalog.import_model(model_path, model_id="local-1", runtime="ollama", endpoint="http://localhost:11434")
            self.assertEqual(record.file_format, "gguf")
            self.assertEqual(record.asset_type, "model")
            self.assertEqual(len(record.checksum_sha256), 64)
            self.assertEqual(catalog.get("local-1").endpoint, "http://localhost:11434")
            self.assertEqual(catalog.provider_config("local-1").local_model_id, "local-1")
            self.assertTrue(json.loads(Path(directory, "catalog.json").read_text())["models"])

    def test_local_catalog_validates_and_manages_model_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory, "model.gguf")
            model_path.write_bytes(b"fake model weights")
            catalog = LocalModelCatalog(Path(directory, "catalog.json"))
            catalog.import_model(model_path, model_id="local-2", runtime="ollama", endpoint="http://localhost:11434")
            self.assertTrue(catalog.validate("local-2")["checks"]["valid"])
            self.assertEqual(catalog.activate("local-2").status, "active")
            self.assertEqual(catalog.deactivate("local-2").status, "inactive")
            with self.assertRaises(Exception):
                catalog.remove("local-2", delete_files=True)
            catalog.remove("local-2")
            with self.assertRaises(KeyError):
                catalog.get("local-2")

    def test_local_catalog_maps_gateway_runtimes_to_openai_compatible_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory, "model.gguf")
            model_path.write_bytes(b"fake model weights")
            catalog = LocalModelCatalog(Path(directory, "catalog.json"))
            catalog.import_model(model_path, model_id="local-gateway", runtime="llama_cpp", endpoint="http://127.0.0.1:8000/v1")
            config = catalog.provider_config("local-gateway")
            self.assertEqual(config.provider_type, "openai-compatible-local")
            self.assertEqual(config.base_url, "http://127.0.0.1:8000/v1")
            self.assertIsInstance(create_provider(config), OpenAICompatibleAdapter)

    def test_local_catalog_activation_assigns_runtime_and_endpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory, "model.gguf")
            model_path.write_bytes(b"fake model weights")
            catalog = LocalModelCatalog(Path(directory, "catalog.json"))
            catalog.import_model(model_path, model_id="local-activate")
            record = catalog.activate("local-activate", required_runtime="llama_cpp", endpoint="http://127.0.0.1:8000/v1")
            self.assertEqual(record.status, "active")
            self.assertEqual(record.runtime, "llama_cpp")
            self.assertEqual(catalog.provider_config("local-activate").provider_type, "openai-compatible-local")

    def test_local_catalog_rejects_duplicate_asset_and_detects_checksum_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory, "duplicate.gguf")
            model_path.write_bytes(b"fake model weights")
            catalog = LocalModelCatalog(Path(directory, "catalog.json"))
            catalog.import_model(model_path, model_id="first")
            with self.assertRaisesRegex(ValueError, "duplicates registered model"):
                catalog.import_model(model_path, model_id="second")
            self.assertTrue(catalog.verify_checksum("first")["matches"])
            model_path.write_bytes(b"tampered")
            self.assertFalse(catalog.verify_checksum("first")["matches"])

    def test_local_catalog_dry_run_does_not_activate_or_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory, "dry-run.gguf")
            model_path.write_bytes(b"fake model weights")
            catalog = LocalModelCatalog(Path(directory, "catalog.json"))
            catalog.import_model(model_path, model_id="dry-run", runtime="ollama", endpoint="http://localhost:11434")
            result = catalog.dry_run("dry-run", required_runtime="ollama")
            self.assertEqual(result["mode"], "validation_only")
            self.assertFalse(result["executed"])
            self.assertFalse(result["catalog_mutated"])
            self.assertEqual(catalog.get("dry-run").status, "imported")

    def test_local_catalog_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                LocalModelCatalog(Path(directory, "catalog.json")).import_model(Path(directory, "missing.gguf"), model_id="x")


if __name__ == "__main__":
    unittest.main()


def test_provider_config_complete_schema_is_validated_and_redacted():
    config = ProviderConfig(
        "blackbox",
        "blackbox",
        "blackboxai/openai/gpt-5.5",
        "https://api.blackbox.ai",
        api_key="synthetic-secret",
        auth_method="api_key",
        endpoint_family="standard",
        account_plan_status="eligible",
        privacy_mode="cloud_approved",
        timeout_seconds=45.0,
        enabled=True,
    )
    public = config.redacted()
    assert public["auth_method"] == "api_key"
    assert public["endpoint_family"] == "standard"
    assert public["account_plan_status"] == "eligible"
    assert public["privacy_mode"] == "cloud_approved"
    assert public["enabled"] is True
    assert "synthetic-secret" not in str(public)


def test_provider_errors_are_actionable_and_do_not_include_response_bodies():
    from orville_core.providers import _http_provider_error

    expected = {
        401: "check the API key and reconnect",
        403: "check account permissions and model access",
        402: "check the Blackbox subscription or usage billing status",
        429: "retry after the provider rate-limit window",
    }
    for status_code, action in expected.items():
        error = _http_provider_error(status_code, detail="Bearer sk-live-secret123")
        assert error.status_code == status_code
        assert error.action == action
        assert action in str(error)
        assert "sk-live-secret123" not in str(error)
