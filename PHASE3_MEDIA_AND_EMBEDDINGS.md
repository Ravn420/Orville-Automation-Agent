# Phase 3: Streaming, Multimodal Inputs, and Embeddings

## Overview

Phase 3 extends the provider-neutral layer without requiring vendor SDKs. Gemini, Ollama, and custom Ollama-compatible endpoints now expose the same concepts: a complete response, an iterable stream of normalized chunks, and an embedding response. The existing provider configuration and capability declarations remain compatible with the Phase 1 checkpoint engine.

## Streaming

Use `provider.stream(request)` when the user interface or orchestration layer should receive incremental output. Each `StreamChunk` contains provider ID, model ID, text delta, raw provider event, finish reason, tool calls, and usage metadata when supplied by the provider.

```python
chunks = provider.stream(LLMRequest([
    {"role": "user", "content": "Explain the generated architecture."},
]))
for chunk in chunks:
    print(chunk.text, end="", flush=True)
```

The HTTP transport accepts newline-delimited JSON and server-sent event lines with `data:` prefixes. Ollama streams newline-delimited JSON. Gemini streaming is requested through `streamGenerateContent` with SSE output. The transport skips keep-alive comments and stops on the `[DONE]` sentinel.

## Multimodal messages

`LLMRequest` message content can be a string or a list of typed parts. Text parts use `{ "type": "text", "text": "..." }`. Image, audio, video, and file parts can use a URL, URI, or base64 data payload. Gemini converts data URLs into `inlineData` and remote references into `fileData`. The provider validates that each non-text part has a usable source.

```python
request = LLMRequest([{
    "role": "user",
    "content": [
        {"type": "text", "text": "Describe this image."},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
    ],
}])
response = provider.generate(request)
```

The current Ollama adapter forwards typed content to its API. Runtime-specific multimodal support must be declared in `ModelCapabilities.vision`, and the GUI should disable or explain unsupported combinations rather than silently dropping media.

## Embeddings

Use `provider.embed(text)` or `provider.embed([text1, text2])` to obtain normalized `EmbeddingResponse.embeddings`. Gemini sends one `embedContent` request per input. Ollama sends a batch to `/api/embed` and supports either `embeddings` or a legacy single `embedding` response.

```python
result = provider.embed(["first document", "second document"])
for vector in result.embeddings:
    print(len(vector))
```

Embedding dimensions, model identity, provider identity, and any provider usage metadata should be persisted with indexes. Orville should not mix vectors from incompatible embedding models in the same index without an explicit migration.

## Capability and safety requirements

The adapter layer normalizes transport behavior but does not grant permission to use a capability. The model registry and GUI must check the configured capability flags before sending vision, audio, embedding, streaming, or tool requests. User-provided media and URLs remain untrusted inputs; the security layer must enforce size, MIME, URL, network, privacy, and retention policies.

The adapters do not execute tool calls. They only normalize tool-call proposals. Authorization, argument validation, approval, side-effect control, and execution remain responsibilities of the orchestration layer.

## Tests

The Phase 3 suite uses fake transports and does not contact external services. It covers Ollama stream normalization, Gemini multimodal inline data conversion, Ollama batch embeddings, Gemini embedding normalization, existing structured outputs and tool payloads, local model cataloging, and all Phase 1 orchestration behavior.
