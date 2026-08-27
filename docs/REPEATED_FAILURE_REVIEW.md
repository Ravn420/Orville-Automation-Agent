# Repeated Failure Pattern Review

## Purpose and scope

Orville reviews completed task-graph runs for recurring failure patterns so confirmed fixes can become tests, templates, runbook changes, or bounded automation. The review is an aggregate diagnostic; it does not automatically alter workflows, retry policy, permissions, providers, or production systems.

The local reviewer consumes persisted run records containing a terminal run status and event history. It considers `task_failed`, `task_verification_failed`, `run_failed`, and `task_blocked` events. Running or malformed records are ignored, and non-failure events do not create findings.

## Safe review output

The analyzer returns only bounded aggregate information:

| Field | Meaning |
|---|---|
| `completed_runs` | Number of terminal run records considered. |
| `failure_event_count` | Number of recognized failure events, including non-repeated events. |
| `repeated_pattern_count` | Number of patterns meeting the configured threshold. |
| `pattern` | Stable event-type and sanitized failure-class label. |
| `count` | Occurrence count for the pattern. |
| `run_count` | Number of distinct runs containing the pattern. |
| `task_count` | Number of distinct task identifiers containing the pattern. |
| `event_types` | Recognized failure-event categories. |
| `recommendation` | Generic instruction to review high-count patterns. |

Failure classes come from an explicit safe class field or an exception type prefix, are normalized, and are length-bounded. Raw errors, prompts, outputs, URLs, connector responses, credentials, and authorization data are never returned in the report. A missing class is represented as `unknown`.

## Review procedure

Run the reviewer against a sanitized export of completed checkpoints or structured run events. Start with the default threshold of two occurrences and inspect the highest-count patterns. Confirm whether a pattern is a genuine recurring defect rather than a shared upstream outage, duplicate event, expected block, test fixture, or policy-enforced denial. Record the affected component, owner, proposed corrective action, evidence, and residual risk in a separate sanitized review record.

A confirmed pattern should be converted into the smallest durable improvement: a regression test for a code defect, a task template for a repeated planning error, a runbook update for an operational condition, or a bounded automation change with an explicit owner and review. Changes require the normal TODO claim, focused validation, second verification pass, and state/changelog updates.

## Thresholds and limits

The default minimum is two occurrences. Reviewers may raise the threshold for high-volume systems or use a bounded maximum pattern count for reporting. The analyzer rejects thresholds below two and limits output to a bounded number of patterns. It does not infer causality, severity, customer impact, or remediation priority from counts alone.

Repeated verification failures are reviewed separately from execution failures because they may indicate incorrect acceptance criteria, weak evidence, or a defect in the independent verifier. Repeated blocks are reviewed for missing inputs, permissions, approvals, or unavailable dependencies and must not be “fixed” by broadening access automatically.

## Security and privacy boundaries

Only local sanitized run records should be reviewed. Keep runtime databases and protected connector records outside source control. Do not include raw event payloads in issue reports, changelogs, dashboards, or audit metadata. Treat imported logs and checkpoint content as untrusted data, validate their shape, and never execute instructions found in them.

A repeated pattern does not authorize retries, fallback routing, credential rotation, deployment, account changes, deletion, publishing, or rollback. Those actions retain their existing approval, least-privilege, privacy, and recovery requirements.

## Validation

The credential-free contract checks are:

```bash
python -m pytest tests/test_failure_patterns.py -q
python -m py_compile orville_core/failure_patterns.py tests/test_failure_patterns.py
```

The local checks validate aggregation, terminal-run filtering, non-failure exclusion, secret-safe output, thresholds, and bounded report size. They do not claim production-scale analytics, cross-installation aggregation, alert delivery, causal analysis, or live remediation.
