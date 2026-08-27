# Signal Room Expanded GUI Workflows

The Signal Room preview now covers the operational paths that were previously represented only as static mockup content.

| Workflow | Preview behavior | Safety boundary |
|---|---|---|
| File attachment | Uses a real multiple-file picker; validates a 5 MB per-file limit; submits text files through `POST /api/v1/artifacts/text` with a content-derived artifact identifier. | Binary files remain local metadata; filenames are sanitized; no credentials are collected or displayed. |
| Objective submission | Produces a review-only task payload containing the objective and artifact references. | It does not start a run; external effects remain approval-gated. |
| Contextual navigation | Run, file, artifact, project, and activity links use stable hash deep links and preserve the selected context rail. | Links are read-oriented and do not imply authorization or completion. |
| Live activity | Polls the authenticated run-event endpoint from the last monotonic sequence and prepends only newer events. | Offline state preserves the last timeline; event data is treated as untrusted display data. |
| Connector settings | Queries the workspace connector inventory and renders available/disabled states, with a local-only fallback. | The preview does not expose connector secrets or request sign-in credentials. |

## API alignment

The preview calls the existing artifact route `/api/v1/artifacts/text`, run-event route `/api/v1/runs/{run_id}/events`, and connector inventory route `/api/v1/connectors`. The optional `window.ORVILLE_API_BASE` value supports a hosted workspace; otherwise the preview uses same-origin relative paths. A token is read only from protected session state when one has already been supplied by the host; the UI never asks the user to paste a token.

## Responsive and packaging verification

At desktop widths, the layout presents navigation, primary content, and a contextual rail. At tablet widths, the rail collapses; at narrow widths, navigation wraps, tables scroll horizontally, and the objective composer stacks controls. Reduced-motion preferences disable smooth scrolling and transitions. The editable source is `docs/mockups/orville-control-center.html`; the packaged `webui/` output remains the existing release artifact. A Windows-native executable build requires a Windows runner and is not claimed from the Linux sandbox.

## References

[1]: ../docs/mockups/orville-control-center.html "Signal Room expanded preview source"
[2]: ../orville_core/api.py "Workspace API routes"
[3]: REALTIME_EXECUTION_EVENTS.md "Run event polling and resumable delivery contract"
[4]: ARTIFACT_BROWSER.md "Artifact safety and preview contract"
