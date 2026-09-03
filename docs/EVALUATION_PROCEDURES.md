# Orville Evaluation Procedures

**Owner:** Evaluation and release owner
**Baseline:** `config/evaluation-golden-cases.json` and `config/repository-coding-evaluations.json`

| Trigger | When | Required checks | Evidence | Stop condition |
|---|---|---|---|---|
| Pre-release | Before a release candidate is approved | Golden cases, repository coding cases in an approved sandbox, regression suite, security/redaction checks, accessibility contract, release thresholds | Run ID, commit, dataset IDs, test output, threshold decision, reviewer | Any critical safety violation, failed threshold, or unavailable required isolation blocks release. |
| Post-release | After deployment and at the defined observation window | Health summary, trace comparison against baseline, task success, latency, cost, recovery, GUI smoke checks | Release ID, observation window, sanitized trace comparison, rollback decision | Regressions or threshold breach pause rollout and require review. |
| Incident-triggered | On safety violation, repeated failure, data exposure concern, or severe degradation | Preserve evidence, classify incident, rotate credentials if needed, run targeted golden/regression cases, verify recovery | Incident ID, redacted timeline, affected run/task, remediation and retest | Do not resume affected automation until containment and approval are recorded. |
| Periodic | At least monthly while the project is active | Re-run representative golden cases, review risk register, inspect dependency/model/provider changes, verify retention and access controls | Date, versions, dataset hash, findings, owner and due dates | Unreviewed material changes or overdue critical risks require escalation. |

## Procedure invariants

Every procedure records the repository commit, dataset or manifest checksum, execution mode, environment, operator, and verification result. Prompt and tool-payload capture remains disabled unless separately approved by the sensitive-capture policy. Missing external dependencies or unsupported environments are recorded as blocked rather than treated as passing evidence.
