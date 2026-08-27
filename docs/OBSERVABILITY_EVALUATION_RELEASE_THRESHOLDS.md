# Observability, evaluation, security, and release thresholds

## Scope

Orville records bounded operational evidence without retaining prompts, credentials, bearer tokens, cookies, or arbitrary high-cardinality payloads. The local trace recorder writes append-only JSON Lines records through `SecretRedactor`; the telemetry registry aggregates counts, failure classes, retries, verification outcomes, and lifecycle phase durations; and the production metric source normalizes tenant, cohort, and release-scoped samples.

## Evaluation and security evidence

The retained regression manifest at `tests/fixtures/regressions/manifest.json` is the local fixture index. It covers scheduled retry/idempotency, dry-run mutation suppression, and nested secret redaction. Focused security tests must continue to exercise credential redaction, boundary validation, approval handling, and safe failure behavior. Fixture assertions must remain deterministic and must not contain live credentials or personal data.

## Release thresholds

The default non-secret profile is stored in `config/release-thresholds.example.json` and is evaluated by `orville_core.release_thresholds.evaluate_release_thresholds`:

| Signal | Default threshold | Release rule |
|---|---:|---|
| Samples | At least 1 | Required evidence must exist. |
| Error rate | At most 5% | Candidate must not exceed the limit. |
| P95 latency | At most 2,000 ms | Candidate must not exceed the limit. |
| Saturation | At most 90% | Candidate must not exceed the limit. |
| Security findings | 0 | Any finding fails the default profile. |
| Business health | At least 0.80 | A missing value fails closed. |
| Release quality | At least 0.90 | A missing value fails closed. |

The evaluator returns per-check booleans, observed values, and the applied thresholds. It does not deploy, roll back, contact providers, or authorize external changes. A release controller may consume the decision only after its own approval, environment, and rollback gates pass.

## Validation

```text
python -m pytest -q tests/test_observability_release_evidence.py tests/test_telemetry.py tests/test_telemetry_metrics.py tests/test_phase_duration_metrics.py tests/test_security_attack_surfaces.py tests/test_security_hardening.py
python -m py_compile orville_core/observability.py orville_core/telemetry.py orville_core/production_metrics.py orville_core/release_thresholds.py tests/test_observability_release_evidence.py
```

The repository-wide release gate remains responsible for compilation, regression tests, wheel creation, and its existing security prerequisites. Provider-backed metric collection, OpenTelemetry export, live deployment, and production alerting remain deployment-owned follow-up work.
