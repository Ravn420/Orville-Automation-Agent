"""Provider-neutral model contracts and HTTP adapters.

The module uses only the Python standard library. Credentials are supplied at
runtime and are never serialized by these classes.
"""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    """Raised when a model provider cannot complete a request."""

    def __init__(self, message: str, *, status_code: int | None = None, action: str | None = None) -> None:
        self.status_code = status_code
        self.action = action
        super().__init__(message if action is None else f"{message}; action: {action}")


def _http_provider_error(status_code: int, *, detail: str = "") -> ProviderError:
    actions = {
        401: "check the API key and reconnect",
        402: "check the Blackbox subscription or usage billing status",
        403: "check account permissions and model access",
        429: "retry after the provider rate-limit window",
    }
    action = actions.get(status_code, "check the endpoint configuration and provider status")
    return ProviderError(f"HTTP {status_code} from provider", status_code=status_code, action=action)


@dataclass(frozen=True)
class ModelCapabilities:
    text: bool = True
    code: bool = False
    vision: bool = False
    image_generation: bool = False
    video_generation: bool = False
    audio: bool = False
    embeddings: bool = False
    streaming: bool = False
    structured_output: bool = False
    tool_calling: bool = False

    def to_dict(self) -> dict[str, bool]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class ProviderConfig:
    provider_id: str
    provider_type: str
    model: str
    base_url: str
    api_key: str | None = None
    timeout_seconds: float = 60.0
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    auth_method: str = "none"
    endpoint_family: str = "standard"
    account_plan_status: str = "unknown"
    privacy_mode: str = "local_only"
    enabled: bool = True
    local_model_id: str | None = None
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.provider_id.strip() or not self.provider_type.strip() or not self.model.strip() or not self.base_url.strip():
            raise ValueError("provider_id, provider_type, model, and base_url must not be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.auth_method not in {"none", "api_key", "bearer", "oauth2", "server_relay"}:
            raise ValueError("unsupported provider auth_method")
        if self.endpoint_family not in {"standard", "enterprise", "local", "custom"}:
            raise ValueError("unsupported provider endpoint_family")
        if self.account_plan_status not in {"unknown", "eligible", "ineligible", "expired", "rate_limited"}:
            raise ValueError("unsupported provider account_plan_status")
        if self.privacy_mode not in {"local_only", "cloud_approved", "restricted"}:
            raise ValueError("unsupported provider privacy_mode")

    def redacted(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "timeout_seconds": self.timeout_seconds,
            "auth_method": self.auth_method,
            "endpoint_family": self.endpoint_family,
            "account_plan_status": self.account_plan_status,
            "privacy_mode": self.privacy_mode,
            "enabled": self.enabled,
            "capabilities": self.capabilities.to_dict(),
            "local_model_id": self.local_model_id,
            "custom_headers": sorted(self.headers.keys()),
        }


@dataclass(frozen=True)
class LLMRequest:
    """A provider-neutral request; message content may be text or multimodal parts."""

    messages: list[dict[str, Any]]
    temperature: float | None = None
    max_tokens: int | None = None
    response_schema: dict[str, Any] | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.messages:
            raise ValueError("messages must not be empty")
        for message in self.messages:
            if message.get("role") not in {"system", "user", "assistant", "tool"}:
                raise ValueError("message role must be system, user, assistant, or tool")
            if "content" not in message:
                raise ValueError("each message must contain content")
        if self.temperature is not None and not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError("max_tokens must be positive")


@dataclass(frozen=True)
class MediaRequest:
    prompt: str
    modality: str = "image"
    negative_prompt: str | None = None
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty")
        if self.modality not in {"image", "video"}:
            raise ValueError("modality must be image or video")


@dataclass(frozen=True)
class MediaResponse:
    provider_id: str
    model: str
    modality: str
    assets: list[dict[str, Any]]
    raw: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMResponse:
    provider_id: str
    model: str
    text: str
    raw: dict[str, Any]
    finish_reason: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)

    def json(self) -> Any:
        try:
            return json.loads(self.text)
        except json.JSONDecodeError as exc:
            raise ProviderError("provider response is not valid JSON") from exc


@dataclass(frozen=True)
class StreamChunk:
    provider_id: str
    model: str
    text: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    finish_reason: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingResponse:
    provider_id: str
    model: str
    embeddings: list[list[float]]
    raw: dict[str, Any]
    usage: dict[str, int] = field(default_factory=dict)


class LLMProvider(Protocol):
    config: ProviderConfig

    def generate(self, request: LLMRequest) -> LLMResponse:
        ...

    def generate_media(self, request: MediaRequest) -> MediaResponse:
        ...

    def stream(self, request: LLMRequest) -> Iterable[StreamChunk]:
        ...

    def embed(self, inputs: str | list[str]) -> EmbeddingResponse:
        ...

    def health_check(self) -> dict[str, Any]:
        ...


class JsonHttpClient:
    """Injectable JSON HTTP client supporting regular and line-streaming responses."""

    def request(self, method: str, url: str, *, headers: dict[str, str] | None = None, payload: dict[str, Any] | None = None, timeout: float = 60.0) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, method=method, headers={"Accept": "application/json", **(headers or {})})
        if payload is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urlopen(request, timeout=timeout) as response:
                content = response.read().decode("utf-8")
        except HTTPError as exc:
            exc.read(4096)
            raise _http_provider_error(exc.code) from exc
        except URLError as exc:
            raise ProviderError("provider connection failed", action="check TLS, allowed hosts, redirects, and endpoint configuration") from exc
        except TimeoutError as exc:
            raise ProviderError("provider request timed out", action="retry with a bounded timeout or check provider availability") from exc
        try:
            return json.loads(content) if content else {}
        except json.JSONDecodeError as exc:
            raise ProviderError("provider returned non-JSON content") from exc

    def stream_json(self, method: str, url: str, *, headers: dict[str, str] | None = None, payload: dict[str, Any] | None = None, timeout: float = 60.0) -> Iterable[dict[str, Any]]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, method=method, headers={"Accept": "application/x-ndjson, text/event-stream, application/json", **(headers or {})})
        if payload is not None:
            request.add_header("Content-Type", "application/json")
        try:
            response = urlopen(request, timeout=timeout)
        except HTTPError as exc:
            exc.read(4096)
            raise _http_provider_error(exc.code) from exc
        except URLError as exc:
            raise ProviderError("provider connection failed", action="check TLS, allowed hosts, redirects, and endpoint configuration") from exc
        except TimeoutError as exc:
            raise ProviderError("provider request timed out", action="retry with a bounded timeout or check provider availability") from exc
        try:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ProviderError("provider returned an invalid streaming JSON event") from exc
        finally:
            response.close()


class BaseHttpProvider:
    def __init__(self, config: ProviderConfig, http: JsonHttpClient | None = None) -> None:
        self.config = config
        self.http = http or JsonHttpClient()

    def _headers(self) -> dict[str, str]:
        return dict(self.config.headers)

    def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.http.request("POST", urljoin(self.config.base_url.rstrip("/") + "/", path.lstrip("/")), headers=self._headers(), payload=payload, timeout=self.config.timeout_seconds)

    def _stream_request(self, path: str, payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
        return self.http.stream_json("POST", urljoin(self.config.base_url.rstrip("/") + "/", path.lstrip("/")), headers=self._headers(), payload=payload, timeout=self.config.timeout_seconds)

    def generate_media(self, request: MediaRequest) -> MediaResponse:
        raise ProviderError(f"provider {self.config.provider_id} does not implement {request.modality} generation")

    @staticmethod
    def _parts(content: Any) -> list[dict[str, Any]]:
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        if isinstance(content, list):
            return content
        raise ValueError("message content must be text or a list of multimodal parts")


class GeminiAdapter(BaseHttpProvider):
    """Adapter for Gemini generateContent, streamGenerateContent, and embedContent."""

    def _headers(self) -> dict[str, str]:
        headers = dict(self.config.headers)
        if self.config.api_key:
            headers.setdefault("x-goog-api-key", self.config.api_key)
        return headers

    def _contents(self, request: LLMRequest) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        contents, system_parts = [], []
        for message in request.messages:
            parts = []
            for part in self._parts(message["content"]):
                kind = part.get("type")
                if kind == "text":
                    parts.append({"text": part.get("text", "")})
                elif kind in {"image_url", "image", "audio", "video", "file"}:
                    source = part.get("image_url", part)
                    uri = source.get("url") or source.get("uri")
                    if uri and uri.startswith("data:"):
                        header, encoded = uri.split(",", 1)
                        mime = header.split(";", 1)[0][5:]
                        parts.append({"inlineData": {"mimeType": mime, "data": encoded if ";base64" in header else base64.b64encode(encoded.encode()).decode()}})
                    elif uri:
                        parts.append({"fileData": {"fileUri": uri, "mimeType": source.get("mime_type", "application/octet-stream")}})
                    elif part.get("data"):
                        parts.append({"inlineData": {"mimeType": part.get("mime_type", "application/octet-stream"), "data": part["data"]}})
                    else:
                        raise ValueError("multimodal part requires url, uri, or data")
                else:
                    raise ValueError(f"unsupported multimodal part type: {kind}")
            if message["role"] == "system":
                system_parts.extend(parts)
            else:
                contents.append({"role": "model" if message["role"] == "assistant" else "user", "parts": parts})
        return contents, system_parts

    def _payload(self, request: LLMRequest) -> dict[str, Any]:
        contents, system_parts = self._contents(request)
        generation: dict[str, Any] = {}
        if request.temperature is not None:
            generation["temperature"] = request.temperature
        if request.max_tokens is not None:
            generation["maxOutputTokens"] = request.max_tokens
        if request.response_schema:
            generation.update({"responseMimeType": "application/json", "responseSchema": request.response_schema})
        payload: dict[str, Any] = {"contents": contents}
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}
        if generation:
            payload["generationConfig"] = generation
        if request.tools:
            payload["tools"] = [{"functionDeclarations": request.tools}]
        return payload

    def _path(self, operation: str) -> str:
        suffix = f"?{urlencode({'key': self.config.api_key})}" if self.config.api_key else ""
        return f"v1beta/models/{self.config.model}:{operation}{suffix}"

    @staticmethod
    def _response(raw: dict[str, Any], provider_id: str, model: str) -> LLMResponse:
        candidate = (raw.get("candidates") or [{}])[0]
        parts = candidate.get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts)
        calls = [ToolCall(part["functionCall"]["name"], part["functionCall"].get("args", {})) for part in parts if "functionCall" in part]
        usage = raw.get("usageMetadata", {})
        return LLMResponse(provider_id, model, text, raw, candidate.get("finishReason"), calls, {"input_tokens": int(usage.get("promptTokenCount", 0)), "output_tokens": int(usage.get("candidatesTokenCount", 0))})

    def generate(self, request: LLMRequest) -> LLMResponse:
        raw = self.http.request("POST", urljoin(self.config.base_url.rstrip("/") + "/", self._path("generateContent")), headers=self._headers(), payload=self._payload(request), timeout=self.config.timeout_seconds)
        return self._response(raw, self.config.provider_id, self.config.model)

    def stream(self, request: LLMRequest) -> Iterable[StreamChunk]:
        for raw in self._stream_request(self._path("streamGenerateContent") + "&alt=sse", self._payload(request)):
            response = self._response(raw, self.config.provider_id, self.config.model)
            yield StreamChunk(response.provider_id, response.model, response.text, raw, response.finish_reason, response.tool_calls, response.usage)

    def embed(self, inputs: str | list[str]) -> EmbeddingResponse:
        values = [inputs] if isinstance(inputs, str) else inputs
        vectors = []
        raws = []
        for value in values:
            raw = self.http.request("POST", urljoin(self.config.base_url.rstrip("/") + "/", self._path("embedContent")), headers=self._headers(), payload={"model": f"models/{self.config.model}", "content": {"parts": [{"text": value}]}}, timeout=self.config.timeout_seconds)
            vectors.append(raw.get("embedding", {}).get("values", []))
            raws.append(raw)
        return EmbeddingResponse(self.config.provider_id, self.config.model, vectors, {"responses": raws})

    def health_check(self) -> dict[str, Any]:
        raw = self.http.request("GET", urljoin(self.config.base_url.rstrip("/") + "/", "v1beta/models"), headers=self._headers(), timeout=self.config.timeout_seconds)
        models = raw.get("models", [])
        available = any(str(model.get("name", "")).endswith(self.config.model) for model in models)
        return {"ok": available, "provider_id": self.config.provider_id, "model": self.config.model, "models_seen": len(models)}


class AnthropicAdapter(BaseHttpProvider):
    """Adapter for Anthropic's Messages API with text streaming."""

    def _headers(self) -> dict[str, str]:
        headers = {"anthropic-version": "2023-06-01", **self.config.headers}
        if self.config.api_key:
            headers.setdefault("x-api-key", self.config.api_key)
        return headers

    def _payload(self, request: LLMRequest, stream: bool = False) -> dict[str, Any]:
        messages = [message for message in request.messages if message.get("role") != "system"]
        payload: dict[str, Any] = {"model": self.config.model, "max_tokens": request.max_tokens or 4096, "messages": messages, "stream": stream}
        system = next((message.get("content") for message in request.messages if message.get("role") == "system"), None)
        if system:
            payload["system"] = system
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.tools:
            payload["tools"] = request.tools
        return payload

    @staticmethod
    def _response(raw: dict[str, Any], provider_id: str, model: str) -> LLMResponse:
        text = "".join(str(part.get("text", "")) for part in raw.get("content", []) if part.get("type") == "text")
        usage = raw.get("usage") or {}
        return LLMResponse(provider_id, model, text, raw, raw.get("stop_reason"), usage={"input_tokens": int(usage.get("input_tokens", 0)), "output_tokens": int(usage.get("output_tokens", 0))})

    def generate(self, request: LLMRequest) -> LLMResponse:
        raw = self.http.request("POST", urljoin(self.config.base_url.rstrip("/") + "/", "messages"), headers=self._headers(), payload=self._payload(request), timeout=self.config.timeout_seconds)
        return self._response(raw, self.config.provider_id, self.config.model)

    def stream(self, request: LLMRequest) -> Iterable[StreamChunk]:
        finish_reason = None
        for raw in self._stream_request("messages", self._payload(request, True)):
            event_type = raw.get("type")
            if event_type == "content_block_delta":
                delta = raw.get("delta") or {}
                yield StreamChunk(self.config.provider_id, self.config.model, str(delta.get("text", "")), raw)
            elif event_type == "message_delta":
                finish_reason = (raw.get("delta") or {}).get("stop_reason") or finish_reason
        if finish_reason:
            yield StreamChunk(self.config.provider_id, self.config.model, "", {}, finish_reason)

    def embed(self, inputs: str | list[str]) -> EmbeddingResponse:
        raise ProviderError("Anthropic does not expose embeddings through the Messages API")

    def health_check(self) -> dict[str, Any]:
        raw = self.http.request("GET", urljoin(self.config.base_url.rstrip("/") + "/", "models"), headers=self._headers(), timeout=self.config.timeout_seconds)
        models = raw.get("data", [])
        names = {str(item.get("id", "")) for item in models}
        return {"ok": self.config.model in names, "provider_id": self.config.provider_id, "model": self.config.model, "models_seen": len(names)}


class OllamaAdapter(BaseHttpProvider):
    """Adapter for Ollama /api/chat, /api/embed, and /api/tags."""

    def _payload(self, request: LLMRequest, stream: bool) -> dict[str, Any]:
        options: dict[str, Any] = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens
        payload: dict[str, Any] = {"model": self.config.model, "messages": request.messages, "stream": stream}
        if options:
            payload["options"] = options
        if request.response_schema:
            payload["format"] = request.response_schema
        if request.tools:
            payload["tools"] = request.tools
        return payload

    @staticmethod
    def _response(raw: dict[str, Any], provider_id: str, model: str) -> LLMResponse:
        message = raw.get("message", {})
        calls = [ToolCall(call.get("function", {}).get("name", ""), call.get("function", {}).get("arguments", {})) for call in message.get("tool_calls", [])]
        return LLMResponse(provider_id, model, message.get("content", ""), raw, raw.get("done_reason"), calls, {"input_tokens": int(raw.get("prompt_eval_count", 0)), "output_tokens": int(raw.get("eval_count", 0))})

    def generate(self, request: LLMRequest) -> LLMResponse:
        return self._response(self._request("api/chat", self._payload(request, False)), self.config.provider_id, self.config.model)

    def stream(self, request: LLMRequest) -> Iterable[StreamChunk]:
        for raw in self._stream_request("api/chat", self._payload(request, True)):
            response = self._response(raw, self.config.provider_id, self.config.model)
            yield StreamChunk(response.provider_id, response.model, response.text, raw, response.finish_reason, response.tool_calls, response.usage)

    def embed(self, inputs: str | list[str]) -> EmbeddingResponse:
        raw = self._request("api/embed", {"model": self.config.model, "input": inputs})
        vectors = raw.get("embeddings", [])
        if not vectors and raw.get("embedding"):
            vectors = [raw["embedding"]]
        return EmbeddingResponse(self.config.provider_id, self.config.model, vectors, raw)

    def health_check(self) -> dict[str, Any]:
        raw = self.http.request("GET", urljoin(self.config.base_url.rstrip("/") + "/", "api/tags"), timeout=self.config.timeout_seconds)
        models = raw.get("models", [])
        available = any(model.get("name") == self.config.model or model.get("model") == self.config.model for model in models)
        return {"ok": available, "provider_id": self.config.provider_id, "model": self.config.model, "models_seen": len(models)}


class OpenAICompatibleAdapter(BaseHttpProvider):
    """Adapter for OpenAI-compatible gateways, including Blackbox AI."""

    def _headers(self) -> dict[str, str]:
        headers = dict(self.config.headers)
        if self.config.api_key:
            headers.setdefault("Authorization", f"Bearer {self.config.api_key}")
        return headers

    def _payload(self, request: LLMRequest, stream: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": self.config.model, "messages": request.messages, "stream": stream}
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.tools:
            payload["tools"] = request.tools
        if request.response_schema:
            payload["response_format"] = {"type": "json_schema", "json_schema": {"name": "orville_output", "schema": request.response_schema}}
        return payload

    @staticmethod
    def _response(raw: dict[str, Any], provider_id: str, model: str) -> LLMResponse:
        choice = (raw.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        calls = [ToolCall(call.get("function", {}).get("name", ""), call.get("function", {}).get("arguments", {})) for call in message.get("tool_calls", [])]
        usage = raw.get("usage") or {}
        return LLMResponse(provider_id, model, message.get("content", "") or "", raw, choice.get("finish_reason"), calls, {"input_tokens": int(usage.get("prompt_tokens", 0)), "output_tokens": int(usage.get("completion_tokens", 0))})

    def generate(self, request: LLMRequest) -> LLMResponse:
        raw = self._request("chat/completions", self._payload(request))
        return self._response(raw, self.config.provider_id, self.config.model)

    def stream(self, request: LLMRequest) -> Iterable[StreamChunk]:
        for raw in self._stream_request("chat/completions", self._payload(request, True)):
            choices = raw.get("choices") or [{}]
            delta = choices[0].get("delta") or {}
            yield StreamChunk(self.config.provider_id, self.config.model, delta.get("content", ""), raw, choices[0].get("finish_reason"))

    def embed(self, inputs: str | list[str]) -> EmbeddingResponse:
        raw = self._request("embeddings", {"model": self.config.model, "input": inputs})
        values = [item.get("embedding", []) for item in raw.get("data", [])]
        return EmbeddingResponse(self.config.provider_id, self.config.model, values, raw)

    def health_check(self) -> dict[str, Any]:
        raw = self.http.request("GET", urljoin(self.config.base_url.rstrip("/") + "/", "models"), headers=self._headers(), timeout=self.config.timeout_seconds)
        models = raw.get("data", [])
        available = any(model.get("id") == self.config.model for model in models)
        return {"ok": available, "provider_id": self.config.provider_id, "model": self.config.model, "models_seen": len(models)}


class ManagedBlackboxRelayAdapter(OpenAICompatibleAdapter):
    """OpenAI-compatible Blackbox access through an Orville-managed relay.

    The relay URL is client-visible, but the Blackbox provider credential stays
    on the relay service. A deployment may add a short-lived Orville session
    header through ``ProviderConfig.headers``; no Blackbox API key is accepted.
    """

    def __init__(self, config: ProviderConfig, http: JsonHttpClient | None = None) -> None:
        if config.api_key:
            raise ValueError("managed Blackbox relay must not receive a Blackbox API key")
        super().__init__(config, http)

    def _preflight(self, request: LLMRequest, *, streaming: bool = False) -> None:
        capabilities = self.config.capabilities
        if streaming and not capabilities.streaming:
            raise ProviderError("managed Blackbox relay does not advertise streaming capability")
        if request.tools and not capabilities.tool_calling:
            raise ProviderError("managed Blackbox relay does not advertise tool_calling capability")
        if request.response_schema and not capabilities.structured_output:
            raise ProviderError("managed Blackbox relay does not advertise structured_output capability")

    def generate(self, request: LLMRequest) -> LLMResponse:
        self._preflight(request)
        return super().generate(request)

    def stream(self, request: LLMRequest) -> Iterable[StreamChunk]:
        self._preflight(request, streaming=True)
        return super().stream(request)

    def embed(self, inputs: str | list[str]) -> EmbeddingResponse:
        if not self.config.capabilities.embeddings:
            raise ProviderError("managed Blackbox relay does not advertise embeddings capability")
        return super().embed(inputs)

    def health_check(self) -> dict[str, Any]:
        try:
            raw = self.http.request("GET", urljoin(self.config.base_url.rstrip("/") + "/", "health"), headers=self._headers(), timeout=self.config.timeout_seconds)
        except ProviderError as exc:
            return {"ok": False, "provider_id": self.config.provider_id, "model": self.config.model, "error": str(exc), "managed_relay": True}
        return {"ok": bool(raw.get("ok", raw.get("status") in {"ok", "ready"})), "provider_id": self.config.provider_id, "model": self.config.model, "managed_relay": True, "credential_configured": False, "capabilities": self.config.capabilities.to_dict(), "relay": raw}


class HuggingFaceAdapter(OpenAICompatibleAdapter):
    """Hugging Face Inference Providers adapter for chat, image, and video tasks.

    Chat and code use the Hugging Face OpenAI-compatible router. Media uses the
    official ``huggingface_hub`` client lazily so the core package remains
    importable without the optional media dependency.
    """

    def _headers(self) -> dict[str, str]:
        headers = dict(self.config.headers)
        if self.config.api_key:
            headers.setdefault("Authorization", f"Bearer {self.config.api_key}")
        return headers

    def generate_media(self, request: MediaRequest) -> MediaResponse:
        if request.modality == "video" and not self.config.capabilities.video_generation:
            raise ProviderError("Hugging Face provider is not configured with video_generation capability for this model")
        if request.modality == "image" and not self.config.capabilities.image_generation:
            raise ProviderError("Hugging Face provider is not configured with image_generation capability for this model")
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise ProviderError("Hugging Face media generation requires the optional huggingface-hub package") from exc
        if not self.config.api_key:
            raise ProviderError("Hugging Face media generation requires an API token")
        options = dict(request.options)
        provider = options.get("provider") or self.config.headers.get("X-HF-Provider") or "auto"
        client = InferenceClient(model=self.config.model, token=self.config.api_key, provider=provider)
        try:
            if request.modality == "image":
                result = client.text_to_image(request.prompt, negative_prompt=request.negative_prompt, width=options.get("width"), height=options.get("height"), num_inference_steps=options.get("steps"), guidance_scale=options.get("cfg_scale"), seed=options.get("seed"))
                mime = "image/png"
            else:
                result = client.text_to_video(request.prompt, num_frames=options.get("frames"), num_inference_steps=options.get("steps"), guidance_scale=options.get("cfg_scale"), seed=options.get("seed"))
                mime = "video/mp4"
        except Exception as exc:
            raise ProviderError(f"Hugging Face {request.modality} generation failed: {exc}") from exc
        if hasattr(result, "save"):
            from io import BytesIO
            stream = BytesIO()
            result.save(stream, format="PNG")
            data = stream.getvalue()
        elif isinstance(result, (bytes, bytearray)):
            data = bytes(result)
        else:
            raise ProviderError("Hugging Face returned an unsupported media response type")
        return MediaResponse(self.config.provider_id, self.config.model, request.modality, [{"type": request.modality, "mime_type": mime, "data": base64.b64encode(data).decode("ascii"), "size_bytes": len(data)}], {"provider": provider})

    def health_check(self) -> dict[str, Any]:
        return {"ok": bool(self.config.api_key), "provider_id": self.config.provider_id, "model": self.config.model, "configured": bool(self.config.api_key), "message": "Token configured; model availability is checked when the selected task is invoked"}


class StableHordeAdapter(BaseHttpProvider):
    """AI Horde asynchronous text-generation adapter for code-capable models."""

    def _headers(self) -> dict[str, str]:
        headers = {"Client-Agent": "Orville/1.0", **self.config.headers}
        if self.config.api_key:
            headers["apikey"] = self.config.api_key
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    @staticmethod
    def _model_names(raw: Any) -> set[str]:
        values = raw if isinstance(raw, list) else raw.get("models", []) if isinstance(raw, dict) else []
        names: set[str] = set()
        for item in values:
            if isinstance(item, str):
                names.add(item)
            elif isinstance(item, dict):
                for key in ("name", "model_name", "model", "id"):
                    if item.get(key):
                        names.add(str(item[key]))
        return names

    @staticmethod
    def _prompt(request: LLMRequest) -> str:
        parts: list[str] = []
        for message in request.messages:
            role = message.get("role", "user").upper()
            content = message.get("content", "")
            if isinstance(content, list):
                content = " ".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
            parts.append(f"### {role}:\n{content}")
        return "\n\n".join(parts)

    def _payload(self, request: LLMRequest) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if request.max_tokens is not None:
            params["max_length"] = request.max_tokens
        if request.temperature is not None:
            params["temperature"] = request.temperature
        return {"prompt": self._prompt(request), "models": [self.config.model], "params": params}

    def generate(self, request: LLMRequest) -> LLMResponse:
        submitted = self._request("v2/generate/text/async", self._payload(request))
        request_id = str(submitted.get("id", ""))
        if not request_id:
            raise ProviderError("Stable Horde did not return a text-generation request id")
        deadline = time.monotonic() + self.config.timeout_seconds
        last: dict[str, Any] = submitted
        while time.monotonic() <= deadline:
            last = self.http.request("GET", urljoin(self.config.base_url.rstrip("/") + "/", f"v2/generate/text/status/{request_id}"), headers=self._headers(), timeout=self.config.timeout_seconds)
            if last.get("faulted"):
                raise ProviderError(f"Stable Horde code generation faulted: {last.get('message') or 'unknown error'}")
            if last.get("done"):
                generations = last.get("generations") or []
                text = "".join(str(item.get("text", "")) for item in generations if item.get("text") is not None)
                if not text:
                    raise ProviderError("Stable Horde completed without generated text")
                return LLMResponse(self.config.provider_id, self.config.model, text, last, "stop", usage={})
            time.sleep(1.0)
        raise ProviderError(f"Stable Horde code generation timed out after {self.config.timeout_seconds:g} seconds (request {request_id})")

    def generate_media(self, request: MediaRequest) -> MediaResponse:
        if request.modality == "video":
            raise ProviderError("Stable Horde's direct API currently supports text and image generation, not video generation")
        options = dict(request.options)
        params: dict[str, Any] = {}
        for key in ("width", "height", "steps", "cfg_scale", "seed", "sampler_name", "n_iter", "karras", "tiling"):
            if options.get(key) is not None:
                params[key] = options[key]
        params["n_iter"] = max(1, min(int(options.get("number", params.get("n_iter", 1))), 4))
        payload: dict[str, Any] = {"prompt": request.prompt, "models": [self.config.model], "params": params, "nsfw": bool(options.get("nsfw", False)), "censor_nsfw": bool(options.get("censor_nsfw", True))}
        if request.negative_prompt:
            payload["params"]["negative_prompt"] = request.negative_prompt
        submit = self._request("v2/generate/async", payload)
        request_id = str(submit.get("id", ""))
        if not request_id:
            raise ProviderError("Stable Horde did not return an image-generation request id")
        deadline = time.monotonic() + min(float(options.get("wait_timeout_seconds", self.config.timeout_seconds)), self.config.timeout_seconds)
        interval = max(0.1, min(float(options.get("poll_interval_seconds", 1.0)), 10.0))
        last: dict[str, Any] = submit
        while time.monotonic() <= deadline:
            last = self.http.request("GET", urljoin(self.config.base_url.rstrip("/") + "/", f"v2/generate/status/{request_id}"), headers=self._headers(), timeout=self.config.timeout_seconds)
            if last.get("faulted"):
                raise ProviderError(f"Stable Horde image generation faulted: {last.get('message') or 'unknown error'}")
            if last.get("done"):
                assets = []
                for item in last.get("generations") or []:
                    if item.get("img") or item.get("url"):
                        assets.append({"type": "image", "data": item.get("img"), "url": item.get("url"), "seed": item.get("seed"), "model": item.get("model")})
                if not assets:
                    raise ProviderError("Stable Horde completed without generated image assets")
                return MediaResponse(self.config.provider_id, self.config.model, "image", assets, last)
            time.sleep(interval)
        raise ProviderError(f"Stable Horde image generation timed out after {min(float(options.get('wait_timeout_seconds', self.config.timeout_seconds)), self.config.timeout_seconds):g} seconds (request {request_id})")

    def stream(self, request: LLMRequest) -> Iterable[StreamChunk]:
        response = self.generate(request)
        yield StreamChunk(response.provider_id, response.model, response.text, response.raw, response.finish_reason, usage=response.usage)

    def embed(self, inputs: str | list[str]) -> EmbeddingResponse:
        raise ProviderError("Stable Horde code-generation models do not provide embeddings")

    def health_check(self) -> dict[str, Any]:
        heartbeat = self.http.request("GET", urljoin(self.config.base_url.rstrip("/") + "/", "v2/status/heartbeat"), headers=self._headers(), timeout=self.config.timeout_seconds)
        models_raw = self.http.request("GET", urljoin(self.config.base_url.rstrip("/") + "/", "v2/status/models"), headers=self._headers(), timeout=self.config.timeout_seconds)
        model_names = self._model_names(models_raw)
        return {"ok": bool(heartbeat) and self.config.model in model_names, "provider_id": self.config.provider_id, "model": self.config.model, "models_seen": len(model_names), "model_available": self.config.model in model_names}


class CustomLocalAdapter(OllamaAdapter):
    """Adapter for a user-supplied Ollama-compatible local endpoint."""

    pass


def create_provider(config: ProviderConfig, http: JsonHttpClient | None = None) -> LLMProvider:
    provider_type = config.provider_type.lower().replace("_", "-")
    if provider_type == "gemini":
        return GeminiAdapter(config, http)
    if provider_type == "anthropic":
        return AnthropicAdapter(config, http)
    if provider_type == "ollama":
        return OllamaAdapter(config, http)
    if provider_type in {"custom-local", "custom-local-ollama", "ollama-compatible"}:
        return CustomLocalAdapter(config, http)
    if provider_type in {"blackbox-relay", "managed-blackbox", "orville-blackbox-relay"}:
        return ManagedBlackboxRelayAdapter(config, http)
    if provider_type in {"blackbox", "openai", "openai-compatible", "openai-compatible-local", "openrouter", "groq", "together", "deepseek", "mistral", "xai", "perplexity", "cohere", "fireworks", "cerebras", "nvidia-nim", "azure-openai", "bedrock-compatible"}:
        return OpenAICompatibleAdapter(config, http)
    if provider_type in {"huggingface", "hugging-face", "hf-inference"}:
        return HuggingFaceAdapter(config, http)
    if provider_type in {"stable-horde", "stablehorde", "ai-horde", "aihorde"}:
        return StableHordeAdapter(config, http)
    raise ValueError(f"unsupported provider type: {config.provider_type}")


class ProviderRegistry:
    """Register providers and select an available provider by explicit ID."""

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}

    def register(self, provider: LLMProvider) -> None:
        self._providers[provider.config.provider_id] = provider

    def get(self, provider_id: str) -> LLMProvider:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise ProviderError(f"provider not registered: {provider_id}") from exc

    def providers(self) -> tuple[LLMProvider, ...]:
        return tuple(self._providers.values())

    def remove(self, provider_id: str) -> None:
        if provider_id not in self._providers:
            raise ProviderError(f"provider not registered: {provider_id}")
        del self._providers[provider_id]

    def health_check_all(self) -> dict[str, dict[str, Any]]:
        results = {}
        for provider_id, provider in self._providers.items():
            try:
                results[provider_id] = provider.health_check()
            except ProviderError as exc:
                results[provider_id] = {"ok": False, "provider_id": provider_id, "error": str(exc)}
        return results
