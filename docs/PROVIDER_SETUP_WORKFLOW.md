# Guided Provider Setup Workflow

**Status:** completed-local for desktop onboarding and safe health-check UI  
**Owner:** IDE Agent with Verification Agent review  
**Runtime:** Windows Tkinter desktop client with the local Orville API

## Summary

The desktop control center now exposes **Provider setup** from the sidebar. The workflow supports guided defaults for Ollama, Gemini, OpenAI-compatible local endpoints, and Anthropic. It accepts a user-supplied provider ID, model name, endpoint, optional API key, timeout, and declared capabilities, then submits the provider configuration to the authenticated local API.

The workflow also provides provider inventory refresh and provider health checks. Health output is rendered as the API's structured, redacted result; prompts, generated responses, and API-key values are not displayed by the UI.

## Supported setup presets

| Provider type | Default endpoint | Default model | Intended use |
|---|---|---|---|
| `ollama` | `http://127.0.0.1:11434` | `llama3.2` | Local inference |
| `gemini` | `https://generativelanguage.googleapis.com` | `gemini-2.5-flash` | User-approved cloud inference |
| `openai_compatible` | `http://127.0.0.1:8000/v1` | `local-model` | Local compatible server |
| `anthropic` | `https://api.anthropic.com` | `claude-3-5-sonnet-latest` | User-approved cloud inference |

The defaults are editable and are not credentials. The user remains responsible for supplying a valid endpoint, model, and credential through an approved secure source.

## Security boundaries

The API key field is masked and cleared from the form after submission. The GUI does not write credentials to project files, checkpoints, logs, or artifacts. The local API remains responsible for endpoint validation, provider registration, secret redaction, and health-check error handling.

The privacy selector is currently **advisory UI only**. It does not authorize remote transmission and is intentionally not included in the provider registration payload until routing policy persistence is implemented. Remote execution must therefore continue to use the existing explicit routing and approval controls.

## Validation

Run the following commands from the repository root:

```powershell
python -m py_compile windows_gui.py
python -m pytest -q
```

A manual smoke check should start the desktop client, open **Provider setup**, confirm each preset supplies the documented defaults, save a synthetic local provider against a test endpoint, refresh the inventory, and run **Test provider health**. Do not use production credentials in a smoke test.

## Known limitations

The workflow does not yet discover provider models, persist privacy classes, configure rate limits, export redacted provider templates, or implement Blackbox OAuth/device authorization. Those remain separate roadmap items. The health button invokes the provider inventory health route; provider-specific network behavior remains dependent on the configured adapter and endpoint.
