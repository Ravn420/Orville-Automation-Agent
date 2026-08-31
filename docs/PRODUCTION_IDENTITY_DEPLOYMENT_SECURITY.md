# Production Identity and Deployment Security Contract

This contract defines the minimum production boundary for Orville's authenticated API and GUI. It is a deployment requirement, not a claim that this attached local worktree is connected to a production identity provider or audit service.

## Required controls

| Control | Production requirement | Verification evidence |
|---|---|---|
| Identity provider | Use an approved OIDC/OAuth 2.0 identity provider with issuer discovery pinned to an approved issuer, Authorization Code + PKCE for interactive clients, short-lived access tokens, and key rotation. Local development may use a synthetic identity adapter only. | Issuer and JWKS configuration review; login/logout and expired-token tests; no live token values in repository files. |
| Scoped authorization | Validate issuer, audience, signature, expiry, nonce/state, and tenant/user/task context. Map claims to least-privilege scopes such as `task:read`, `task:run`, `approval:write`, and `artifact:read`; deny missing or excessive scope. | Matrix tests for each route and scope; denial evidence for missing, expired, wrong-audience, and cross-task credentials. |
| TLS | Require HTTPS at the public boundary, modern protocol/cipher policy, valid certificate chain, secure cookies, HSTS after deployment review, and no plaintext credential or session transport. TLS termination must preserve the authenticated client context to the application. | Deployment scan, certificate-expiry alert, redirect and secure-cookie checks, and a documented local HTTP-disabled mode. |
| Deployment secrets | Inject provider secrets, signing keys, encryption keys, database credentials, and audit-sink credentials through the deployment secret manager or protected environment references. Never place values in source, images, logs, fixtures, screenshots, or client bundles. | Secret inventory containing names and owners only; startup check for required references; redacted configuration review and rotation record. |
| CORS allowlist | Permit only explicitly configured HTTPS origins. Reject wildcard origins with credentials, dynamic reflection of request origins, unapproved methods, and unapproved headers. Keep the allowlist separate from authentication and review changes as deployment configuration. | Preflight tests for allowed and denied origins, credentialed requests, methods, and headers. |
| Audit-log sink | Send append-only, structured, redacted audit events to an access-controlled sink with retention, integrity, clock, delivery-failure, and alerting policies. Events must include actor reference, task/run reference, action, decision, outcome, timestamp, and correlation ID without raw secrets or payloads. | Sink connectivity and retry test, redaction test, access review, retention setting, and alert for delivery failure. |

## Authorization boundary

Authentication establishes who is acting; authorization establishes what that actor may do in the current tenant, task, and risk context. Every sensitive operation is checked server-side against the current subject, scope, resource ownership, approval state, and policy. Client-provided role labels, model text, browser state, or UI visibility are never authorization evidence. External side effects remain deny-by-default and require the existing approval gate.

## Configuration contract

Production deployment must provide references, not values, for `ORVILLE_OIDC_ISSUER`, `ORVILLE_OIDC_AUDIENCE`, `ORVILLE_CORS_ALLOWED_ORIGINS`, `ORVILLE_TLS_MODE`, `ORVILLE_SECRET_PROVIDER`, and `ORVILLE_AUDIT_SINK`. The repository may document synthetic examples such as `https://idp.example.invalid/tenant`; it must not contain real issuer credentials, private keys, bearer tokens, cookies, or sink URLs.

## Rollout and failure behavior

A deployment fails closed when issuer metadata, signing keys, TLS policy, secret references, CORS configuration, or audit-sink policy is missing or invalid. Authentication or authorization failures return bounded, non-secret errors. Audit delivery failures raise an operational alert and follow the configured durability policy; they must not silently discard sensitive-operation decisions. Configuration changes require review, a reversible deployment, focused security checks, and a recorded owner.

## Local validation boundary

This repository can validate configuration schemas, denial behavior, redaction, and synthetic route matrices without contacting a real identity provider or audit sink. Production issuer registration, certificate issuance, secret provisioning, CORS origin approval, and sink provisioning require an authorized deployment owner and are intentionally not performed by this task.
