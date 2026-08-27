# Autonomous TODO Completion Workflow

## Summary

The Orville worker continues one existing task thread at a time after each turn stops. Each continuation is bound to exactly one unchecked TODO item and must claim, implement, validate, synchronize, and report that item before it may be marked complete.

## Completion state machine

| State | Required behavior |
|---|---|
| `unchecked` | Select one actionable `- [ ]` item that is not already reserved by another worker record. |
| `in_progress` | Claim the item as `[-]` before substantial implementation work. |
| `implemented` | Edit only the files needed for the selected item and preserve repository guidance. |
| `validated` | Run focused tests, Python compilation, and broader regression checks when feasible. Triage failures before completion. |
| `synchronized` | Update `STATE.md`, `TASK_GRAPH.md`, `CHANGELOG.md`, and evidence paths when materially required. |
| `complete` | Change the item to `[x]` only after implementation, tests, state, and changelog evidence agree. |
| `blocked` | Change the item to `[!]` with a concise blocker note when a decision, credential, environment, or approval is required. |

A stopped task is resumed with the next eligible item. A failed or waiting task remains recorded so a later invocation can retry or continue it. The worker does not claim multiple TODO items for one task turn.

## Git delivery behavior

When the repository is a Git worktree, the task should create a focused branch before editing, keep the branch scoped to one TODO item, commit only validated changes, and open a pull request only after all required checks pass. If `.git` metadata or a remote is unavailable, the task must not fabricate a branch, commit, or pull request. It must record the delivery limitation and still perform local validation.

The attached Orville directory currently has no `.git` metadata or remote origin. Consequently, branch creation and pull-request delivery are unavailable in this workspace until the directory is connected to a Git repository.

## External changes

External changes are not implied by TODO completion. Publishing, deletion, account changes, purchases, deployments, messages, connector actions, and other irreversible operations require their applicable explicit approval gate. A task may prepare a plan or dry run without approval but must stop before the live operation.

## Worker configuration

The Windows Scheduled Task invokes:

```powershell
python tools\orville_manus_worker.py --repo "C:\Users\Zeref\Documents\Manus Projects\Orville" --max-active 3
```

The worker can be raised to ten existing task threads only after the creation-readability gate passes. A real scaled invocation must include:

```powershell
python tools\orville_manus_worker.py --repo "C:\Users\Zeref\Documents\Manus Projects\Orville" --max-active 10 --validate-create-readability
```

The gate is fail-closed when a newly created diagnostic task remains unreadable. It prevents the worker from polling additional records under an API routing condition known to return inaccessible task IDs.

## Validation commands

Run the focused worker checks with:

```powershell
python -m pytest -q tests\test_orville_manus_worker.py tests\test_worker_creation_validation.py
python -m py_compile tools\orville_manus_worker.py tests\test_orville_manus_worker.py tests\test_worker_creation_validation.py
```
