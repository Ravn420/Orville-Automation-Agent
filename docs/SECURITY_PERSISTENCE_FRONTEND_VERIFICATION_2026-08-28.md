# Security, Persistence, Shutdown, Run-Linkage, and Frontend Verification

**Roadmap item:** `TODO-e1bada1fe5df`  
**Verification date:** 2026-08-28  
**Scope:** Attached standalone Orville repository

## Result

The focused verification run produced **36 passing tests and one pre-existing failure**. The passing tests cover browser persistence and recovery, shutdown lifecycle, run/artifact linkage, security policy, GUI action wiring, frontend architecture boundaries, backend bridge behavior, expanded workflows, and GUI quality checks. The remaining failure is a Windows path-representation assertion in `tests/test_security_hardening.py`, where `SandboxPlan.from_request` currently returns `C:\\model` while the test expects `C:/model`. This is recorded as a baseline compatibility blocker and was not changed within this verification item.

## Verification matrix

| Area | Evidence | Result |
|---|---|---|
| Security | `tests/test_security_hardening.py` and related security contracts | Passed except the documented Windows path representation assertion |
| Browser/session persistence | `tests/test_browser_persistence.py`, `tests/test_browser_session_persistence_recovery.py` | Passed |
| Clean shutdown/recovery | `tests/test_browser_run_artifact_shutdown_audit.py` and lifecycle tests | Passed |
| Run linkage and artifacts | `tests/test_run_lifecycle_narrative.py`, artifact and checkpoint tests | Passed |
| Frontend/API wiring | `tests/test_gui_action_wiring.py`, `test_gui_architecture_boundaries.py`, `test_gui_backend_bridge.py`, `test_gui_expanded_workflows.py`, `test_gui_quality.py` | Passed |
| Python compilation | `python -m compileall -q orville_core windows_gui.py <selected tests>` | Passed |
| Patch integrity | `git diff --check` | Passed |

## Reproduction

From the repository root on Windows:

```powershell
$tests = @(
  'tests/test_security_hardening.py',
  'tests/test_browser_persistence.py',
  'tests/test_browser_session_persistence_recovery.py',
  'tests/test_browser_run_artifact_shutdown_audit.py',
  'tests/test_run_lifecycle_narrative.py',
  'tests/test_gui_action_wiring.py',
  'tests/test_gui_architecture_boundaries.py',
  'tests/test_gui_backend_bridge.py',
  'tests/test_gui_expanded_workflows.py',
  'tests/test_gui_quality.py'
)
python -m pytest $tests -q
python -m compileall -q orville_core windows_gui.py $tests
git diff --check
```

Observed test summary: `1 failed, 36 passed`. The failed assertion is `test_sandbox_plan_preserves_windows_absolute_paths_from_request`; it compares `str(plan.model_path)` with `C:/model` but receives `C:\model`.

## Limitations

This verification does not claim a production Windows executable launch, real external browser login, remote telemetry sink, or destructive deployment. The GUI checks are source-level and contract-level checks in the available host environment; packaging and clean-host execution remain separate acceptance gates.

## References

[1]: ../tests/test_security_hardening.py "Security hardening tests"

[2]: ../tests/test_browser_session_persistence_recovery.py "Browser session recovery tests"

[3]: ../tests/test_gui_action_wiring.py "GUI action wiring tests"
