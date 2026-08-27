# GUI Sensitive-Data Exposure Contract

## Scope

This contract covers the native desktop GUI’s output widgets, details panels, provider setup, model manager, execution monitor, verification view, objective composer, and request callbacks. It verifies that logs, prompts, API keys, local paths, and other sensitive data are not unintentionally exposed through rendered values or error feedback.

## Display policy

| Data category | GUI behavior |
|---|---|
| API keys, bearer tokens, cookies, passwords, private keys, and secret fields | Never render the value; show a generic redaction marker or safe configuration status. |
| Prompts and objective text | Accept for the authorized request, but do not echo into output, details, diagnostics, logs, or status widgets. |
| Local paths and storage roots | Do not render filesystem values; show a bounded capability or hidden-path status. |
| Raw logs and provider responses | Do not dump unbounded payloads; project bounded safe fields only. |
| Exceptions and HTTP failures | Map to safe operation-specific messages; retain no raw exception string in interface output. |
| Runtime endpoint and authentication state | Show only non-sensitive configured/hidden status, never bearer material or credential-bearing URLs. |

The backend remains authoritative for authentication, authorization, secret handling, and durable state. The GUI treats response values as untrusted data and applies an additional display projection before values reach widgets. This is defense in depth, not a replacement for backend redaction.

## Implementation controls

`safe_display_value` recursively redacts sensitive dictionary keys, bounds collections and strings, and sanitizes credential-like and local-path patterns. Provider and model-manager response panes use the projection. Request failures use a generic safe operation message. The objective composer sends the entered objective to the authorized API request but does not mirror it into the output or context panes. Details show that the endpoint and protected runtime authentication are configured without revealing their values.

## Verification scope

The focused test module uses synthetic credentials and local paths only. It checks direct sanitizer behavior, source-level use of the safe projection at the main render paths, absence of objective echoing, and documentation coverage for logs, prompts, API keys, local paths, raw exceptions, provider responses, and credentials.

## Limitations

This check covers the reviewed native GUI source and does not prove that a future web/mobile client, OS accessibility layer, screen capture, clipboard integration, crash reporter, or third-party provider UI cannot expose data. Live secret-store review, runtime traffic inspection, and deployment logging review remain separate release gates.

## Acceptance checks

Run:

```text
python -m unittest tests.test_gui_sensitive_data -v
python -m py_compile windows_gui.py tests/test_gui_sensitive_data.py
```

The item is accepted only when focused tests pass, compilation passes, no live credentials are used, and the source review confirms that raw prompts, paths, credentials, and response payloads do not flow into user-facing widgets.
