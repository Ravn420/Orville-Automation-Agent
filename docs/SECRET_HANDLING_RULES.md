# Secret-Handling Rules

## Purpose

Orville treats provider credentials, API tokens, bearer values, refresh tokens, private keys, cookies, passwords, signing secrets, credential references, and account identifiers as sensitive. These rules define where secrets may originate, where they may be used, and where they must never appear. A secret-safe workflow is a combination of protected storage, least-privilege access, redaction, path containment, and verification; redaction alone is not a storage mechanism.

> Secret values must remain in an approved protected runtime boundary and must never cross into committed source, user-facing presentation, unredacted diagnostics, or retained evidence.

## Storage and handling matrix

| Surface | Allowed handling | Prohibited handling | Required validation |
|---|---|---|---|
| Environment variables | Inject at process start through an approved environment or deployment secret manager; read only in the owning server/provider adapter; use synthetic values in tests. | Printing full environments, echoing shell commands with live values, copying values into task prompts, GUI state, screenshots, or repository files. | Inspect variable names and presence only; never print values. Confirm deployment manifests reference secret injection rather than literals. |
| Configuration files | Commit `.env.example`, schemas, and non-secret placeholders; store live values in protected OS credential storage, external secret manager, or approved AppData/config boundary outside source control. | Committing `.env.production`, raw API keys, private keys, refresh tokens, cookies, or embedded credentials in JSON/YAML/TOML. | Secret scan tracked files and verify runtime paths are outside the repository. Review file permissions and backup scope. |
| Logs | Record safe provider, operation, correlation ID, status, error class, and redacted identifiers. Apply `SecretRedactor` before persistence or display. | Logging request headers, bearer values, query tokens, full environment values, raw exception payloads, prompt attachments, or unredacted provider responses. | Run redaction fixtures and inspect representative logs for token-shaped values. Retain only sanitized logs needed for operations or audit. |
| Artifacts and reports | Retain source, outputs, checksums, sanitized metadata, and reproducibility evidence after content review. Mark sensitive artifacts and keep them in approved protected storage when retention is required. | Including credentials in generated documents, code bundles, archives, fixtures, reports, exported metadata, or artifact previews. | Review artifact manifests, scan content and metadata, verify approved-root containment, and redact before promotion from `tmp/` to `artifacts/`. |
| Screenshots and recordings | Capture only the minimum UI state needed for review; mask secrets, personal data, local paths, account identifiers, and provider responses before retention or sharing. | Capturing credential fields, token previews, browser cookies, authorization headers, private paths, raw logs, or unreviewed desktop content. | Perform visual review and secret scan of the final image/video; retain only sanitized evidence under the approved artifact boundary. |

## Approved secret lifecycle

1. **Provision.** The operator supplies a credential through a protected environment mechanism, OS credential store, deployment secret manager, or approved connector flow. The value is never placed in a task message, source file, fixture, screenshot, or changelog.
2. **Reference.** Application state stores only a non-secret reference ID, provider, authentication method, scopes, status, and expiry metadata. A reference is not a substitute for authorization; it must be checked for provider, scope, lifecycle, and action policy.
3. **Use.** Only the owning server-side adapter reads the secret. The GUI, client bundle, prompts, logs, artifacts, and screenshots receive safe status and redacted projections, never the raw value.
4. **Redact.** Apply structured-key and token-pattern redaction before errors, logs, API diagnostics, previews, exports, and evidence are persisted or displayed. Redaction must be bounded and tested against nested values, headers, query strings, and exception text.
5. **Rotate or revoke.** Rotate or revoke credentials when exposure is suspected, a connector is retired, a test account is no longer needed, or a credential reaches expiry. Preserve only a safe incident identifier and error class.
6. **Recover.** If a secret may have crossed a prohibited boundary, stop the affected operation, preserve sanitized diagnostics, revoke or rotate the credential through the approved manager, remove the exposed value from the affected retention surface where authorized, and document the incident without repeating the secret.

## Repository and path rules

Live secret files must remain outside the repository and outside `artifacts/`, `logs/`, `tmp/`, `release/`, browser-extension bundles, and packaged application directories unless an approved encrypted secret mechanism explicitly owns the file. Runtime mutable state belongs under the configured AppData or portable data directory, with backup and access permissions appropriate to the deployment.

Examples and tests must use placeholders that are visibly synthetic, such as `synthetic-test-key`, and must not resemble a production token. Never use a credential discovered in the environment, another connector, a browser session, a downloaded file, or an external response as a test value. Do not run broad deletion or rewrite history as a secret-remediation shortcut; rotate first and use the repository's approved remediation process.

## Display and interface rules

The GUI may show provider name, credential reference ID, authentication method, scope summary, expiry state, and connection status. It may show whether a value is configured, but not the value itself. Secret inputs must use password-style controls, avoid clipboard or accessibility leakage where the platform permits, and clear transient values after submission. Error messages must identify the safe operation, failure class, and recovery action without including raw request data or provider diagnostics.

Screenshots, recordings, mockups, exports, and generated reports require the same review as logs. A hidden or password-masked field is not sufficient evidence of safety if the underlying value is present in HTML, accessibility text, browser storage, URLs, telemetry, or debug output.

## Validation checklist

- [ ] Live values originate only from approved protected secret boundaries.
- [ ] Committed configuration contains placeholders, schemas, or references—not live values.
- [ ] Server/provider adapters are the only raw-secret consumers.
- [ ] `SecretRedactor` is applied before logs, errors, diagnostics, exports, and evidence are retained.
- [ ] Artifacts and screenshots receive path, metadata, and content review before retention.
- [ ] Tests use synthetic credentials and local endpoints only.
- [ ] Credential references enforce provider, scope, expiry, revocation, and action policy.
- [ ] Rotation, revocation, incident handling, and recovery steps are documented.
- [ ] Secret scans inspect source, configuration, logs, artifacts, screenshots, and packaged outputs.

## Focused validation

From the repository root:

```powershell
python -m unittest tests.test_secret_handling_rules -v
python -m py_compile tests\test_secret_handling_rules.py
```

The focused tests verify that every required surface is covered, prohibited raw-secret patterns are absent from the contract, and the existing redactor masks nested credential fields, bearer values, query tokens, and token-shaped values. They use synthetic values only and do not contact external services.

## Related contracts

- `orville_core/security.py`
- `tests/test_security.py`
- `ENVIRONMENT_SETUP.md`
- `docs/WORKFLOW_DRY_RUN.md`
- `docs/GUI_STANDALONE_OPERATIONS.md`
