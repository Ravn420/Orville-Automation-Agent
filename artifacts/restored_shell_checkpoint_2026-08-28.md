# Restored Orville Shell Checkpoint — 2026-08-28

## Scope

This checkpoint records the restored desktop shell work covering navigation, instruction-first intake, task history, projects, settings, personal-agent status, persistence projections, and preserved operational controls.

## Implementation

`windows_gui.py` now exposes a collapsible-sidebar information architecture with `New Task`, `Personal Agent`, `Projects`, `Task history`, `Overview`, `Active tasks`, `Verification`, `Artifacts`, `Integrations`, `Settings`, and the existing local-model controls. Project, thread-history, and agent views use bounded read projections from the authenticated local API. Settings continues to route through the existing provider/privacy configuration flow. The main screen remains instruction-first and preserves the existing objective composer, dashboard, context viewer, runs, artifacts, events, repository controls, and API documentation access.

The always-on boundary remains local and explicit: the personal-agent view describes isolated runtime status and project-scoped persistence; external side effects continue to require existing approval paths. No credentials or external services were used for this checkpoint.

## Verification

- `python -m py_compile windows_gui.py` — passed.
- Focused restored-shell, GUI, history, and persistence tests — **36 passed, 1 warning, 1 subtest passed**.
- The prior full-suite run on synchronized `main` recorded **822 passed, 1 failed, 1 skipped, 1 warning, 6 subtests passed**. The remaining failure is the pre-existing Windows path separator expectation in `tests/test_security_hardening.py::test_sandbox_plan_preserves_windows_absolute_paths_from_request`; it is unrelated to the shell changes.
- Working-tree review and API route inspection confirmed the project and thread history endpoints, agent runtime endpoint, provider/settings flow, and existing run/artifact/state/event routes remain available.

## Known limitations

Live visual inspection of a running Tk desktop window and end-to-end recovery against a populated local API were not performed in this checkpoint. The focused structural and behavioral tests pass. The Windows path separator failure remains a separate follow-up.

## Recovery

The pre-sync local work remains preserved in `stash@{0}`. This checkpoint is a source-controlled audit artifact and does not authorize deployment, publication, or external side effects.

