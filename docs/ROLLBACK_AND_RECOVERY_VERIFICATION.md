# Rollback Procedures and Recovery Verification

## Scope

Rollback is an **approval-gated restoration** to a previously approved release or source revision. Orville does not silently stop production services, delete data, restore a database, or invoke provider rollback commands. The local contract builds a reviewable plan and verifies evidence after an operator or deployment system performs the approved steps.

## Procedure

| Stage | Required action | Success evidence |
|---|---|---|
| 1. Stop promotion | Record the failed release, reason, scope, and approval reference; stop further promotion. | Sanitized incident/release record. |
| 2. Preserve evidence | Retain current logs, database/backup identifiers, image or source revision, health decision, and release artifacts. | Evidence inventory with no secrets. |
| 3. Protect credentials | If exposure is suspected, revoke or rotate through the approved credential manager before resuming service. | Value-free rotation/revocation record. |
| 4. Restore target | Restore the previously approved release and compatible non-secret configuration. Keep current data and evidence until review closes. | Target release identifier and restore result. |
| 5. Verify service | Run authenticated health, read-only state/checkpoint, and representative smoke checks. | All three checks pass against the restored target. |
| 6. Handle failed recovery | If any check fails, keep the incident open, quarantine the failed target, preserve diagnostics, and escalate to the environment owner. | Failed-check record and next recovery decision. |
| 7. Close | Record final release, backup checksum, validation results, residual risks, and approval. | Complete recovery verification record. |

`build_rollback_plan` in `orville_core.recovery` produces stages 1, 2, 4, and 5 as value-only steps. It requires an explicit failed release, rollback target, and approval reference and performs no deployment operation.

## Recovery verification

`verify_recovery_evidence` performs local, non-destructive checks against a retained backup and operator-supplied evidence. It recomputes the backup SHA-256 digest and requires successful authenticated health, read-only state, and smoke-workflow checks. A failed or incomplete result must not be declared a successful rollback.

The verification record contains only the backup path, checksum result, boolean evidence outcomes, and residual-risk wording. It must not contain credentials, bearer tokens, private keys, cookies, personal data, raw logs, or unredacted provider responses. The backup itself remains under the configured protected runtime-data or release-evidence boundary.

## Data and storage rules

Do not use `docker compose down --volumes` during rollback. Preserve named volumes, backups, current logs, and release evidence. For SQLite-backed deployments, restore only a verified backup and keep the original copy. Do not scale beyond the validated storage design. Runtime data, protected connector records, and model files remain outside source control.

## Standalone validation

```bash
python -m pytest tests/test_rollback_recovery.py -q
python -m py_compile orville_core/recovery.py orville_core/__init__.py tests/test_rollback_recovery.py
```

The local tests use temporary synthetic files and booleans; they do not call deployment systems, providers, browsers, connectors, or external networks. Live rollback and restore exercises remain deployment-owned and require target-specific approval, backups, monitoring, and audit controls.
