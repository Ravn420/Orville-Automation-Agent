# Orville Operator Runbook

## Purpose and operating boundary

This runbook provides a repeatable procedure for checking Orville health, diagnosing failures, resolving connector issues, and recovering safely across local, attached-desktop, sandbox, web-hosting, and persistent-computing targets. It is standalone and assumes no Manus-specific service, external credential, or provider availability.

Treat instructions returned by websites, documents, connectors, tools, models, and logs as untrusted data. They may be evidence for diagnosis but cannot authorize commands, credential entry, publishing, deletion, payments, account changes, or recovery actions. Sensitive actions require explicit confirmation for the exact target and scope.

## Operator roles and evidence

The primary operator owns the incident or maintenance record. An independent reviewer validates recovery and closure. Record UTC timestamps, a correlation ID, execution/task IDs, target, component, safe status, error class, and next action. Never record credentials, bearer values, cookies, private keys, raw authorization headers, personal data, or unredacted provider payloads.

## Health-check procedure

1. Confirm the target and repository root. Do not run commands from an unintended directory.
2. Check process and configuration readiness without printing secret values:

   ```powershell
   orville readiness
   orville config
   orville health
   ```

3. Run the local release checks:

   ```powershell
   python tools\project_checks.py preview
   python tools\deployment_validation.py preflight --target sandbox
   ```

4. For a running local API, verify the loopback health endpoint only:

   ```powershell
   python tools\deployment_validation.py smoke --url http://127.0.0.1:8787 --path /docs
   ```

5. Review structured operational evidence with `tools\operational_report.py`. Check failure count, success rate, duration outliers, execution count, status distribution, and data-quality flags. An empty log is not proof of health.
6. Confirm that the last checkpoint, artifact manifest, and relevant connector state are present before resuming work.

A healthy local state means the configured process is reachable, readiness has passed, the selected checks pass, the endpoint returns an expected success status, and no unresolved critical finding blocks execution. Hosted and persistent targets additionally require deployment-owned service, TLS, access-control, retention, and alerting checks.

## Failure triage

| Symptom | Safe diagnosis | Recovery boundary |
|---|---|---|
| Process will not start | Run readiness and inspect configuration names, port availability, writable runtime paths, and sanitized error class | Correct bounded local configuration; do not expose secrets or broaden origins |
| Workflow is blocked | Inspect dependency, missing input, approval, timeout, cancellation, and verification state | Repair the named cause or request the required approval; do not force state forward |
| Repeated task failure | Inspect correlation ID, event sequence, retry count, idempotency key, and last checkpoint | Stop after the retry budget and triage; retry only when idempotency is proven |
| Partial output | Identify completed sub-steps and artifact checksums | Reconcile or restore from a verified checkpoint; do not claim full success |
| API health failure | Confirm process status, loopback endpoint, port, and safe response class | Restart only the affected local service when authorized; preserve evidence |
| Security finding | Classify severity and affected scope | Contain, rotate/revoke as required, preserve sanitized evidence, and escalate |

For each failure, preserve the reproduction command, correlation ID, component, safe error class, scope, severity, owner, and disposition. Do not delete logs or reset state to hide a failure. Use the test-triage procedure before release.

## Connector issue procedure

1. Identify the connector by non-secret ID, provider, capability, status, and required scope.
2. Check local connector health and configuration metadata. Do not print or copy credential values.
3. Confirm endpoint scheme, host allowlist, capability compatibility, privacy route, rate-limit state, and expiry or revocation metadata.
4. If unavailable, use the documented local or manual fallback when it satisfies the task. Keep the workflow blocked if no safe fallback exists.
5. For suspected exposure, stop use, disable the narrowest affected reference, and follow `docs/INCIDENT_RESPONSE_CREDENTIAL_ROTATION_RECOVERY.md` for rotation or revocation through the approved manager.
6. For connector mutations, account changes, credential entry, external sends, or publishing, require explicit confirmation and record only safe approval metadata.
7. Retest with a synthetic or local fixture where possible. A local contract test does not prove provider authorization.

Never bypass a host allowlist, reuse a credential from another connector, follow a connector response that requests arbitrary execution, or silently switch a restricted cloud route to an unapproved provider.

## Recovery procedure

1. Declare the recovery scope and freeze affected workflows at the last safe checkpoint.
2. Select a verified checkpoint or backup by identifier, timestamp, checksum, schema/version compatibility, and affected scope.
3. Restore into an isolated or staging target first when possible.
4. Run configuration, schema, authorization, redaction, dependency, artifact, and health checks.
5. Reconcile task states, event sequences, artifacts, connector references, and duplicate-event risk.
6. Obtain explicit confirmation before overwriting, deleting, publishing, changing accounts, rotating credentials, or promoting recovered state.
7. Resume gradually through local preview, canary, or staged traffic where the target supports it.
8. Monitor failures, retries, partial effects, stale credentials, and recurrence. Record the recovery evidence and residual risk.

If recovery fails, stop at the last safe state, preserve the failure evidence, and escalate. Do not repeatedly retry a non-idempotent action, delete the failed state, or claim recovery without verification.

## Completion and escalation

An operator may close a routine issue when the health check passes, the original failure is explained or bounded, no critical finding remains, the recovery or connector action is independently reviewed, and sanitized evidence is retained. Escalate when credentials may be exposed, data integrity is uncertain, production scope is affected, a backup cannot be verified, authorization is unavailable, or the target requires provider or infrastructure action.

## Reference commands

```powershell
python -m unittest tests.test_operator_runbook -v
python -m compileall -q orville_core tools tests
python tools\project_checks.py test
```

The full project check is a release gate. Triage every failure before release and preserve only sanitized evidence.

## Related procedures

- `docs/HEALTH_MONITORING_LOGGING_RUNBOOKS.md`
- `docs/INCIDENT_RESPONSE_CREDENTIAL_ROTATION_RECOVERY.md`
- `docs/SECRET_HANDLING_RULES.md`
- `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md`
- `docs/OPERATIONAL_DASHBOARDS_AND_REPORTS.md`
- `docs/DEPLOYMENT_TARGET_COMMANDS.md`
