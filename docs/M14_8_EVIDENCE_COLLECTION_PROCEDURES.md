# M14.8 Evidence Collection Procedures

**Milestone:** M14.8 — Non-production canary and rollback drill
**Status:** Local contract complete; live drill pending

## Purpose

This document defines the procedures for collecting, retaining, and verifying evidence during the M14.8 non-production canary and rollback drill. All evidence must be sanitized, access-controlled, and suitable for independent review.

## Evidence Classes

### 1. Change and Approval Evidence

**Description:** Records of approved changes, authorizations, and decisions

**Repository-Safe Content:**
- Change reference ID
- Scope and timing
- Approver roles and identities
- Approval timestamps
- Outcome status

**Protected System Location:**
- Change-management system
- Approval workflow platform

**Collection Procedure:**
1. Record change reference at drill start
2. Capture approval chain with timestamps
3. Document scope boundaries
4. Verify rollback authority designation

**Verification Checklist:**
- [ ] Change reference is valid and active
- [ ] All required approvals obtained
- [ ] Scope matches drill boundaries
- [ ] Rollback authority named and reachable

---

### 2. Release and Deployment Evidence

**Description:** Immutable release identifiers, deployment records, and adapter mutations

**Repository-Safe Content:**
- Release ID (candidate and rollback target)
- Immutable digest/reference
- Adapter version
- Cohort assignments
- Traffic percentages
- Deployment status

**Protected System Location:**
- Deployment system audit trail
- Container registry
- Artifact repository

**Collection Procedure:**
1. Record candidate release_id and immutable reference
2. Record rollback_target release_id and immutable reference
3. Capture adapter version and configuration
4. Log all adapter mutations (deploy, set_traffic, pause, rollback)
5. Verify traffic percentages match cohort policy

**Verification Checklist:**
- [ ] Release identifiers are immutable
- [ ] Rollback target is known-good
- [ ] Adapter mutations match controller decisions
- [ ] Traffic percentages are correctly applied

---

### 3. Health and Security Evidence

**Description:** Health observations, threshold evaluations, and security findings

**Repository-Safe Content:**
- Aggregated metrics (error rate, latency percentiles, saturation)
- Sample counts and observation windows
- Decision inputs and outcomes
- Freshness timestamps
- Redacted security finding types (no details)

**Protected System Location:**
- Monitoring platform
- Security scanning system
- Health observation store

**Collection Procedure:**
1. Capture health observations with timestamps
2. Record policy thresholds applied
3. Document decision reasons (if failed)
4. Verify observation scoping (tenant/cohort/release)
5. Redact security finding details (retain count only)

**Verification Checklist:**
- [ ] Observations are fresh (within window)
- [ ] Sample counts meet minimum requirements
- [ ] Metrics are properly scoped
- [ ] Security findings are redacted
- [ ] Decision trail is complete

---

### 4. Controller and Audit Evidence

**Description:** Controller state, state transitions, and audit events

**Repository-Safe Content:**
- Run ID and policy ID
- State transition timeline
- Decision cursor and cohort index
- Idempotency context
- Event identifiers and outcomes
- Timestamps

**Protected System Location:**
- Controller SQLite database
- Audit event store

**Collection Procedure:**
1. Export canary_runs table (sanitized)
2. Export canary_audit table (redacted)
3. Capture state before and after each scenario
4. Record decision identifiers
5. Verify audit sequence continuity

**Verification Checklist:**
- [ ] Run ID is consistent across scenarios
- [ ] State transitions follow valid paths
- [ ] Audit events are sequential
- [ ] No duplicate events without idempotency
- [ ] Secrets are redacted from audit

---

### 5. Logs and Incident Evidence

**Description:** Diagnostic logs, error records, and incident references

**Repository-Safe Content:**
- Log checksums or hashes
- Incident reference IDs
- Error types (no stack traces with secrets)
- Sanitized excerpts

**Protected System Location:**
- Access-controlled logging system
- Incident management platform

**Collection Procedure:**
1. Compute checksums of log files
2. Record incident reference IDs
3. Extract sanitized error excerpts
4. Verify no secrets in retained excerpts

**Verification Checklist:**
- [ ] Log checksums are recorded
- [ ] Incident references are valid
- [ ] Excerpts contain no credentials
- [ ] Full logs are in protected system

---

### 6. Secrets and Identity Evidence

**Description:** Credential references, identity assertions, and access records

**Repository-Safe Content:**
- Credential reference names (not values)
- Role names and assignments
- Identity provider references
- Access scope descriptions

**Protected System Location:**
- Secret management system
- Identity provider
- Access control system

**Collection Procedure:**
1. Record credential reference names only
2. Document role assignments
3. Verify identity provider configuration
4. Confirm access scope boundaries

**Verification Checklist:**
- [ ] No credential values in repository
- [ ] Role assignments are documented
- [ ] Access scopes are defined
- [ ] Secret references are valid

## Evidence Collection Workflow

### Pre-Drill Collection

```
┌─────────────────┐
│  Entry Gates    │
│  Verification   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Record Baseline │────▶│ Capture Pre-Drill│
│   State         │     │   Health/State   │
└─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Verify Rollback │
│   Target Health │
└─────────────────┘
```

### Per-Scenario Collection

```
┌─────────────────┐
│ Scenario Start  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Capture Before  │────▶│ Execute Scenario│
│   State         │     │                 │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Capture After   │
                        │   State         │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Record Adapter  │
                        │   Mutations     │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Verify State    │
                        │   Transition    │
                        └─────────────────┘
```

### Post-Drill Collection

```
┌─────────────────┐
│ Redaction Review│
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Evidence Index  │────▶│ Signature       │
│   Compilation   │     │   Collection    │
└─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Acceptance      │
│   Record        │
└─────────────────┘
```

## Redaction Requirements

### Automatic Redaction (Controller-Level)

The following keys are automatically redacted from audit metadata:

| Key | Example Value | Redacted To |
|-----|---------------|-------------|
| `token` | `Bearer abc123...` | `[REDACTED]` |
| `api_key` | `sk-abc123...` | `[REDACTED]` |
| `authorization` | `Basic abc123...` | `[REDACTED]` |
| `secret` | `my-secret-value` | `[REDACTED]` |
| `password` | `my-password` | `[REDACTED]` |

### Manual Redaction Review

Before evidence retention:

1. **Credential Scan**: Search for patterns matching:
   - API keys (e.g., `sk-`, `ak-`, `Bearer`)
   - Connection strings with passwords
   - Private key blocks
   - JWT tokens

2. **Personal Data Scan**: Remove or anonymize:
   - Email addresses
   - User IDs (replace with hashes)
   - IP addresses
   - Hostnames (if sensitive)

3. **Provider Response Redaction**: Sanitize:
   - Raw HTTP responses
   - Internal error details
   - Stack traces with paths

### Redaction Verification Checklist

- [ ] No credentials in audit events
- [ ] No bearer tokens in state
- [ ] No cookies in logs
- [ ] No private keys in evidence
- [ ] No personal data retained
- [ ] No raw provider responses

## Evidence Storage

### Repository-Safe Storage

**Location:** `artifacts/` directory in repository

**Permitted Content:**
- Sanitized JSON evidence files
- Checksums and hashes
- Reference IDs
- Structured decision records
- Redacted audit excerpts

**Format:**
```json
{
  "schema": "orville.m14.8.evidence",
  "drill_id": "M14.8-DRILL-20261016-001",
  "collected_at": "2026-10-16T07:49:59Z",
  "evidence_class": "controller_audit",
  "content": {
    "run_id": "abc123...",
    "state_transitions": [...],
    "audit_events": [...]
  },
  "checksum": "sha256:..."
}
```

### Protected System Storage

**Location:** Environment's protected logging and retention system

**Content:**
- Raw logs
- Full audit trails
- Credential references
- Provider responses
- Personal data (if required)

**Access Control:**
- Role-based access
- Audit logging of access
- Encryption at rest
- Retention policy enforcement

## Evidence Verification

### Independent Review Process

1. **Reviewer Assignment**: Independent verification reviewer
2. **Evidence Receipt**: All evidence classes provided
3. **Completeness Check**: All scenarios covered
4. **Consistency Check**: State, audit, and adapter records agree
5. **Redaction Check**: No secrets in repository evidence
6. **Acceptance Decision**: Pass, conditional, or fail

### Verification Checklist

| Evidence Class | Completeness | Consistency | Redaction |
|----------------|--------------|-------------|-----------|
| Change/Approval | ☐ | ☐ | ☐ |
| Release/Deployment | ☐ | ☐ | ☐ |
| Health/Security | ☐ | ☐ | ☐ |
| Controller/Audit | ☐ | ☐ | ☐ |
| Logs/Incident | ☐ | ☐ | ☐ |
| Secrets/Identity | ☐ | ☐ | ☐ |

## Evidence Retention Schedule

| Evidence Type | Repository | Protected System | Retention Period |
|---------------|------------|------------------|------------------|
| Drill evidence | 7 years | 7 years | Per compliance |
| Audit events | 7 years | 7 years | Per compliance |
| Logs | Checksums only | 90 days | Operational |
| Credentials | Reference only | Per secret policy | Secret policy |
| Incident records | Reference only | 7 years | Per compliance |

## M14.8 Evidence Template

Use the template at:
[`artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md`](../artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md)

### Template Sections

1. **Entry Gates Verification** — 10 required gates
2. **Synthetic Fault Injection Baseline** — 18 scenarios
3. **Live Drill Evidence** — 5 scenario categories
4. **Evidence Retention Checklist** — 6 evidence classes
5. **Redaction Verification** — 6 security checks
6. **Signatures** — 5 required roles
7. **Completion Statement** — Result classification

## Related Documentation

- [`M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md) — Drill procedure
- [`M14_8_CANARY_CONTROLLER_OPERATION_GUIDE.md`](M14_8_CANARY_CONTROLLER_OPERATION_GUIDE.md) — Controller operations
- [`M14_8_HEALTH_EVALUATION_PROCEDURES.md`](M14_8_HEALTH_EVALUATION_PROCEDURES.md) — Health evaluation
- [`M14_8_ROLLBACK_DECISION_MATRIX.md`](M14_8_ROLLBACK_DECISION_MATRIX.md) — Rollback decisions
