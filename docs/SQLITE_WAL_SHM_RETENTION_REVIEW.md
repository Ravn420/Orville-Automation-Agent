# SQLite WAL and Shared-Memory Retention Review

**Review date:** 2026-08-28  
**Selected TODO:** `TODO-570aaf580e3d`  
**Scope:** Tracked SQLite WAL and shared-memory artifacts only. No file was deleted, truncated, compacted, or rewritten.

## Decision

> **Retain all four named paths unchanged. No destructive change is approved or performed in this task turn.**

The files are orphaned sidecar artifacts: the repository tracks the WAL and shared-memory files but does not track a corresponding SQLite primary database at either location. The WAL files are empty, and the two shared-memory files are identical 32 KiB artifacts created by the repository bootstrap state. Removing them could erase forensic or reproducibility evidence and is not necessary to validate the current repository. A future cleanup may remove them only after an explicit owner approval identifies the exact paths and confirms that no SQLite process or recovery workflow depends on them.

## Named-path inventory

| Path | Tracked | Size | SHA-256 | Decision |
|---|---:|---:|---|---|
| `.orville/orville.db-shm` | Yes | 32,768 bytes | `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb` | Retain unchanged |
| `.orville/orville.db-wal` | Yes | 0 bytes | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Retain unchanged |
| `data/.orville/orville.db-shm` | Yes | 32,768 bytes | `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb` | Retain unchanged |
| `data/.orville/orville.db-wal` | Yes | 0 bytes | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Retain unchanged |

The four paths were first introduced in repository initialization commit `62e8df0`. No other present or tracked `.db`, `.sqlite`, `.sqlite3`, WAL, SHM, or shared-memory files were found in the scoped inventory.

## Secret scan

A read-only scan covered **680 tracked files** using patterns for private keys, AWS access keys, GitHub tokens, OpenAI-style keys, bearer tokens, and password assignments. It reported eight matches, all in test fixtures or test/security-review source where the strings are synthetic pattern examples or detection rules:

| Pattern class | Paths | Assessment |
|---|---:|---|
| Bearer-token pattern | 7 | Synthetic test/security-review strings; no finding in the four SQLite sidecars |
| Password-assignment pattern | 1 | Synthetic security-test string; no finding in the four SQLite sidecars |

The binary sidecars contain no printable secret material identified by the scan, and no secret values were printed or copied into this record.

## Approval and retention record

**Destructive action approval:** Not requested and not granted.  
**Action taken:** None; all four paths remain byte-for-byte unchanged.  
**Retention approval basis:** The task instruction explicitly prohibits automatic deletion and requires a decision before destructive change. Retention is the non-destructive default pending explicit owner approval for any future removal.  
**Future removal gate:** A subsequent task must name the exact paths, confirm the corresponding SQLite database/process dependency check, obtain explicit owner approval, then remove only the approved paths and rerun repository validation.

## Validation

The inventory, SHA-256 checks, Git tracking check, ignore-rule review, and secret scan were completed read-only. This checkpoint is the evidence required to mark `TODO-570aaf580e3d` complete; no unrelated roadmap item was changed.
