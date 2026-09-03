# Final Local Acceptance Report

**Repository:** `/home/ubuntu/orville-recovery`
**Run date:** 2026-09-02
**Command:** `python3 -m pytest -q --ignore=tests/__pycache__`

## Result

| Measure | Result |
|---|---:|
| Passing tests | 874 |
| Failing tests | 9 |
| Collection/setup errors | 0 |
| Warnings | 1 Starlette/httpx deprecation warning |
| Subtests | 6 passed |

The GUI source and packaging support files have since been restored from the pre-refactor Git revision, and the full suite now collects successfully. The nine remaining failures are primarily contract mismatches caused by intentionally replacing the historical `TODO.md` with the reduced remaining-work roadmap, a missing deployment-only Docker prerequisite that has now been restored, and one local performance-boundary overrun. The failures are not converted into passes and no generated placeholder GUI source was introduced. Focused backend, persistence, evaluation, observability, security, runtime, visual-contract, and configuration suites pass.

## Deployment-owned gates

Production identity, TLS, deployment secrets, audit sink, real provider/model credentials, live sandbox adapter, device/screen-reader environment, and clean deployment topology remain unavailable. These are recorded as blocked in `TODO.md`; local contracts fail closed when those dependencies are absent.

## Reproduction and closure

Restore the complete GUI source tree and select an approved deployment topology. Then rerun the full suite, live GUI/accessibility matrix, sandbox boundary tests, production identity/TLS checks, real-provider workflow, packaging, rollback, and disaster-recovery validation. A release must not be declared complete from the local result alone.
