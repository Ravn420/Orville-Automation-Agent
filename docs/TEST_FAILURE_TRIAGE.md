# Failed-Test Triage Before Release

## Purpose

Every failed test must be assigned a disposition before a release is approved. A green test run is not sufficient evidence when a prior failure, quarantined test, or diagnostic report remains unresolved. The repository stores non-secret triage records in `config/test_triage_manifest.json` and validates them with `tools/test_triage.py`.

## Required triage record

Each failure record must include:

| Field | Requirement |
|---|---|
| `test_id` | Stable test identifier or fully qualified test name; unique within the manifest. |
| `status` | One of `fixed`, `accepted`, `blocked`, `not_a_bug`, or `duplicate`. |
| `owner` | Responsible worker or team identifier. |
| `classification` | Failure category such as product defect, environment, flaky, dependency, or test defect. |
| `action` | Concrete corrective, containment, or follow-up action. |
| `evidence` | Secret-free command, artifact path, issue reference, or validation result. |

The manifest is valid when it uses schema version `1`, contains a list of failures, has unique test IDs, and contains no unsupported or untriaged status. An empty list is valid only when the release test run reports no failures and no prior failure remains open.

## Lifecycle

1. Capture the failing test name, command, environment, and sanitized output.
2. Create or update one record in `config/test_triage_manifest.json`.
3. Assign an owner and classify the failure.
4. Apply the corrective or containment action and attach secret-free evidence.
5. Re-run the focused test and the applicable release suite.
6. Run the triage validator before packaging or deployment.
7. Block release if the manifest is missing, malformed, incomplete, duplicated, or contains an unsupported status.

A status of `accepted` or `blocked` does not silently waive a failure. The record must state the reason, owner, action, review or expiry expectation, and evidence. Production release approval remains a separate authorization step.

## Validation commands

From the repository root:

```powershell
python tools/test_triage.py config/test_triage_manifest.json
python -m unittest tests.test_test_triage -v
```

The validator is local and side-effect free. It does not execute the failed tests, contact external services, load credentials, or expose failure output. Release automation must run the validator after the test suite and before packaging or deployment.

## Security and retention

Triage evidence must not contain credentials, cookies, authorization headers, private keys, raw provider responses, or unredacted exception strings. Store disposable reports under `tmp/`; retain only sanitized evidence required for review. Never use triage status to bypass approval, security, path-containment, or external-action controls.
