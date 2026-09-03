# SQLite WAL and Shared-Memory Artifact Review

**Review date:** 2026-09-01
**Reviewer:** Orville roadmap operator
**Related TODO:** `TODO-570aaf580e3d`
**Scope:** Review tracked SQLite sidecars without deleting, moving, overwriting, checkpointing, archiving, uploading, or publishing any data.

## Named-path decision

| Path | Artifact | Observed state | Decision |
|---|---|---:|---|
| `.orville/orville.db-wal` | SQLite write-ahead log | 0 bytes | Retain in place pending an approved repository-cleanup policy. |
| `.orville/orville.db-shm` | SQLite shared-memory sidecar | 32,768 bytes | Retain in place pending an approved repository-cleanup policy. |

Both paths are currently tracked by Git and both paths also appear in repository history. The repository uses SQLite WAL mode in its persistence and task-store implementations, so the sidecars are operationally related to the database lifecycle rather than being treated as arbitrary temporary files.

## Secret scan

A byte-oriented scan was run against both named sidecars for common credential markers including `api_key`, `secret`, `token`, `password`, `authorization`, and OpenAI-style key prefixes. The scan returned no matching file paths. This is a bounded indicator only; it is not a substitute for a database-aware review of the primary database.

## Retention rationale

No destructive cleanup is authorized by this review. The zero-byte WAL and non-empty shared-memory sidecar are retained because they are tracked, operationally associated with the SQLite database, and their removal could alter recovery or repository state. Any future removal must first establish whether the primary database is live, whether the sidecars are regenerated safely, whether the tracked artifacts are intentionally versioned, and whether a reproducible backup exists.

## Explicit approval record

**Approval status: not approved for destructive change.** This record authorizes observation and documentation only. It does not authorize deletion, truncation, movement, replacement, checkpointing, or history rewriting. A separate explicit operator approval record is required before any such action.

## Evidence

The review command enumerated the named paths, sizes, timestamps, Git tracking status, Git history paths, and the bounded secret-marker scan. No file contents were modified and no external system was contacted.
