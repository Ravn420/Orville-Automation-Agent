# Operational Dashboards and Reports

## Purpose

Orville provides a standalone operational report for environments that can retain structured JSONL execution logs. The report is suitable for local review, attached-desktop operation, sandbox validation, web-hosting operations, and persistent-computing operations. It is a report contract and does not claim that a hosted monitoring backend or live alerting service is installed.

## Supported targets

| Target | Local artifact | Operational use | External dependency |
|---|---|---|---|
| `local` | JSON report from a JSONL log | Developer and operator review | None |
| `attached-desktop` | JSON report in the configured workspace | Desktop troubleshooting and release evidence | None for generation |
| `sandbox` | Disposable JSON report | Preflight and smoke evidence | None for generation |
| `web-hosting` | JSON report from retained service logs | Service health review | Deployment-owned log collection |
| `persistent-computing` | JSON report from retained service logs | Long-running service review | Deployment-owned retention and alerting |

## Report fields

The report contains event count, distinct execution count, failure count, success rate, duration count/mean/maximum, status counts, target, and data-quality flags. It accepts only JSON objects, bounds input to 100,000 events, fails closed on malformed records, ignores blank lines, and includes no raw event payloads or credentials.

`tools/operational_report.py` generates the report:

```powershell
python tools\operational_report.py logs\execution.jsonl --target local --output artifacts\operational-report.json
```

## Review interpretation

Operators should inspect failure count and rate first, then status distribution, duration outliers, execution coverage, and data-quality flags. A success rate of `1.0` for an empty log means no failures were observed, not that an execution occurred. Missing or stale logs are an evidence-quality failure and must not be represented as service health.

The report is intentionally descriptive. It does not automatically restart services, suppress alerts, change credentials, publish artifacts, delete data, or modify accounts. Any follow-up sensitive action requires explicit confirmation and the relevant authorization boundary.

## Retention and privacy

Retain only sanitized structured logs and reports required for active operations, incident response, or reproducibility. Use the existing secret sanitizer before log persistence, keep runtime logs outside source-controlled directories where configured, and do not include prompts, credentials, authorization headers, cookies, private paths, or raw provider responses. For hosted and persistent targets, deployment owners must supply access-controlled retention, alert routing, and deletion schedules.

## Acceptance criteria

The operational-report contract is accepted when each supported target is named, the report fields are stable and bounded, malformed input fails closed, empty-log semantics are explicit, failures and duration are summarized, secret safety is stated, and sensitive follow-up actions remain approval-gated. Live dashboards, alert delivery, and infrastructure-level SLO collection remain deployment-owned extensions.

## Focused validation

```powershell
python -m unittest tests.test_operational_report -v
python -m py_compile tools\operational_report.py tests\test_operational_report.py
```

## Related contracts

- `orville_core/telemetry.py`
- `orville_core/structured_logging.py`
- `docs/HEALTH_MONITORING_LOGGING_RUNBOOKS.md`
- `docs/SECRET_HANDLING_RULES.md`
