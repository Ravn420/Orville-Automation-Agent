# Standalone examples

These examples use only the Orville package, Python standard-library facilities, and local temporary or runtime paths. They do not import Manus modules, invoke MCP, require a browser session, load provider credentials, contact an external service, or perform sensitive actions.

## Basic checkpointed workflow

Run from the repository root after installation:

```powershell
python examples\basic_run.py
```

The script creates a two-node dependency-aware graph, executes deterministic local handlers, persists a checkpoint under `.orville/checkpoints`, and prints the run status. Use a disposable working directory when experimenting with checkpoint output.

## Local operational report

Create a small local JSONL event file and summarize it without a service:

```powershell
@'
{"execution_id":"demo-run","status":"completed","duration_seconds":0.25}
{"execution_id":"demo-run","status":"failed","level":"error","duration_seconds":0.50}
'@ | Set-Content .\tmp\demo-events.jsonl
python tools\operational_report.py .\tmp\demo-events.jsonl --target local
```

The report is descriptive only. It does not restart services, publish artifacts, change accounts, rotate credentials, or contact a provider.

## Standalone execution expectations

Run examples with a virtual environment and from the repository root so the local package is importable. If a provider, connector, browser, or deployment target is needed, use the corresponding operational documentation rather than modifying these examples to embed credentials or bypass safety gates.
