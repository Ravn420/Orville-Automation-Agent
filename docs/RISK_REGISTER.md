# Orville Risk Register

**Review date:** 2026-09-01
**Owner:** Orchestration Agent

| ID | Risk owner | Affected asset | Likelihood | Impact | Mitigation | Residual risk | Review date | Evidence |
|---|---|---|---|---|---|---|---|---|
| R-001 | Runtime owner | Approved isolation adapter | Medium | High | Require an approved adapter and fail closed when unavailable; disable network by default. | Repository evaluations remain blocked on hosts without isolation. | 2026-10-01 | `orville_core/repository_evaluation.py`, `tests/test_repository_evaluation.py` |
| R-002 | Release evidence owner | Walkthrough video retention | High | Medium | Retain source/checksum or obtain a documented waiver; do not claim archival completion. | Live artifact or waiver is still unavailable. | 2026-10-01 | `docs/WALKTHROUGH_VIDEO_ARCHIVAL_COMPLIANCE_NOTE.md` |
| R-003 | GUI owner | Accessibility validation | Medium | High | Use WCAG 2.2 contract, status-message safeguards, and a complete manual test protocol. | No executable GUI/device/screen-reader environment in recovered checkout. | 2026-10-01 | `docs/GUI_ACCESSIBILITY_TEST_PROTOCOL_2026-09-01.md` |
| R-004 | Security owner | Sensitive run evidence | Medium | High | Opt-in capture, role allowlist, recursive redaction, bounded payloads, and expiry metadata. | Misconfiguration could still reduce evidence availability; policy review required. | 2026-10-01 | `orville_core/sensitive_capture.py`, `tests/test_sensitive_capture.py` |
| R-005 | Operations owner | Persistent worker credentials | High | High | Keep credentials in mode-600 runtime configuration, never log them, and rotate credentials exposed in chat. | Worker cannot start after reset until a replacement credential is restored. | 2026-10-01 | `skills/orville-background-worker/SKILL.md`, worker launcher diagnostics |
