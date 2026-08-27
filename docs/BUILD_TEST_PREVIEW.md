# Automated Build, Test, and Preview Procedures

## Purpose

Orville provides one standalone command surface for repeatable local validation. The entrypoint is `tools/project_checks.py`; it runs from the repository root, does not require Manus services, and fails on the first unsuccessful check.

## Prerequisites

Use Python 3.10 or newer with the project dependencies installed. Install development dependencies in an isolated environment:

```text
python -m pip install -e ".[dev]"
```

The commands do not require cloud credentials. The optional API preview smoke test uses only the local API and a user-provided `.env.production` token; it must never print that token.

## Check commands

| Command | Procedure | Expected result |
| --- | --- | --- |
| `python tools/project_checks.py build` | Compiles `orville_core`, `tools`, and `windows_gui.py`, then builds a no-dependency wheel. | A wheel exists under `tmp/project-check-wheels/`. |
| `python tools/project_checks.py test` | Runs the complete `pytest` suite with quiet output. | Pytest exits successfully. |
| `python tools/project_checks.py preview` | Runs the local Signal Room smoke, document-language, reduced-motion, focus, and stylesheet checks. | The preview checks pass; existing contrast findings may be warnings. |
| `python tools/project_checks.py preview --api-smoke` | Runs the static preview checks and the existing authenticated local API workflow smoke script. | Local API health, state, artifacts, objective, run, events, approval, and cancellation checks complete successfully. |
| `python tools/project_checks.py all` | Runs build, test, and static preview checks in order. | All three procedures pass. |
| `python tools/project_checks.py all --api-smoke` | Runs all checks plus the optional local API smoke test. | All checks and local API smoke pass. |

The optional API smoke requires a running local API at `http://127.0.0.1:8787` and a user-created `.env.production` containing `ORVILLE_API_TOKEN`. The token is read by the existing local smoke script and is never generated, persisted by this procedure, or displayed by the wrapper.

## Build procedure

The build step is source-focused and reproducible. It compiles the Python package and operational tools, then invokes `pip wheel --no-deps` into the disposable `tmp/project-check-wheels/` directory. The wheel is a validation artifact, not a release. Use `tools/release_gate.py` when the security evidence and release-specific gates are also required.

## Test procedure

The test step runs the repository’s configured `pytest` test paths. Focused tests should be run first while developing a change; this command is the repeatable regression check before delivery. Tests must use synthetic credentials and local endpoints only.

## Preview procedure

The default preview step is credential-free and does not start a server or contact an external service. It validates the bundled `webui` files through `tools/signal_room_checks.py`. For a live local API preview, start the API through the documented local run procedure, verify that it binds to `127.0.0.1:8787`, and then use `--api-smoke`. The API smoke performs local workflow mutations and cancellation only; do not aim it at production or a remote host.

## Failure handling and evidence

A non-zero exit code blocks delivery. Record the exact command, first failing check, relevant output, corrective action, and rerun result in the task handoff or retained validation artifact. Do not treat a generated wheel or a running preview as proof that tests passed. Remove disposable wheel and cache output according to `AGENTS.md` after validation unless it is explicitly retained as release evidence.

## Safety boundaries

These procedures do not publish content, deploy to production, change accounts, purchase services, submit external forms, or create credentials. The optional API smoke is restricted to the loopback address and requires an existing user-provided token. Never commit `.env.production`, tokens, generated caches, or wheel output.
