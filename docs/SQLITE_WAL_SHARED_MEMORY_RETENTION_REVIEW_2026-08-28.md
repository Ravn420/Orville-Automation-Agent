# SQLite WAL and Shared-Memory Retention Review

**Review date:** 2026-08-28 UTC  
**Repository:** `/home/ubuntu/Orville-Automation-Agent`  
**Task:** `TODO-570aaf580e3d`  
**Review owner:** Orchestration Agent  
**Scope:** Inspection and retention decision only. No deletion, quarantine, archive move, database checkpoint, or content extraction was performed.

## Decision

The four tracked SQLite runtime files listed below are **retained**. They are not cleanup targets in this worker cycle. The two path pairs have identical contents by SHA-256, which is consistent with a mirrored local-data layout but is not, by itself, proof that either pair is disposable. The write-ahead-log files are empty in this checkout, while the shared-memory files are recognized as SQLite shared-memory files. Their runtime lifecycle cannot be inferred safely from their names or current sizes.

> **Destructive approval status:** Not granted. This review explicitly authorizes inspection-only work and records that no deletion or mutation is approved. Any future deletion, archive, quarantine, or database lifecycle operation requires a new approval naming the exact path list, backup/checkpoint result, reviewer, expiry, and rollback method.

## Exact-path inventory

| ID | Repository-relative path | Git state | Type | Size | SHA-256 | Decision | Retention basis |
|---|---|---|---|---:|---|---|---|
| W-01 | `.orville/orville.db-shm` | tracked and present | SQLite WAL shared-memory file | 32,768 bytes | `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb` | Retain | Runtime database state; do not remove while ownership and recovery status are not proven |
| W-02 | `.orville/orville.db-wal` | tracked and present | SQLite write-ahead log | 0 bytes | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Retain | SQLite transaction lifecycle; empty does not establish safe deletion |
| W-03 | `data/.orville/orville.db-shm` | tracked and present | SQLite WAL shared-memory file | 32,768 bytes | `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb` | Retain | Persistent application data; preserve until an approved database recovery procedure exists |
| W-04 | `data/.orville/orville.db-wal` | tracked and present | SQLite write-ahead log | 0 bytes | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Retain | Persistent application data; preserve until an approved checkpoint/backup is verified |

The files were mode `0644` and had the same recorded modification timestamp within each mirrored pair during inspection. No database- or Orville-named process was present in the sampled process list. That observation is not a substitute for an ownership lock, SQLite connection check, or operator confirmation.

## Privacy and secret scan

The review did not print or inspect the contents of the WAL, shared-memory, database, or browser-session files. A repository text scan was performed using high-confidence credential patterns. It found no private-key headers, AWS-style access-key IDs, GitHub personal-access-token prefixes, or common `sk-` API-key prefixes. A separate generic `password`-word scan matched four source/UI files (`orville_core/boundary.py`, `orville_core/endpoint_probe.py`, `webui/assets/index-WtVoC55i.js`, and `webui/index.html`); those matches were recorded as file-and-line metadata only and were not treated as credential evidence. Binary runtime files were not content-scanned.

## Ownership, recovery, and future-action requirements

The owning process and database lifecycle owner remain environment-specific and are not established by this local review. Before any future mutation, an operator must freeze active workers and database users, create a verified database checkpoint or backup, confirm whether browser-session state is needed, compare the exact path list with the checkpoint, and obtain separate approval for the named paths. The approved operation must be reversible or have a documented restore test. A broad directory deletion, `git clean`, wildcard removal, or Git-history rewrite remains prohibited.

## Evidence commands

The review used read-only commands equivalent to the following from the repository root:

```bash
git ls-files | grep -E '(^|/)[^/]+\\.(db|sqlite|sqlite3)(-wal|-shm)$|(^|/)[^/]+\\.(wal|shm)$'
find . -type f \\( -name '*.db-wal' -o -name '*.db-shm' -o -name '*.sqlite-wal' -o -name '*.sqlite-shm' -o -name '*.wal' -o -name '*.shm' \\) -not -path './.git/*'
stat -c '%n|size=%s|mode=%a|mtime=%y' <exact-path>
sha256sum <exact-path>
git grep -Il -E '<high-confidence-credential-patterns>' -- . ':!*.pyc'
ps -eo pid=,args= | grep -Ei '[o]rville|[s]qlite'
file <exact-path>
```

## Acceptance disposition

The named-path inventory, retention rationale, and privacy-safe scan are complete. The explicit gate record above confirms that this worker cycle authorizes no destructive action. The task is complete as an inspection-only local contract; destructive cleanup remains a separate, approval-gated task.

## References

- [`docs/WORKER_TASK_2_NAMED_PATH_DELETION_INVENTORY_AND_DRY_RUN.md`](WORKER_TASK_2_NAMED_PATH_DELETION_INVENTORY_AND_DRY_RUN.md)
- [`docs/REPOSITORY_AUDIT_2026-08-27.md`](REPOSITORY_AUDIT_2026-08-27.md)
- [`TASK_GRAPH.md`](../TASK_GRAPH.md)

_Last updated by Manus AI._
