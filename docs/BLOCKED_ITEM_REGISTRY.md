# Orville Blocked Item Registry

**Registry ID:** `orville-blocked-items-2026-10-16`  
**Last Updated:** 2026-10-16  
**Owner:** Orchestration Agent  
**Status:** Active — 9 blocked/pending items documented

---

## Overview

This registry documents all externally-blocked items in the Orville project that prevent 100% completion status. Each entry identifies the specific external dependency, impact assessment, alternative approaches, and unblock criteria.

### Summary Statistics

| Category | Count |
|----------|-------|
| Blocked by Infrastructure | 3 |
| Blocked by Provider | 2 |
| Blocked by Credentials/Provider | 1 |
| Blocked External | 1 |
| Partially Complete (Pending External) | 4 |
| **Total** | **11** |

---

## Blocked Items

### M9: Hardened Execution Infrastructure

| Field | Value |
|-------|-------|
| **Item ID** | M9 |
| **Name** | Hardened execution infrastructure |
| **Status** | `blocked-by-infrastructure` |
| **Owner** | Automation Agent and Security Agent |
| **Last Checked** | 2026-08-27 |

#### External Dependency Required
- Approved non-root container/VM environment with:
  - CPU, memory, disk, and process quotas
  - Network egress controls
  - Filesystem isolation policies
  - Package source restrictions

#### Impact Assessment
**What cannot be done without it:**
- Production-grade sandboxed execution of untrusted code
- Resource-constrained model worker isolation
- Network-restricted execution environments
- Multi-tenant execution boundaries

**Current Limitation:**
Local sandbox adapters exist (Windows Sandbox, bubblewrap) but live runtime enforcement on approved production hosts remains unavailable.

#### Alternative Approaches Considered
| Approach | Status | Limitation |
|----------|--------|------------|
| Windows Sandbox adapter | Completed-local | Host-dependent; production hosts lack Windows Sandbox binaries |
| Linux bubblewrap adapter | Completed-local-contract | Live runtime execution remains host-dependent |
| Synthetic deployment adapter | Completed-local-contract | Mock only; no real isolation guarantees |

#### Unblock Criteria
1. [ ] Select approved execution host with container/VM support
2. [ ] Define and deploy fail-closed resource/network/filesystem policies
3. [ ] Run isolation and negative-boundary validation tests
4. [ ] Obtain monitoring evidence and independent review
5. [ ] Document approved environment record and policy reference

#### Local Fallbacks Available
- `sandbox_adapters.py` — Windows/Linux adapter contracts
- `sandbox.py` — Canonical JSON-lines protocol
- `worker_protocol.py` — Guest communication boundary
- `model_worker.py` — Worker lifecycle management
- `local_execution.py` — Local execution controls

---

### M10: Browser Operator and Live Preview

| Field | Value |
|-------|-------|
| **Item ID** | M10 |
| **Name** | Browser operator and live preview |
| **Status** | `blocked-by-provider` |
| **Owner** | Prototype Agent |
| **Last Checked** | 2026-08-27 |

#### External Dependency Required
- Supported browser runtime with:
  - Screenshot/DOM instrumentation capabilities
  - Login handoff controls
  - Session isolation
  - Domain allowlist configuration
  - Privacy-preserving audit trails

#### Impact Assessment
**What cannot be done without it:**
- Live browser-based preview workflows
- DOM-aware visual testing
- Automated browser interaction for testing
- Screenshot-based visual regression testing
- Login-handoff for authenticated previews

**Current Limitation:**
Local preview runtime exists but requires browser provider for full functionality.

#### Alternative Approaches Considered
| Approach | Status | Limitation |
|----------|--------|------------|
| Local preview runtime | Completed-local | No live browser instrumentation |
| Deterministic style patches | Completed-contract | Static only; no runtime DOM |
| Smoke reports | Completed-contract | Limited to static analysis |

#### Unblock Criteria
1. [ ] Select/configure supported browser operator
2. [ ] Define user takeover and approval controls
3. [ ] Establish domain allowlist and session isolation
4. [ ] Configure screenshot/DOM privacy controls
5. [ ] Validate safe read-only workflows
6. [ ] Obtain adapter health/capability record
7. [ ] Complete privacy/security review

#### Local Fallbacks Available
- `preview_runtime.py` — Local preview without browser
- `preview.py` — Preview generation (static)
- `handoff.py` — Handoff conflict detection
- `readiness.py` — Readiness checking
- `telemetry.py` — Telemetry collection

---

### M11: GitHub/GitLab Synchronization and Deployment

| Field | Value |
|-------|-------|
| **Item ID** | M11 |
| **Name** | GitHub/GitLab synchronization and deployment |
| **Status** | `blocked-by-credentials/provider` |
| **Owner** | IDE Agent and Deployment Agent |
| **Last Checked** | 2026-08-27 |

#### External Dependency Required
- Configured credentials for target repository
- Remote repository access
- Selected deployment provider
- Release approval authority
- Protected credential/workload-identity boundary

#### Impact Assessment
**What cannot be done without it:**
- Automated repository synchronization
- Continuous deployment pipelines
- Release automation
- Production deployment from CI/CD
- Git-based workflow integration

**Current Limitation:**
Source-control integration is available in present context; deployment provider remains unselected/unauthorized.

#### Alternative Approaches Considered
| Approach | Status | Limitation |
|----------|--------|------------|
| Split source-control and deployment | Proposed | Requires explicit provider selection |
| Local release gates | Completed-local | No remote deployment capability |
| Manual deployment | Available | Not automated; requires human intervention |

#### Unblock Criteria
1. [ ] Split work into source-control and deployment-provider scopes
2. [ ] Select target deployment provider
3. [ ] Establish protected credential/workload-identity boundary
4. [ ] Define deployment environment and rollback target
5. [ ] Configure monitoring and change approval
6. [ ] Complete provider-specific preflight/dry-run
7. [ ] Obtain authorization evidence and release approval

#### Local Fallbacks Available
- `tools/release_gate.py` — Local release validation
- `docs/RELEASE_GATES.md` — Release gate documentation
- `docs/DELIVERY_RUNBOOK.md` — Deployment procedures
- `orville_core/canary.py` — Canary controller (synthetic only)

---

### M12.18: Blackbox Developer Support Confirmation

| Field | Value |
|-------|-------|
| **Item ID** | M12.18 |
| **Name** | Blackbox developer-support confirmation assessment |
| **Status** | `blocked-external` |
| **Owner** | Research Agent and Governance Agent |
| **Last Checked** | 2026-08-27 |

#### External Dependency Required
- Official Blackbox developer-support response confirming:
  - Supported OAuth 2.0/device-authorization flow (if any)
  - API-key-only authentication boundaries
  - Relay service permissions and requirements
  - Data handling and retention policies
  - Production integration terms

#### Impact Assessment
**What cannot be done without it:**
- Implementation of OAuth/device flow for Blackbox
- Confirmation of server-side relay architecture compliance
- Production authorization for Blackbox integration
- Closure of provider access mode uncertainty

**Current Limitation:**
Public documentation insufficient; official provider confirmation required.

#### Alternative Approaches Considered
| Approach | Status | Limitation |
|----------|--------|------------|
| API-key-only/managed-first | Completed-local | Safe fallback; no OAuth capability |
| Support request submission | Pending approval | Requires explicit authorization to send |
| Community documentation | Rejected | Not authoritative |

#### Unblock Criteria
1. [ ] Obtain explicit source-owner approval for external outreach
2. [ ] Verify official support channel/destination
3. [ ] Submit narrowly scoped provider support request
4. [ ] Receive official provider response
5. [ ] Build claim matrix mapping answers to questions
6. [ ] Complete independent review against repository contract
7. [ ] Record decision with evidence reference

#### Evidence Requirements
- M12.18-E01: Source-owner approval (approver, timestamp, scope)
- M12.18-E02: Destination validation (official channel URL)
- M12.18-E03: Sent-request receipt (case ID, timestamp, hash)
- M12.18-E04: Provider response (response ID, redacted copy)
- M12.18-E05: Claim matrix (questions, answers, confidence)
- M12.18-E06: Independent review (reviewer, discrepancies)
- M12.18-E07: Decision record (decision, owner, follow-up)

#### Local Fallbacks Available
- `cloud_relay.py` — Managed relay with API-key
- `blackbox_contract.py` — API contract validation
- `blackbox_capabilities.py` — Capability negotiation
- `cloud_onboarding.py` — Managed-first onboarding
- `docs/BLACKBOX_INTEGRATION.md` — Current access modes
- `docs/BLACKBOX_INTEGRATION_RESEARCH.md` — Research record

---

## Partially Complete Items (Pending External Resources)

### M12.8: Process Sandboxing and Cryptographic Attestation

| Field | Value |
|-------|-------|
| **Item ID** | M12.8 |
| **Name** | Process sandboxing and cryptographic attestation verification |
| **Status** | `partially-complete-local` |
| **Owner** | Security Agent and Verification Agent |
| **Last Checked** | 2026-08-27 |

#### Completed Locally
- Fallback controls and repository-chain TUF verification
- Trust-store controls and Cosign/in-toto handling
- Fail-closed integration and negative tests
- Activation evidence persistence
- GUI attestation policy/status presentation
- Windows Sandbox host-folder mapping
- Automatic `LogonCommand` execution

#### Pending External
| Component | Dependency | Unblock Criteria |
|-----------|------------|------------------|
| Production trust-root ceremony | Live operator approval, production root material | M14.2 completion |
| Linux live execution | Linux host with bwrap runtime | M14.3 completion |
| GPU isolation | GPU-capable sandbox environment | Infrastructure approval |

#### Local Fallbacks Available
- `sandbox.py`, `sandbox_adapters.py` — Sandbox implementation
- `attestations.py`, `attestation_service.py` — Attestation services
- `tuf_metadata.py` — TUF metadata handling
- `tools/tuf_root_ceremony.py` — Ceremony tooling
- `config/tuf-trust-root.example.json` — Example configuration

---

### M13.4: Sandbox Execution Integration

| Field | Value |
|-------|-------|
| **Item ID** | M13.4 |
| **Name** | Sandbox execution integration |
| **Status** | `partially-complete-local` |
| **Owner** | Code Synthesis Agent / IDE Agent |
| **Last Checked** | 2026-08-27 |

#### Completed Locally
- Canonical JSON-lines protocol
- Active-attestation/checksum execution boundary
- Windows guest-marker verification

#### Pending External
| Component | Dependency | Unblock Criteria |
|-----------|------------|------------------|
| Production-path routing | Approved production environment | M14.1 completion |
| Automated guest completion evidence | Live sandbox execution | M14.3 completion |
| Linux live IPC | Linux host with bwrap | M13.3 live execution |

#### Local Fallbacks Available
- `sandbox.py`, `sandbox_adapters.py` — Sandbox adapters
- `worker_protocol.py` — Worker protocol
- `model_worker.py` — Model worker
- `local_execution.py` — Local execution
- `local_models.py` — Local model integration

---

### M14.2: Production Trust-Root Ceremony

| Field | Value |
|-------|-------|
| **Item ID** | M14.2 |
| **Name** | Production trust-root ceremony |
| **Status** | `partially-complete-local` |
| **Owner** | Security Agent |
| **Last Checked** | 2026-08-27 |

#### Completed Locally
- `orville_core/trust_root_ceremony.py` — Ceremony implementation
- `config/production-trust-root-ceremony.example.json` — Example config
- `docs/M14_PRODUCTION_TRUST_ROOT_CEREMONY.md` — Documentation
- 3 focused tests passing

#### Pending External
| Component | Dependency | Unblock Criteria |
|-----------|------------|------------------|
| Live operator approval | Named ceremony operators | M14.1 operator assignment |
| Production root material | HSM or air-gapped key generation | Hardware procurement |
| Rotation/revocation drill | Approved test environment | M14.8 non-production drill |

#### Local Fallbacks Available
- `tools/tuf_root_ceremony.py` — Local ceremony tooling
- `config/tuf-trust-root.example.json` — Development trust root
- `attestation_service.py` — Local attestation services

---

### M14.3: Live Windows/Linux Sandbox Validation

| Field | Value |
|-------|-------|
| **Item ID** | M14.3 |
| **Name** | Live Windows/Linux sandbox validation |
| **Status** | `partially-complete-local` |
| **Owner** | Security / Verification Agents |
| **Last Checked** | 2026-08-27 |

#### Completed Locally
- Targeted security and sandbox tests (15 tests passing)
- `artifacts/m14_3_sandbox_validation_2026-08-27.md` — Validation record

#### Pending External
| Component | Dependency | Unblock Criteria |
|-----------|------------|------------------|
| Windows Sandbox live execution | Windows host with Sandbox enabled | Infrastructure approval |
| WSL binary availability | WSL-enabled Windows host | Infrastructure approval |
| Linux bwrap execution | Linux host with bubblewrap | Infrastructure approval |
| Worker IPC validation | Live sandbox environment | M13.2/M13.3 live execution |
| GPU isolation validation | GPU-capable sandbox | Infrastructure approval |

#### Blocker
Windows Sandbox/WSL binaries and Linux `bwrap` are unavailable on approved hosts.

#### Local Fallbacks Available
- `sandbox_adapters.py` — Adapter contracts (fail-closed)
- `tests/test_security_hardening.py` — Security tests
- `tests/test_m12_8_m13_8.py` — Combined tests

---

### M14.4: Enterprise Identity and Authorization

| Field | Value |
|-------|-------|
| **Item ID** | M14.4 |
| **Name** | Enterprise identity and authorization |
| **Status** | `partially-complete-local` |
| **Owner** | Security / IDE Agents |
| **Last Checked** | 2026-08-27 |

#### Completed Locally
- `orville_core/enterprise_identity.py` — Identity implementation
- `tests/test_enterprise_identity.py` — Identity tests
- `docs/M14_ENTERPRISE_IDENTITY.md` — Documentation
- Tenant-scoped scopes, approvals, revocation
- Bounded claims and audit

#### Pending External
| Component | Dependency | Unblock Criteria |
|-----------|------------|------------------|
| Live OIDC/SAML | Identity provider configuration | M14.1 environment provisioning |
| MFA integration | MFA provider | Identity provider setup |
| Issuer/audience verification | Production identity issuer | M14.1 completion |
| Revocation propagation | Real-time revocation service | Identity provider capability |

#### Local Fallbacks Available
- Local identity contracts and tests
- Tenant-scoped authorization logic
- Audit event generation

---

## Dependency-Gated Production Items

These items are not labeled `blocked` but are unavailable for execution until dependency gates pass.

| ID | Status | Gate Preventing Execution | Required Next Action |
|----|--------|---------------------------|----------------------|
| M13.15 | `infrastructure-dependent` | M13 security/canary foundation, enterprise credentials, reviewed provider, non-production rollback proof | Do not integrate until M14 readiness evidence exists |
| M14.8 | `in-progress-local` | Approved target, live M14.2–M14.7 evidence, bounded policy, health sources, rollback target | Complete change package; run non-production drill |
| M14.9 | `planned` | M14.1/M14.4 controls, accepted M14.8 evidence | Establish encrypted backup and restore evidence |
| M14.10 | `planned` | M14.3, M14.8, M14.9 evidence | Run integrated security, load, soak, rollback gates |
| M14.11 | `infrastructure-dependent` | M14.1–M14.10 completion, explicit approval | Start smallest approved production cohort |

---

## Resolution Sequencing

The safe order to resolve blocked items:

1. **Environment and Authority Prerequisites** (M14.1, M14.2, M14.4)
   - Identify approved non-production environment
   - Assign owners, change route, identity boundary
   - Establish monitoring and rollback authority

2. **Live Evidence Gaps** (M14.3, M14.2 completion)
   - Complete live trust-root ceremony
   - Execute live sandbox validation
   - Verify identity provider integration

3. **Non-Production Drill** (M14.8)
   - Execute canary and rollback drill
   - Obtain independent acceptance evidence

4. **Backup/Restore Controls** (M14.9)
   - Run backup and disaster recovery operations
   - Validate restore procedures

5. **Integrated Readiness Gates** (M14.10)
   - Security, load, soak, observability validation

6. **Production Integration** (M13.15, M14.11)
   - Last step: real deployment-provider or production traffic decisions

**Parallel Work:**
- M9 may proceed in parallel with target-environment preparation
- M10 and M12.18 remain independent of production-readiness sequence
- M12.18 should not delay API-key-only workflows

---

## Recommendations for Resolution

### Immediate Actions (No External Dependencies)

1. **M12.18 External Request Approval**
   - Decision needed: Authorize Blackbox support request submission
   - Risk: Low — request contains no secrets or private data
   - Timeline: Can proceed immediately upon approval

2. **M14.8 Non-Production Drill Preparation**
   - Complete prepared change package
   - Identify approved non-production target
   - Schedule independent verification

### Short-Term Actions (Requires Infrastructure Selection)

3. **M9 Infrastructure Selection**
   - Evaluate container/VM options
   - Define resource and network policies
   - Obtain infrastructure approval

4. **M14.3 Live Sandbox Hosts**
   - Provision Windows Sandbox-enabled host
   - Provision Linux host with bubblewrap
   - Schedule validation runs

### Medium-Term Actions (Requires Provider Engagement)

5. **M10 Browser Provider Selection**
   - Evaluate browser operator options
   - Define privacy and security controls
   - Complete capability validation

6. **M11 Deployment Provider Selection**
   - Split source-control from deployment
   - Select and authorize deployment provider
   - Establish credential boundaries

### Long-Term Actions (Production Readiness)

7. **M14.2 Trust-Root Ceremony**
   - Assign ceremony operators
   - Procure HSM or air-gapped key generation
   - Schedule ceremony execution

8. **M14.4 Identity Provider Integration**
   - Configure OIDC/SAML provider
   - Enable MFA
   - Test revocation propagation

---

## Evidence Retention

For each resolved blocker, retain:

1. **Repository-safe evidence summary** in `artifacts/`
2. **Protected-system evidence reference** for sensitive operational material
3. **Updated tracker records** in `TODO.md`, `STATE.md`, `TASK_GRAPH.md`

---

## References

- [`TASK_GRAPH.md`](../TASK_GRAPH.md) — Current task graph with all milestones
- [`STATE.md`](../STATE.md) — Current project state
- [`docs/BLOCKED_TASK_RESOLUTION_GUIDE_2026-08-27.md`](BLOCKED_TASK_RESOLUTION_GUIDE_2026-08-27.md) — Resolution procedures
- [`docs/M12_18_BLACKBOX_DEVELOPER_SUPPORT_REQUEST_AND_VERIFICATION.md`](M12_18_BLACKBOX_DEVELOPER_SUPPORT_REQUEST_AND_VERIFICATION.md) — M12.18 request plan
- [`docs/M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md) — M14.8 runbook
- [`docs/M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md`](M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md) — M14.9 execution plan
- [`docs/M9_HARDENED_EXECUTION_INFRASTRUCTURE_PROVISIONING_AND_ACCEPTANCE.md`](M9_HARDENED_EXECUTION_INFRASTRUCTURE_PROVISIONING_AND_ACCEPTANCE.md) — M9 provisioning guide

---

*Last updated: 2026-10-16 by Documentation Agent*
