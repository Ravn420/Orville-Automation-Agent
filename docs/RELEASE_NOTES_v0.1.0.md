# Orville Core v0.1.0 Release Notes

**Release date:** 2026-08-27
**Release candidate tag:** `v0.1.0`
**Package version:** `0.1.0`


## Release summary

Orville Core v0.1.0 packages the repository’s task-graph orchestration engine, authenticated local API, local Browser Operator relay, provider adapters, durable checkpointing, and desktop control-center support. This release consolidates the recent portability, reliability, visual-regression, and error-contract repairs and is backed by a passing full integration suite.

The release is intended for local and deployment-owned environments. It does not provision external provider credentials, publish a cloud API, launch a browser session, or authorize external side effects. Those activities remain controlled by the existing explicit approval, local configuration, and deployment procedures.

## Notable fixes and improvements

| Area | Release change | Outcome |
|---|---|---|
| Preview runtime | Added bounded TCP readiness polling after static-server startup, early child-exit diagnostics, and bounded process cleanup. | A returned `running` preview record now represents an accepting listener. |
| GUI portability | Moved display projection, state classification, dashboard aggregation, and GUI-to-engine action construction to `orville_core.gui_state`. | Non-rendering desktop contracts can run without importing Tkinter. |
| Browser and API contracts | Updated the shell-control-plane research rejection test to require an operation-aware, safe allowlist reason without exposing the requested host. | The combined API/browser readiness suite passes. |
| Cross-platform paths | Preserved fully qualified Windows sandbox paths on POSIX control hosts and validated native or Windows absolute paths. | Windows Sandbox configuration can be generated and validated cross-platform without accepting relative paths. |
| Regression discipline | Added a deterministic visual-regression baseline and portable repository-reference resolution. | Visual and documentation contracts are reproducible on POSIX and Windows path conventions. |

## Validation

The release candidate passed the following local checks. The Starlette test client emits one upstream `httpx` deprecation warning; it does not cause a test failure and does not alter the validated behavior.

| Validation command or procedure | Result | Evidence |
|---|---:|---|
| Full pytest integration suite | **789 passed, 6 subtests passed** in 22.27 seconds | `artifacts/test_runs/passing_release_candidate_pytest_2026-08-27.log` |
| Combined authenticated API and Browser Operator suite | **28 passed** in 5.06 seconds | `artifacts/test_runs/api_browser_readiness_after_shell_contract_fix_2026-08-27.log` |
| Repeated preview readiness check | **10 consecutive passing runs** | `artifacts/test_runs/preview_runtime_readiness_2026-08-27.log` |
| Wheel and source-distribution build | **Passed** | `dist/orville_core-0.1.0-py3-none-any.whl`, `dist/orville_core-0.1.0.tar.gz` |
| Isolated wheel installation/import validation | **Passed** | `artifacts/test_runs/distribution_validation_after_fix_2026-08-27.log` |

## Distribution artifacts

| Artifact | SHA-256 |
|---|---|
| `orville_core-0.1.0-py3-none-any.whl` | `fdd71e325b3d979b630d804e36681428b7ea0210317907b40504178f9353bd83` |
| `orville_core-0.1.0.tar.gz` | `6b6e91ecb7d0a8c7a9a82c62dcea856882e75abc5aa9b02314168453fd0d1e1d` |

The `dist/SHA256SUMS` manifest is the authoritative in-repository checksum record. Verify a downloaded artifact using `sha256sum -c SHA256SUMS` from the directory that contains the listed paths, or compare its SHA-256 digest to the table above.

## Upgrade and operation

Install the wheel in a supported Python 3.10+ environment with the API or browser optional extras appropriate to the deployment. Review `API_BRIDGE.md` before enabling the authenticated local API, and review `CONNECTOR_BRIDGE.md` before loading the unpacked Manifest V3 Browser Operator extension. Keep API tokens and connector credentials in the approved protected runtime configuration; do not add secrets to the package, release notes, or repository state.

The distribution validates importability of its orchestration, API, preview-runtime, and browser-relay modules from an isolated virtual environment. Deployment-specific transport security, real browser profile pairing, provider authorization, and external connector execution require a separately configured authorized environment.

## References

[1]: https://github.com/Ravn420/Orville-Automation-Agent/blob/main/CHANGELOG.md "Orville changelog"
[2]: https://github.com/Ravn420/Orville-Automation-Agent/blob/main/pyproject.toml "Orville Core package metadata"
[3]: https://github.com/Ravn420/Orville-Automation-Agent/blob/main/API_BRIDGE.md "Authenticated API setup"
[4]: https://github.com/Ravn420/Orville-Automation-Agent/blob/main/CONNECTOR_BRIDGE.md "Browser Operator and connector bridge setup"
