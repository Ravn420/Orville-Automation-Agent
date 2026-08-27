# Worker Task 2 Named-Path Deletion Inventory and Dry-Run Procedure

**Document status:** Prepared—operator approval required before any deletion
**Task:** Remove obsolete dependencies, connectors, instructions, and artifacts
**Owner:** Worker Task 2, with Orchestration/Automation execution and Verification review
**Prepared:** 2026-08-27
**Safety posture:** Inspection and dry run only; no deletion is authorized by this document

## 1. Purpose

This document turns the cleanup checkpoint into a reviewable, named-path change. It separates disposable runtime material from tracked evidence, active configuration, connector definitions, and release records. Every path must be individually classified and approved before a mutation. A glob, directory-wide deletion, or inferred “old” status is not an acceptable substitute for named-path approval.

The working tree and repository history are evidence. The following procedure must not rewrite Git history, remove remote branches, delete provider-side resources, revoke credentials, or modify a connector merely because a local path appears unused.

## 2. Candidate inventory

The inventory below contains known candidates and protected examples from the current Orville repository. `Candidate` means “inspect and classify,” not “delete.” The operator must fill the evidence, retention, and decision columns from the exact current checkout before approval.

| Inventory ID | Named path or exact pattern | Class | Default decision | Required review |
|---|---|---|---|---|
| C-01 | `.pytest_cache/` | Local test cache | Candidate for deletion | Confirm untracked, not required by an active run, and reproducible from source |
| C-02 | `**/__pycache__/` | Python bytecode cache | Candidate for deletion | Enumerate exact directories and confirm no active process depends on them |
| C-03 | `**/*.pyc` | Python bytecode artifacts | Candidate for deletion | Record exact files and ensure source-controlled equivalents exist |
| C-04 | `artifacts/test_runs/unittest_discover_2026-08-27.log` | Test evidence | Retain by default | Verify retention owner and release-readiness references before any move or deletion |
| C-05 | `artifacts/test_runs/unittest_discover_with_pytest_2026-08-27.log` | Test evidence | Retain by default | Preserve because it supports the current collection/regression disposition |
| C-06 | `artifacts/project_assessment_2026-08-27.md` | Project assessment | Retain by default | Check references from audit, readiness, and task-graph records |
| C-07 | `docs/FULL_REGRESSION_TRIAGE_2026-08-27.md` | Regression decision record | Protected | Never delete while full-suite failures or release exceptions remain open |
| C-08 | `docs/READINESS_REPORT.md` | Readiness evidence | Protected | Keep as the current readiness contract and blocker record |
| C-09 | `docs/M14_8_NONPRODUCTION_CHANGE_PACKAGE.md` | Change-control evidence | Protected | Keep until M14.8 acceptance and post-change retention are complete |
| C-10 | `docs/M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md` | Operational control | Protected | Keep as the execution procedure and audit reference |
| C-11 | `docs/M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md` | Recovery control | Protected | Keep as the downstream backup/restore acceptance plan |
| C-12 | `docs/BLACKBOX_INTEGRATION.md` | Connector/security contract | Protected | Do not remove without a reviewed replacement and architecture approval |
| C-13 | `docs/BLACKBOX_INTEGRATION_RESEARCH.md` | Provider research record | Retain by default | Needed for M12.18 claim reconciliation and support verification |
| C-14 | `.env`, `.env.*`, local credential files, and secret stores under the project root | Secret material | Never delete by this procedure | Escalate to Security Agent; do not print, copy, or commit contents |
| C-15 | Git-tracked source, tests, `TODO.md`, `STATE.md`, `TASK_GRAPH.md`, and configuration | Product/control plane | Never delete by cleanup checkpoint | Requires a separate reviewed change and migration plan |
| C-16 | Any connector configuration path discovered by the inventory command | Connector configuration | Retain until owner confirms obsolete | Record connector UID/category without exposing tokens; obtain owner and dependency review |
| C-17 | Any instruction/skill file discovered by the inventory command | Project instruction | Retain until replacement is accepted | Trace references and confirm no task or agent relies on the file |
| C-18 | Any generated artifact not listed above | Generated evidence | Retain by default | Identify producer, consumers, retention period, and recoverability |
| C-19 | `data/.orville/` | Persistent Orville application data directory | **Retain** | Contains the live local database and session state; no deletion or quarantine without an approved data migration and restore test |
| C-20 | `data/.orville/browser-sessions.json` | Browser session state | **Retain and protect** | Treat as sensitive application state; do not print or inspect contents in cleanup output; delete only through a separate approved session-reset procedure |
| C-21 | `data/.orville/orville.db-shm` | SQLite shared-memory file | **Retain while the database is active** | Confirm no Orville process is using the database; remove only as part of an approved SQLite lifecycle/recovery procedure after a verified checkpoint |
| C-22 | `data/.orville/orville.db-wal` | SQLite write-ahead log | **Retain while the database is active** | Preserve pending transactions; checkpoint/backup and verify restore before any approved cleanup |

The wildcard rows C-01 through C-03 and C-16 through C-18 are collection scopes only. They must be expanded into exact absolute or repository-relative paths in the signed inventory before any deletion approval.

## 2.1 Observed data-directory decision

The current checkout contains exactly these observed data paths: `data/`, `data/.orville/`, `data/.orville/browser-sessions.json`, `data/.orville/orville.db-shm`, and `data/.orville/orville.db-wal`. The data directory is therefore **not a cleanup target** in the current review. The directory and all three observed files are retained. In particular, the browser-session file is sensitive state, while the SQLite shared-memory and write-ahead-log files may represent an active or recoverable database lifecycle. Their presence is not evidence of obsolescence.

Before any future change to this decision, the operator must identify the owning process, establish a consistent database checkpoint or backup, verify that the browser-session state is no longer needed, and obtain separate approval naming the exact path. The current dry run must report metadata only and must never print the contents of `browser-sessions.json`.

## 3. Inventory collection procedure

Run the following read-only commands from a clean checkout. Redirect output to a review file rather than displaying secret-bearing paths or file contents. Do not use `rm`, `git clean`, `find -delete`, or a shell command that mutates the tree during inventory.

```bash
cd /home/ubuntu/Orville-Automation-Agent
mkdir -p artifacts/cleanup_review
find . -path './.git' -prune -o -type d \( -name '__pycache__' -o -name '.pytest_cache' \) -print \
  > artifacts/cleanup_review/cache-directories.txt
find . -path './.git' -prune -o -type f \( -name '*.pyc' -o -name '*.pyo' \) -print \
  > artifacts/cleanup_review/bytecode-files.txt
git status --short > artifacts/cleanup_review/git-status.txt
git ls-files > artifacts/cleanup_review/tracked-paths.txt
find . -path './.git' -prune -o -type f -printf '%p\t%s bytes\t%TY-%Tm-%TdT%TH:%TM:%TS\n' \
  > artifacts/cleanup_review/file-manifest.tsv
```

Next, use repository search to enumerate references to every candidate. Search the path names in source, documentation, task graph, test configuration, packaging metadata, and release notes. Record the command, timestamp, checkout commit, and result count. Do not treat zero textual references as proof that a file is disposable; runtime discovery, imports, packaging rules, and external operators may not appear in repository text.

## 4. Classification and retention decision

For each exact path, the operator records one decision: `retain`, `archive`, `move-to-quarantine`, or `delete-after-approval`. `Retain` is the default. `Archive` requires an approved destination, integrity hash, access control, and restore test. `Move-to-quarantine` requires a reversible location and expiry. `Delete-after-approval` requires the destructive-action checkpoint described below.

| Required field | Acceptance condition |
|---|---|
| Exact path | No unresolved glob, symlink ambiguity, or path traversal |
| Owner | Named person/agent accepts responsibility for the decision |
| Producer/consumer | Source of the item and all known readers are recorded |
| Classification | Cache, evidence, connector, instruction, source, secret, or other |
| Retention basis | Policy, task reference, release evidence, or explicit owner decision |
| Recovery | Backup/archive path and restore test if not disposable |
| Decision | Retain/archive/quarantine/delete with reason |
| Approval | Named approver, timestamp, scope, and expiry |
| Verification | Post-action check and evidence path |

## 5. Safe dry-run procedure

### 5.1 Freeze and snapshot

Confirm that no test run, worker, deployment, connector sync, or evidence upload is active. Record the commit SHA, branch, working-tree status, current task-graph state, and a manifest hash. If any process is active or status is dirty for an unrelated reason, stop and reschedule.

### 5.2 Build an approved candidate list

Copy the classified exact paths into a review file such as `artifacts/cleanup_review/approved-candidates.txt`. The file must contain one repository-relative path per line, no comments interpreted as paths, and no wildcard entries. A second reviewer compares it with the inventory and confirms that protected paths C-04 through C-15 are not present unless a separate approved retention change exists.

### 5.3 Simulate the action without mutation

For each approved candidate, resolve the path and report its type, size, ownership, symlink target, Git tracking state, and SHA-256 where appropriate. A safe dry run may use `test`, `stat`, `git ls-files --error-unmatch`, and `sha256sum`. The dry run must not follow a symlink outside the repository, evaluate shell substitutions from the candidate file, or print secret contents.

```bash
cd /home/ubuntu/Orville-Automation-Agent
while IFS= read -r path; do
  test -n "$path" || continue
  case "$path" in
    /*|*..*|*\**|*\?*|*\[*|*\]*|*\$*|*\;*|*\|*|*\&*)
      printf 'REJECTED unsafe candidate: %s\n' "$path"; exit 1 ;;
  esac
  test -e "$path" || { printf 'MISSING: %s\n' "$path"; continue; }
  printf 'DRY-RUN: %s\n' "$path"
  stat --printf='type=%F size=%s mode=%A path=%n\n' -- "$path"
  if git ls-files --error-unmatch -- "$path" >/dev/null 2>&1; then
    printf 'TRACKED: %s\n' "$path"
  else
    printf 'UNTRACKED: %s\n' "$path"
  fi
done < artifacts/cleanup_review/approved-candidates.txt
```

The shell snippet is intentionally fail-closed for wildcards, absolute paths, traversal-like tokens, and shell metacharacters. It is an inspection loop, not a deletion command. A reviewer must inspect the dry-run output and sign that every path is the intended object.

### 5.4 Approval checkpoint

No deletion may occur without explicit operator confirmation naming the exact approved list, the backup/archive result, the reviewer, the expiry time, and the rollback method. The approval is invalid if the candidate list, commit, checkout, or scope changes. A new approval is required after any material change.

### 5.5 If deletion is later authorized

Deletion is a separate change, not part of this preparation task. The executor must use a version-controlled script or individually reviewed commands that read only the signed exact-path list, refuse tracked/protected paths, refuse symlinks, record pre-delete hashes, and stop on the first mismatch. The executor must not use `git clean -fdx`, recursive wildcard removal, or a broad directory removal.

After the approved action, verify that protected paths remain, tests and imports still work, connectors remain unchanged, evidence links resolve, the working tree reflects only the approved change, and the recovery path can restore any archived item. Record the post-action manifest and independent reviewer sign-off.

## 6. Stop conditions

Stop immediately if a candidate is tracked, referenced by a live task or release record, a secret or connector boundary is involved, the path resolves outside the repository, the path changed after approval, the archive hash differs, a process is active, or any command would broaden the approved scope. Stop if the operator cannot identify a recovery path for an evidence-bearing artifact.

## 7. Current disposition

The current disposition is **inspection-only**. No deletion, quarantine, archive move, connector change, credential revocation, Git-history rewrite, or remote cleanup was performed. The cleanup task remains blocked until the inventory is expanded to exact paths and the destructive-action approval is explicitly recorded.

## References

- [`TASK_GRAPH.md`](../TASK_GRAPH.md), Worker Task 2 cleanup checkpoint and blocker.
- [`CLEAN_ENVIRONMENT_VALIDATION.md`](CLEAN_ENVIRONMENT_VALIDATION.md), clean-environment and validation controls.
- [`APPROVAL_CHECKPOINTS.md`](APPROVAL_CHECKPOINTS.md), approval and external-action gates.
- [`READINESS_REPORT.md`](READINESS_REPORT.md), evidence retention and current blocker record.
- [`FULL_REGRESSION_TRIAGE_2026-08-27.md`](FULL_REGRESSION_TRIAGE_2026-08-27.md), active regression evidence that must be retained.

_Last updated by Manus AI._
