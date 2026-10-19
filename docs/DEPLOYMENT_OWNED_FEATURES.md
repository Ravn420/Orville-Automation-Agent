# Deployment-Owned Feature Matrix

**Purpose:** Document features that require a production environment for full validation and provide clear handoff criteria for deployment teams.

**Status:** Active  
**Last Updated:** 2026-10-16  
**Owner:** Documentation Agent  

---

## Overview

This matrix distinguishes between:
- **Local contracts**: Implemented and tested in the local codebase
- **Deployment-owned features**: Require production environment, credentials, and operational procedures for full validation

Deployment teams must verify all handoff criteria before claiming completion of deployment-owned features.

---

## Feature Matrix

### 1. Live Provider Integrations (Blackbox, etc.)

| Attribute | Details |
|-----------|---------|
| **Feature Name** | Live Provider Integrations |
| **Description** | Production-grade integration with cloud inference providers (Blackbox, etc.) through a hosted relay boundary |
| **Local Contract** | `orville_core.cloud_relay_boundary`, connector store, admission rules, privacy controls |
| **Why Production-Required** | Provider credentials must be server-side; real quota, rate limiting, and streaming behavior only observable with live provider |
| **Related Documents** | [`BLACKBOX_INTEGRATION.md`](BLACKBOX_INTEGRATION.md), [`BLACKBOX_INTEGRATION_RESEARCH.md`](BLACKBOX_INTEGRATION_RESEARCH.md) |

#### Local Contract Status
- ✅ Cloud relay boundary with deterministic policy foundation
- ✅ Connector store with OS-backed encryption (Windows DPAPI / Fernet)
- ✅ Privacy rule enforcement (`cloud_approved`, `local_only`, `restricted`)
- ✅ Per-mode quota ledger (not production billing store)
- ✅ Redacted status endpoints (no secret exposure)
- ✅ Separate managed vs user-connected access paths

#### Handoff Criteria for Deployment
| Criterion | Verification Method |
|-----------|---------------------|
| Relay service deployed with server-side credential isolation | Inspect relay environment variables; confirm `BLACKBOX_API_KEY` is server-only |
| Authenticated session boundary implemented | Verify bearer token validation on all relay endpoints |
| Per-tenant quotas and rate limiting configured | Review quota policy configuration; test threshold enforcement |
| Streaming response relay operational | Test streaming endpoint with live provider request |
| Cancellation semantics implemented | Verify request cancellation propagates to provider |
| Audit records capturing admission decisions | Check audit sink for redacted admission events |
| Abuse prevention and consent tracking enabled | Review privacy consent flow and abuse detection rules |
| Credential rotation procedure documented | Confirm rotation playbook exists and is tested |

#### Verification Checklist
- [ ] Relay service health check passes (`/health` returns 200)
- [ ] Managed access works without client credential
- [ ] User-connected access stores credentials encrypted
- [ ] Privacy rules block `local_only` requests without explicit approval
- [ ] Quota enforcement blocks requests over limit
- [ ] Status endpoint returns redacted data (no API keys, tokens)
- [ ] Audit log contains admission events without secrets
- [ ] Provider credential is absent from all client responses and logs

#### Required Credentials/Configuration
```bash
# Server-side only (relay environment)
BLACKBOX_API_KEY=<server-only-provider-key>
ORVILLE_RELAY_CLIENT_TOKEN=<high-entropy-client-token>

# Client-side (desktop environment)
ORVILLE_BLACKBOX_RELAY_URL=https://relay.example.com/v1
ORVILLE_BLACKBOX_RELAY_ALLOWED_HOSTS=relay.example.com
ORVILLE_BLACKBOX_RELAY_MODEL=blackboxai/openai/gpt-5.5
ORVILLE_BLACKBOX_RELAY_ENABLED=1
ORVILLE_BLACKBOX_RELAY_PLAN=managed
ORVILLE_RELAY_SUBJECT=device-or-session-id
```

---

### 2. Production Trust-Root Ceremony

| Attribute | Details |
|-----------|---------|
| **Feature Name** | Production Trust-Root Ceremony |
| **Description** | Approval-gated workflow for production trust-root bootstrap, rotation, and revocation evidence |
| **Local Contract** | `orville_core.trust_root_ceremony`, `TufRepositoryVerifier`, ceremony service |
| **Why Production-Required** | Requires approved root metadata, out-of-band digest verification, and operator approval through official channels |
| **Related Documents** | [`M14_PRODUCTION_TRUST_ROOT_CEREMONY.md`](M14_PRODUCTION_TRUST_ROOT_CEREMONY.md) |

#### Local Contract Status
- ✅ Ceremony workflow with operator identifier, approval reference, timestamp
- ✅ SHA-256 digest verification against independent out-of-band channel
- ✅ Bootstrap, rotation, and revocation evidence recording
- ✅ Non-secret evidence record (action, status, version, digest, operator, timestamp, reason)
- ✅ Command-line helper at `tools/tuf_root_ceremony.py`
- ✅ Reusable ceremony service `ProductionTrustRootCeremony`

#### Handoff Criteria for Deployment
| Criterion | Verification Method |
|-----------|---------------------|
| Approved root metadata available through official out-of-band process | Confirm metadata source and approval chain |
| Independent digest verification channel established | Verify digest comparison procedure with security team |
| Operator approval workflow configured | Review approval ticketing system integration |
| Protected audit location provisioned | Confirm evidence storage location and access controls |
| Separate operator verification procedure defined | Document second-operator verification steps |

#### Verification Checklist
- [ ] Ceremony requires explicit operator identifier
- [ ] Ceremony requires approved change/approval reference
- [ ] Ceremony requires ISO-8601 approval timestamp
- [ ] Ceremony requires canonical SHA-256 digest from independent channel
- [ ] Ceremony requires written reason for change
- [ ] Bootstrap validates signed root through `TufRepositoryVerifier`
- [ ] Rotation requires increasing root version and dual-policy verification
- [ ] Revocation records digest and reason without deleting root
- [ ] Evidence record contains only non-secret metadata
- [ ] Evidence JSON retained in protected audit location
- [ ] Verification from separate operator session succeeds

#### Required Credentials/Configuration
```bash
# Ceremony inputs (operator-provided at runtime)
OPERATOR_ID=<approved-operator-identifier>
APPROVAL_REFERENCE=<change-ticket-id>
APPROVAL_TIMESTAMP=<ISO-8601-timestamp>
ROOT_DIGEST=<SHA-256-from-independent-channel>
REASON=<written-change-reason>

# Protected audit location
TRUST_ROOT_AUDIT_PATH=/protected/audit/trust-root/
```

---

### 3. Enterprise Identity (OIDC/SAML)

| Attribute | Details |
|-----------|---------|
| **Feature Name** | Enterprise Identity and Least-Privilege Authorization |
| **Description** | Tenant-scoped authorization boundary consuming claims from trusted identity gateway |
| **Local Contract** | `orville_core.enterprise_identity`, tenant membership, scope grants, revocation state |
| **Why Production-Required** | Requires approved identity provider (OIDC/SAML gateway), live claim validation, MFA, group-to-scope mapping, and session revocation propagation |
| **Related Documents** | [`M14_ENTERPRISE_IDENTITY.md`](M14_ENTERPRISE_IDENTITY.md), [`M14_ENTERPRISE_ENVIRONMENT.md`](M14_ENTERPRISE_ENVIRONMENT.md) |

#### Local Contract Status
- ✅ Tenant membership persistence
- ✅ Scope grants (`read`, `plan`, `execute`, `approve`, `publish`, `member_management`, `integration_management`, `canary_deployment`, `trust_root_management`)
- ✅ Revocation state tracking
- ✅ Explicit approval references for sensitive actions
- ✅ 24-hour claim lifetime enforcement
- ✅ Tenant identifier validation (rejects path/control characters)
- ✅ Fail-closed for unknown actions and revoked memberships

#### Handoff Criteria for Deployment
| Criterion | Verification Method |
|-----------|---------------------|
| Approved OIDC/SAML identity provider configured | Review IdP configuration and approval documentation |
| Identity gateway signature verification enabled | Verify signature validation on incoming claims |
| Issuer/audience checks configured | Review claim validation rules |
| MFA enforcement enabled | Confirm MFA requirement in IdP policy |
| Group-to-scope mapping defined | Review group membership to Orville scope mapping |
| Session revocation propagation tested | Test revocation flow and propagation time |
| Key rotation procedure established | Document IdP signing key rotation process |
| Tenant isolation tests passed | Verify cross-tenant access is blocked |

#### Verification Checklist
- [ ] Claims from identity gateway are validated
- [ ] Tenant membership is verified for every authorization decision
- [ ] Actor identity is validated
- [ ] Claim lifetime is checked (24-hour bound)
- [ ] Action scope is verified against narrow vocabulary
- [ ] Deployment/publish/approval/trust-root actions require unexpired approval reference
- [ ] Revoked memberships fail closed
- [ ] Unknown actions fail closed
- [ ] Tenant identifiers reject path/control characters
- [ ] Audit events are sanitized (no secrets)

#### Required Credentials/Configuration
```bash
# Identity gateway configuration (deployment-owned)
OIDC_ISSUER_URL=https://identity.company.com
OIDC_AUDIENCE=orville-production
OIDC_JWKS_URL=https://identity.company.com/.well-known/jwks.json
SAML_IDP_METADATA_URL=https://identity.company.com/saml/metadata

# Orville enterprise configuration
ENTERPRISE_TENANT_ID=<approved-tenant-identifier>
ENTERPRISE_ENVIRONMENT_ID=<approved-environment-id>
```

---

### 4. Live Windows/Linux Sandbox Validation

| Attribute | Details |
|-----------|---------|
| **Feature Name** | Hardened Execution Infrastructure (Windows/Linux Sandbox) |
| **Description** | Approved execution substrate with non-root identity, bounded resources, controlled network, and durable audit |
| **Local Contract** | `orville_core.worker_execution`, deterministic adapter states, contract evidence |
| **Why Production-Required** | Requires live infrastructure with actual resource quotas, network policies, and host-level isolation |
| **Related Documents** | [`M9_HARDENED_EXECUTION_INFRASTRUCTURE_PROVISIONING_AND_ACCEPTANCE.md`](M9_HARDENED_EXECUTION_INFRASTRUCTURE_PROVISIONING_AND_ACCEPTANCE.md) |

#### Local Contract Status
- ✅ Worker execution contract definitions
- ✅ Deterministic adapter state implementations
- ✅ Resource quota validation logic
- ✅ Network policy validation
- ✅ Audit evidence formatting
- ✅ Acceptance test definitions (M9-01 through M9-18)

#### Handoff Criteria for Deployment
| Criterion | Verification Method |
|-----------|---------------------|
| Target provisioned (container/VM/managed runner) | Inspect target infrastructure |
| Non-root execution identity configured | Verify UID/account privileges |
| Resource quotas enforced (CPU, memory, storage) | Run controlled stress tests |
| Network default-deny policy applied | Probe unlisted destinations |
| Approved network allowlist configured | Verify required destinations succeed |
| Package immutability enforced | Attempt runtime package installation |
| Secret isolation verified | Scan logs/artifacts for credentials |
| Audit sink configured and accessible | Read back audit records |
| Health and restart recovery tested | Perform controlled restart |

#### Verification Checklist (M9-01 through M9-18)
- [ ] M9-01: Non-root identity verified
- [ ] M9-02: Filesystem boundary enforced
- [ ] M9-03: Capability reduction confirmed
- [ ] M9-04: CPU and memory quota bounded
- [ ] M9-05: Process and descriptor limits enforced
- [ ] M9-06: Storage quota bounded
- [ ] M9-07: Concurrency and queue bounds enforced
- [ ] M9-08: Network default-deny confirmed
- [ ] M9-09: Approved network allowlist verified
- [ ] M9-10: Package immutability confirmed
- [ ] M9-11: Secret isolation verified
- [ ] M9-12: Audit integrity confirmed
- [ ] M9-13: Restart recovery tested
- [ ] M9-14: Dependency timeout handled
- [ ] M9-15: Crash recovery tested
- [ ] M9-16: Patch/rebuild reproducibility confirmed
- [ ] M9-17: Access review completed
- [ ] M9-18: Termination and rollback verified

#### Required Credentials/Configuration
```bash
# Target specification
TARGET_ID=<stable-identifier>
TARGET_KIND=non-root-container|VM|managed-runner
HOST_OWNER=<named-owner-team>
RELEASE_REFERENCE=<commit-or-tag>
IMAGE_DIGEST=<immutable-digest>
RUNTIME_IDENTITY=<service-account>
REGION=<approved-region>

# Resource quotas
CPU_QUOTA=<value>
MEMORY_QUOTA=<value>
STORAGE_QUOTA=<value>
MAX_WORKER_CONCURRENCY=<value>

# Network policy
NETWORK_POLICY_REF=<allowlist-reference>
LOG_DESTINATION=<redacted-sink-id>
```

---

### 5. Production Canary/Rollback Drills

| Attribute | Details |
|-----------|---------|
| **Feature Name** | Production Canary Deployment and Rollback |
| **Description** | Policy-bound canary promotion with health-gated advancement and deterministic rollback |
| **Local Contract** | `orville_core.canary_controller`, `ReviewedDeploymentAdapter`, policy definitions |
| **Why Production-Required** | Requires live traffic, real health observations, and actual deployment mutations |
| **Related Documents** | [`M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md), [`M13_CANARY_CONTROLLER_ARCHITECTURE.md`](M13_CANARY_CONTROLLER_ARCHITECTURE.md), [`ROLLBACK_AND_RECOVERY_VERIFICATION.md`](ROLLBACK_AND_RECOVERY_VERIFICATION.md) |

#### Local Contract Status
- ✅ Canary controller with durable state
- ✅ Reviewed deployment adapter (dry-run by default)
- ✅ Policy-bound promotion (cohort sequence, hold periods, thresholds)
- ✅ Health observation integration
- ✅ Rollback decision logic
- ✅ Idempotency and duplicate-event handling
- ✅ Fault injection response

#### Handoff Criteria for Deployment
| Criterion | Verification Method |
|-----------|---------------------|
| Approved non-production environment available | Confirm environment isolation from production |
| Reviewed deployment adapter configured | Verify adapter backend and dry-run preflight |
| Known-good rollback target identified | Confirm rollback target passes health checks |
| Canary policy approved (version, cohorts, thresholds) | Review policy document and approval |
| Health sources configured and accessible | Verify monitoring platform integration |
| Controller persistence available | Confirm state storage and restart procedure |
| Named rollback authority assigned | Document escalation path |

#### Verification Checklist
- [ ] Clean bounded canary progression succeeds
- [ ] Controller restart during observation resumes same run
- [ ] Duplicate health events are idempotent
- [ ] Partial failure triggers policy pause/rollback
- [ ] Health threshold breach triggers rollback
- [ ] Security finding triggers rollback
- [ ] Rollback succeeds and restores known-good target
- [ ] Rollback failure enters explicit failed/paused state
- [ ] Evidence is redacted (no secrets, credentials, tokens)
- [ ] All scenarios have retained evidence

#### Required Credentials/Configuration
```bash
# Change control
CHANGE_REFERENCE=<approved-change-id>
ROLLBACK_AUTHORITY=<named-authority>
ENVIRONMENT_OWNER=<named-owner>

# Release targets
CANDIDATE_RELEASE=<immutable-reference>
ROLLBACK_TARGET=<immutable-reference>

# Policy configuration
POLICY_VERSION=<version>
COHORT_SEQUENCE=<comma-separated-percentages>
HOLD_PERIOD_MINUTES=<value>
MAX_TRAFFIC_PERCENT=<value>
MIN_SAMPLE_COUNT=<value>
FRESHNESS_BOUND_SECONDS=<value>
ERROR_THRESHOLD=<value>
LATENCY_THRESHOLD_MS=<value>
MAX_ROLLBACK_ATTEMPTS=<value>
```

---

### 6. Backup/Recovery Operations

| Attribute | Details |
|-----------|---------|
| **Feature Name** | Backup, Restore, and Disaster Recovery |
| **Description** | Encrypted off-host backups with retention controls, restore verification, and RTO/RPO evidence |
| **Local Contract** | `orville_core.recovery`, backup ledger, restore verification, rollback plan builder |
| **Why Production-Required** | Requires approved protected storage, encryption keys, and live restore exercises |
| **Related Documents** | [`M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md`](M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md), [`ROLLBACK_AND_RECOVERY_VERIFICATION.md`](ROLLBACK_AND_RECOVERY_VERIFICATION.md) |

#### Local Contract Status
- ✅ Backup ledger with idempotency keys
- ✅ Checksum verification (SHA-256)
- ✅ Restore verification (integrity, health, state, smoke)
- ✅ Rollback plan builder (stages 1, 2, 4, 5)
- ✅ Recovery verification record (non-secret)
- ✅ RTO/RPO validation

#### Handoff Criteria for Deployment
| Criterion | Verification Method |
|-----------|---------------------|
| Asset inventory with owners and classifications | Review inventory document |
| Approved protected storage target configured | Verify storage location and encryption |
| Encryption at-rest and in-transit enabled | Review encryption configuration |
| Retention controls configured | Verify retention policies and legal holds |
| RTO/RPO targets approved and measured | Compare drill measurements to targets |
| Access review completed | Review least-privilege access matrix |
| Recovery runbook approved | Document review and approval |

#### Verification Checklist
- [ ] Backup coverage includes all recoverable assets
- [ ] Backup operations are bounded and idempotent
- [ ] Backup ledger records IDs, timestamps, checksums, sizes, status
- [ ] Integrity verification confirms backup exists and matches checksum
- [ ] Restore drill passes integrity check
- [ ] Restore drill passes authenticated health check
- [ ] Restore drill passes read-only state/checkpoint check
- [ ] Restore drill passes smoke-workflow check
- [ ] RTO measurement meets target
- [ ] RPO measurement meets target
- [ ] Failure exercise proves escalation and preservation
- [ ] Access review confirms least privilege
- [ ] Recovery runbook is approved and tested

#### Required Credentials/Configuration
```bash
# Backup configuration
BACKUP_TARGET=<protected-storage-location>
ENCRYPTION_KEY_REF=<key-reference>
RETENTION_DAYS=<value>
BACKUP_SCHEDULE=<cron-expression>

# Recovery objectives
RTO_MINUTES=<target>
RPO_MINUTES=<target>

# Ownership
SYSTEM_OWNER=<name>
BACKUP_OPERATOR=<name>
RESTORATION_AUTHORITY=<name>
SECURITY_REVIEWER=<name>
INCIDENT_OWNER=<name>
```

---

## Cross-Reference: Related Runbooks

| Feature | Primary Runbook | Supporting Documents |
|---------|-----------------|---------------------|
| Live Provider Integrations | [`BLACKBOX_INTEGRATION.md`](BLACKBOX_INTEGRATION.md) | [`PROVIDER_SETUP_WORKFLOW.md`](PROVIDER_SETUP_WORKFLOW.md), [`PROVIDER_OPERATIONS_ENTERPRISE.md`](PROVIDER_OPERATIONS_ENTERPRISE.md) |
| Production Trust-Root Ceremony | [`M14_PRODUCTION_TRUST_ROOT_CEREMONY.md`](M14_PRODUCTION_TRUST_ROOT_CEREMONY.md) | [`M14_PROTECTED_SECRET_MANAGEMENT.md`](M14_PROTECTED_SECRET_MANAGEMENT.md) |
| Enterprise Identity | [`M14_ENTERPRISE_IDENTITY.md`](M14_ENTERPRISE_IDENTITY.md) | [`M14_ENTERPRISE_ENVIRONMENT.md`](M14_ENTERPRISE_ENVIRONMENT.md), [`LEAST_PRIVILEGE_PERMISSIONS.md`](LEAST_PRIVILEGE_PERMISSIONS.md) |
| Live Sandbox Validation | [`M9_HARDENED_EXECUTION_INFRASTRUCTURE_PROVISIONING_AND_ACCEPTANCE.md`](M9_HARDENED_EXECUTION_INFRASTRUCTURE_PROVISIONING_AND_ACCEPTANCE.md) | [`CLEAN_ENVIRONMENT_VALIDATION.md`](CLEAN_ENVIRONMENT_VALIDATION.md), [`M14_8_NONPRODUCTION_CHANGE_PACKAGE.md`](M14_8_NONPRODUCTION_CHANGE_PACKAGE.md) |
| Canary/Rollback Drills | [`M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md) | [`M13_CANARY_CONTROLLER_ARCHITECTURE.md`](M13_CANARY_CONTROLLER_ARCHITECTURE.md), [`M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md`](M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md) |
| Backup/Recovery | [`M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md`](M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md) | [`ROLLBACK_AND_RECOVERY_VERIFICATION.md`](ROLLBACK_AND_RECOVERY_VERIFICATION.md) |

---

## Summary: Local vs Deployment-Owned

| Aspect | Local (Implemented) | Deployment-Owned (Requires Production) |
|--------|---------------------|----------------------------------------|
| **Code** | Core modules, adapters, contracts | Provider backends, relay services |
| **Credentials** | Synthetic test values, mock providers | Live API keys, certificates, signing keys |
| **Infrastructure** | Local process, Docker Compose | Hosted VMs, containers, managed services |
| **Identity** | Test users, mock claims | OIDC/SAML gateways, MFA, group mapping |
| **Network** | Localhost, test networks | Production VPCs, firewalls, load balancers |
| **Observability** | Local logs, test assertions | Centralized logging, monitoring, alerting |
| **Procedures** | Unit tests, integration tests | Drills, exercises, operator approvals |

---

## Evidence Retention Requirements

All deployment-owned features require retained evidence that is:
- **Sanitized**: No credentials, bearer tokens, private keys, cookies, personal data
- **Verifiable**: Checksums, timestamps, decision records, approval references
- **Reviewable**: Accessible to independent verification reviewer
- **Bounded**: Time-limited retention with legal/operational hold capability

Store raw logs, credentials, and sensitive data only in approved protected systems—never in source control.

---

## Approval Gates

No deployment-owned feature may be marked complete without:
1. All handoff criteria verified
2. All verification checklist items passed
3. Independent reviewer sign-off
4. Sanitized evidence retained
5. Named owner and rollback authority assigned
6. Exception/disposition record for any incomplete items

---

*This matrix is a living document. Update when new deployment-owned features are identified or when handoff criteria change.*
