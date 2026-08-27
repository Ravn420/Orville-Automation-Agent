# M14.4 Enterprise Identity and Least-Privilege Authorization

`orville_core.enterprise_identity` provides a standalone authorization boundary for tenant-scoped operations. It consumes claims from an already trusted identity gateway; it does not implement OAuth, OIDC discovery, password storage, token issuance, or token exchange.

The local store persists tenant membership, scope grants, revocation state, explicit approvals, and sanitized authorization audit events. Every authorization decision validates tenant and actor identity, claim lifetime, active membership, action scope, and— for deployment, publication, approval, and trust-root actions—an unexpired approval reference matching the same tenant, actor, and action.

The implementation deliberately uses a narrow scope vocabulary: read, plan, execute, approve, publish, member management, integration management, canary deployment, and trust-root management. Unknown actions fail closed. Revoked memberships fail closed. Claim lifetimes are bounded to 24 hours, and tenant identifiers reject path/control characters.

## Integration boundary

A production OIDC/SAML or approved enterprise identity gateway must authenticate the user and produce validated claims before invoking this layer. The gateway remains responsible for signature verification, issuer/audience checks, MFA, group-to-scope mapping, session revocation propagation, and key rotation. Orville remains responsible for tenant authorization, action scope, approval gates, and secret-free audit evidence.

Production completion additionally requires an approved identity provider, tenant-isolation tests against the live gateway, revocation propagation evidence, least-privilege review, and operator approval. No live identity provider or credential is configured by this local module.
