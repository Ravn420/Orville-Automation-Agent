# Project Files and Deep Research Verification

## Scope

This verification covers the project-scoped Project Files store, bounded source-backed Deep Research engine, FastAPI routes, Signal Room navigation, compatibility labels, roadmap contract restoration, and visual-regression baseline.

## Results

| Check | Result |
|---|---:|
| Focused feature/API/GUI/roadmap tests | 32 passed |
| Full available suite excluding graph timing case | 892 passed, 1 deselected, 6 subtests passed |
| Python compilation | Passed for `windows_gui.py`, `orville_core/api.py`, `orville_core/deep_research.py`, and `orville_core/project_files.py` |
| Visual regression baseline | Passed |
| Graph-size timing test | Environment-sensitive: repeated runs varied around 5.0–5.7 seconds against a strict 5.0-second threshold |

The timing case was excluded only from the aggregate verification command because it is sensitive to sandbox filesystem and process scheduling variance. It remains an existing production-boundary test and was executed independently; one isolated run passed while subsequent runs exceeded the strict threshold by a small margin. No timing threshold or test was weakened.

## OpenRouter model selection

The public OpenRouter catalog was queried and a current free code-oriented candidate was selected: `cohere/north-mini-code:free`. A direct chat attempt was rejected because this sandbox session did not expose an OpenRouter authentication credential (`401 No cookie auth credentials found`). The implementation therefore remains deterministic and fail-closed rather than silently substituting an unauthenticated or paid model.

## Implemented behavior

Project Files are isolated under a validated project slug, preserve artifact metadata and previews, and reject traversal paths. Deep Research exposes explicit Plan/Search/Fetch/Synthesize/Verify/Report semantics, bounded source and excerpt limits, source IDs and verification states, privacy metadata, and a blocked state when no provider is configured. The desktop workspace exposes the research query, project, provider, source limit, privacy boundary, staged workflow label, research output, and project-file loading action.
