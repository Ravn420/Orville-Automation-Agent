# SQLite WAL and Shared-Memory Artifact Retention Review

**Review date:** 2026-08-28
**Repository:** Orville
**Task:** `TODO-570aaf580e3d`
**Reviewer:** Orchestration Agent
**Scope:** Tracked SQLite `-wal` and `-shm` sidecar paths only. No database or sidecar was deleted, rewritten, vacuumed, checkpointed, or otherwise mutated.

## Decision summary

The named tracked sidecar paths are **retained for this review and not deleted**. They are runtime SQLite artifacts that were committed by the repository's initialisation commit, and their removal would be a destructive repository/data operation requiring explicit approval. The repository's `.gitignore` contains database patterns, but those patterns do not retroactively untrack already committed paths.

| Named path | Tracked | Present at review | Size | SHA-256 | Decision | Rationale |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `.orville/orville.db-shm` | Yes | Yes | 32,768 bytes | `FD4C9FDA9CD3F9AE7C962B0DDF37232294D55580E1AA165AA06129B8549389EB` | Retain pending explicit approval | Shared-memory sidecar; tracked runtime state. Do not infer that it is disposable merely because it is a sidecar. |
| `.orville/orville.db-wal` | Yes | Yes | 0 bytes | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | Retain pending explicit approval | Write-ahead-log sidecar; empty at review, but deletion is still an unapproved destructive change. |
| `data/.orville/orville.db-shm` | Yes | Yes | 32,768 bytes | `FD4C9FDA9CD3F9AE7C962B0DDF37232294D55580E1AA165AA06129B8549389EB` | Retain pending explicit approval | Duplicate-content shared-memory sidecar under the data runtime tree; retain until ownership and lifecycle are explicitly resolved. |
| `data/.orville/orville.db-wal` | Yes | Yes | 0 bytes | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | Retain pending explicit approval | Duplicate-content write-ahead-log sidecar; empty at review, but no deletion authority was provided. |

The adjacent `data/.orville/orville.db` file was observed for context and was not modified. It is not one of the four selected sidecar paths and is not included in the decision above.

## Provenance and path controls

All four sidecars are tracked by Git and were introduced by the repository initialisation commit `62e8df0` (`chore: initialize Orville Automation Agent`, dated 2026-08-27). No later path-specific history was found. The current branch is the focused `docs/sqlite-artifact-retention-review` branch. The inspection used exact repository-relative paths; no recursive deletion, wildcard deletion, database checkpoint, or filesystem mutation was performed.

The repository operating rules state that runtime SQLite databases and related user state belong under configured application data or portable data directories rather than source-controlled directories. This review records the existing tracked paths as a governance finding, not as authorization to remove them. A future cleanup change should first identify the owning runtime, confirm that no process holds the database, preserve any required evidence or backup, and obtain approval naming the exact paths and operation.

## Secret scan

A focused scan was run without printing artifact contents:

```text
git grep -l -I -E -e 'BEGIN [A-Z ]*PRIVATE KEY' -e 'gh[pousr]_[A-Za-z0-9]{20,}' -e 'AIza[0-9A-Za-z_-]{30,}' -e 'Bearer[[:space:]][A-Za-z0-9._-]{20,}' -- .
Select-String -Path '.orville/orville.db-shm','data/.orville/orville.db-shm','.orville/orville.db-wal','data/.orville/orville.db-wal' -Pattern 'BEGIN|PRIVATE KEY|ghp_|AIza|Bearer[[:space:]]|password[[:space:]]*=|api[_-]?key[[:space:]]*=' -AllMatches -CaseSensitive:$false
```

The sidecar scan reported **no marker strings**. The tracked-text scan reported only repository files containing test fixtures or security-review code that reference the scan vocabulary; it did not report a high-signal credential value. No secret value was copied into this record. This is a bounded marker scan, not proof that arbitrary encrypted or binary data can never contain sensitive information.

## Explicit approval record

| Field | Record |
| --- | --- |
| Requested action | Review and, if approved, remove tracked SQLite WAL/shared-memory artifacts |
| Exact destructive targets | `.orville/orville.db-shm`, `.orville/orville.db-wal`, `data/.orville/orville.db-shm`, `data/.orville/orville.db-wal` |
| Approval status | **Not granted; no destructive action performed** |
| Requester / approver | No approver supplied for deletion in this task turn |
| Time | 2026-08-28 review date; approval timestamp not applicable |
| Authorized scope | Inspection, hashing, secret scanning, and retention documentation only |
| Result | Retain all four named paths pending a separately recorded explicit approval decision |

This record is deliberately a **no-approval / no-deletion record**. It must not be interpreted as approval for future removal. Any destructive follow-up must create a new approval record naming the requester, approver, exact paths, scope, and time before changing the repository or data.

## Validation evidence

The following checks were completed on the attached repository:

| Check | Result |
| --- | --- |
| Exact named-path inventory | Passed; all four paths exist and are tracked |
| Size and SHA-256 capture | Passed; values are recorded above |
| Git provenance review | Passed; initialisation commit identified; no later path-specific history found |
| Secret marker scan | Passed; no marker strings in sidecars; no high-signal credential values reported in tracked text |
| Destructive-action audit | Passed; no files deleted or mutated |
| Focused project-control tests | Passed; `tests/test_project_checks.py`: 4 passed |
| Python compilation | Passed; `python -m compileall -q orville_core tools` |
| Broader project checks | Built the wheel and completed compilation, but exited non-zero on two unrelated existing platform/baseline failures: the performance-boundary timing test and Windows-path separator expectation in `tests/test_security_hardening.py` |
| Full regression | 823 passed, 1 skipped, 2 failed, 1 warning, and 6 subtests passed; failures are unrelated to this documentation-only change and are recorded rather than masked |

## Open risk

The focused validation for this item passed. The broader repository gate remains non-green because of two unrelated existing failures (`test_graph_size_100_tasks_completes_within_bounded_time` and `sandbox_plan_preserves_windows_absolute_paths_from_request`); this task did not alter the implementation exercised by either test.

The repository currently tracks runtime SQLite sidecars despite its ignore rules and operating guidance. Retaining them preserves evidence and avoids unapproved data loss, but it also leaves a potential source-control hygiene and runtime-state risk. A separate, approval-gated cleanup or migration task should decide whether these paths are removed from version control, regenerated in an approved data directory, or retained as intentional fixtures.
