# Hub Transfer Retry Checkpoint

**Date:** 2026-08-28

The Hub download workflow has durable failure and retry telemetry. `DownloadJobManager` persists download state across restart, applies bounded retry and exponential backoff, and cooperates with pause and cancellation requests. Download list/detail API routes expose the retry counters, next retry time, last error, and transfer history used by the Signal Room queue.

| Requirement | Evidence | Result |
|---|---|---|
| Failure and persistence flow | `orville_core/hub_models.py` durable job records and restart recovery | Verified |
| Bounded retry/backoff | Hub transfer manager retry budget and delay fields | Verified |
| Pause/cancel cooperation | Existing download lifecycle controls and API routes | Verified |
| Retry telemetry persistence | Attempt/retry counters, delay, next retry time, last error, history | Verified |
| API exposure | `/api/v1/models/hub/downloads` list/detail responses | Verified |
| Queue rendering | Packaged Signal Room smoke checks and retry-state UI contract | Verified |
| Regression coverage | Focused Hub/model/API suite | 23 tests passed |
| Windows executable rebuild | Requires a Windows-native runner | Not run in Linux sandbox |

The full repository suite also passed **818 tests and 6 subtests** before this documentation-only checkpoint. The remaining Windows packaging item is intentionally left open until a Windows runner can rebuild and smoke-test the executable.
