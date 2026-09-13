# Orville Runs Walkthrough — Scene Order

**Purpose:** Demonstrate the implemented agentic code-completion lifecycle without implying unavailable production behavior.

## Scene sequence

| Scene | Focus | On-screen evidence | Truth boundary |
|---:|---|---|---|
| 1 | Intake | Signal Room opening screen and instruction-first composer | Show instructions, repository context, expected changes, and acceptance criteria. |
| 2 | Planning | Created run with `workflow_mode=agentic_code_completion` | Show the run identifier and task plan; do not claim a real provider unless configured. |
| 3 | Provider readiness | Provider/model and capability surfaces | Distinguish configured, unavailable, and blocked states. |
| 4 | Live code generation | Live viewer with status, task counts, elapsed time, and bounded event list | Use a recorded or fixture-backed run; label it as a local contract demonstration if no provider is active. |
| 5 | Verification | Verification review and acceptance criteria | Show pass, partial, and failure states with plain-text recovery guidance. |
| 6 | Approval gate | Approval-required action and explicit decision | Demonstrate that form submission, downloads, takeover, and side effects are not automatic. |
| 7 | Artifacts | Artifact list, metadata, checksums, and source citations | Show redacted references only; exclude credentials and sensitive payloads. |
| 8 | Failure | Offline, failed, blocked, and reconnect states | Show bounded error text and the next recovery action. |
| 9 | Repair | Retry, resume, checkpoint, and refresh controls | Explain that recovery is state-aware and audit-recorded. |
| 10 | Closeout | Final status, verification evidence, artifact references, and checkpoint | Separate locally verified evidence from deployment-owned gates. |

## Voiceover constraints

Use “the local Orville contract” or “the configured provider” only when the corresponding runtime is actually active. Do not state that production identity, live model generation, browser/device accessibility, deployment, rollback, or disaster recovery has passed unless those environments provide evidence.

## Reproducible evidence

The scene order maps to `windows_gui.py`, `orville_core/gui_state.py`, `orville_core/browser_approvals.py`, `orville_core/browser_evidence.py`, `orville_core/source_citations.py`, and `docs/PREVIEW_CHECKPOINT_2026-09-03.md`.
