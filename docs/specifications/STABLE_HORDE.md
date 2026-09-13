# Stable Horde Code-Generation Integration

Orville supports Stable Horde, also called AI Horde, as a remote **text-generation provider for code tasks**. The adapter submits an asynchronous text-generation request, polls its status, and returns generated source text through Orville’s existing `LLMProvider` and `ProviderRouter` contracts.

## Configuration

```dotenv
ORVILLE_STABLE_HORDE_API_KEY=your-api-key
ORVILLE_STABLE_HORDE_MODEL=aphrodite
ORVILLE_STABLE_HORDE_BASE_URL=https://aihorde.net/api
```

The provider is registered during API startup when either the model or API-key variable is present. If no key is supplied, Orville uses the anonymous AI Horde key `0000000000`, which has lower queue priority. Keep registered keys server-side and never commit them to source control.[1]

`ORVILLE_STABLE_HORDE_MODEL` must name an active **text model** available through AI Horde. The adapter sends that value in the `models` array and registers the provider with `text=true`, `code=true`, and `streaming=true`, allowing existing code-generation objectives to route to it. Active model availability can change as workers join or leave the Horde; verify names through the provider health endpoint or the [AI Horde model directory](https://aihorde.net/details/models/).

## Code-generation workflow

Orville uses the existing objective API. Create a code-generation objective, optionally selecting the Stable Horde provider explicitly:

```bash
curl -X POST \
  -H "Authorization: Bearer $ORVILLE_API_TOKEN" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8787/api/v1/objectives \
  -d '{
    "objective": "Add a retry helper to the HTTP client and include unit tests.",
    "deliverables": ["orville_core/providers.py", "tests/test_providers.py"],
    "acceptance_criteria": ["all tests pass"],
    "provider_id": "stable-horde",
    "generation_mode": "code"
  }'
```

Execute the returned run:

```bash
curl -X POST \
  -H "Authorization: Bearer $ORVILLE_API_TOKEN" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8787/api/v1/objectives/<run-id>/execute \
  -d '{}'
```

The objective’s code-generation tasks request the `code` and `streaming` capabilities. Stable Horde’s implementation performs the asynchronous request and exposes the completed response as a normalized `LLMResponse`; its `stream()` method yields the completed text as one final chunk because the AI Horde text API is asynchronous rather than a token-streaming endpoint.

## Provider registration through the API

Stable Horde can also be registered without environment variables:

```bash
curl -X POST \
  -H "Authorization: Bearer $ORVILLE_API_TOKEN" \
  -H "Content-Type: application/json" \
  http://127.0.0.1:8787/api/v1/providers \
  -d '{
    "provider_id": "stable-horde",
    "provider_type": "stable-horde",
    "model": "aphrodite",
    "base_url": "https://aihorde.net/api",
    "api_key": "your-api-key",
    "capabilities": ["text", "code", "streaming"]
  }'
```

Accepted provider type aliases are `stable-horde`, `stablehorde`, `ai-horde`, and `aihorde`.

## Operational behavior

AI Horde text generation follows an asynchronous workflow. Orville submits to `POST /v2/generate/text/async`, polls `GET /v2/generate/text/status/{id}`, and reads completed text from the response’s `generations[].text` values.[2] The adapter uses the configured model, converts provider-neutral messages into a role-labelled prompt, forwards `max_tokens` as `max_length`, and forwards `temperature` when supplied.

HTTP failures, faulted requests, missing request IDs, empty completed responses, unsupported embeddings, and timeouts are normalized to `ProviderError`. The provider timeout is controlled by `ProviderConfig.timeout_seconds`; the default is 60 seconds per HTTP request and the polling loop uses the same overall timeout.

## Validation

Run the complete suite from the repository root:

```bash
python -m pytest -q
```

The provider tests use an injected fake HTTP client and do not contact AI Horde. They validate code-generation payloads, authentication headers, asynchronous polling, response normalization, health checks, and factory dispatch.

## References

[1]: https://aihorde.net/details/models/ "AI Horde model directory and quickstart information"
[2]: https://github.com/Haidra-Org/AI-Horde/blob/main/README_integration.md "AI Horde integration workflow and text-generation endpoints"
