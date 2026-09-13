# Signal Room Walkthrough — Visual References and Overlays

## Canonical visual references

| Reference | Use in walkthrough | Source |
|---|---|---|
| Control center | Establish workspace navigation and system status | `docs/mockups/orville-control-center.html` |
| Task composer | Intake and acceptance-criteria scene | `docs/mockups/task-composer.html`, `windows_gui.py` |
| Generation workspace | Planning and live-code scene | `docs/mockups/generation-workspace.html`, `windows_gui.py` |
| Model configuration | Provider readiness scene | `docs/mockups/model-configuration.html` |
| Artifact browser | Artifact and citation scene | `docs/mockups/artifact-browser.html` |
| Help and recovery | Failure, reconnect, and repair scene | `docs/mockups/help-recovery.html` |
| Settings workspace | Integration and deployment-boundary scene | `docs/mockups/settings-workspace.html` |

## Overlay inventory

1. **INTAKE** — “Describe the task, repository context, expected changes, and acceptance criteria.”
2. **PLAN** — “The run receives an identifier and an agentic workflow mode.”
3. **PROVIDER READINESS** — “Configured, unavailable, and blocked states are shown explicitly.”
4. **LIVE CODE** — “Status, tasks, elapsed time, and the latest bounded events.”
5. **VERIFY** — “Review acceptance criteria and verification evidence.”
6. **APPROVAL REQUIRED** — “External side effects require an explicit approval flow.”
7. **ARTIFACTS** — “Artifacts retain metadata, checksums, and redacted source citations.”
8. **FAILURE / OFFLINE** — “Failures provide bounded plain-text recovery guidance.”
9. **REPAIR** — “Retry, resume, checkpoint, and refresh are state-aware controls.”
10. **CLOSEOUT** — “Separate local contract evidence from production-environment gates.”

## Visual safety rules

Use the existing design system and mockups as references. Do not display API tokens, cookies, bearer headers, raw browser handles, unredacted tool arguments, or private source payloads. Every simulated or fixture-backed run must be labeled as a local contract demonstration when no real provider is active. Overlays must remain readable at the documented high-zoom and small-screen breakpoints.

## Asset status

The repository contains HTML mockups and a deterministic visual regression baseline. No walkthrough video source or final rendered video is present in the recovered checkout; video generation and review remain separate tasks.
