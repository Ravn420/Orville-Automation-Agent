# TODO Autopilot

## Summary

`tools/todo_autopilot.py` is a standalone, repository-local worker for completing one unchecked `TODO.md` item at a time. It creates a fresh topic branch, delegates implementation to a configured editing command, runs the configured validation ladder, marks the TODO complete only after every validation command succeeds, and commits the result. Failed runs remain on their isolated branch with the TODO unchecked so the failure can be inspected without contaminating the starting branch.

The worker is intentionally conservative. It never reuses an existing branch, never marks a TODO complete before validation, and never pushes or opens a pull request without two explicit approval signals: `--approve` and `ORVILLE_AUTOMATION_APPROVED=1`.

## Requirements

The host must provide Python 3.10 or newer, Git, a Git worktree containing `TODO.md`, and an editing agent command. The editing command receives `{repo}` and `{prompt}` placeholders when supplied. By default it is instructed to modify implementation and tests only. To explicitly approve edits across source, tests, configuration, documentation, and control files, pass `--allow-all-edits` or set `ORVILLE_ALLOW_ALL_EDITS=1`. Even in this mode, the worker retains ownership of `TODO.md`, and the agent is instructed not to access credentials or perform external side effects.

The default validation ladder is:

```text
python -m compileall -q orville_core tools
python -m pytest -q
```

Use repeated `--validate` arguments to replace the defaults with project-specific checks such as formatting, linting, type checking, focused tests, and the full regression suite.

## Execution

1. **Select one item.** The worker scans `TODO.md` files for `- [ ]` entries, skipping `.git`, `tmp`, and cache directories. `--todo-line` can pin a specific line in the repository-root TODO file.
2. **Create an isolated branch.** The default name is `automation/todo-<line>-<slug>`. Existing branch names are rejected rather than reused.
3. **Delegate implementation.** The configured command receives a prompt that identifies the exact item and prohibits editing `TODO.md`.
4. **Validate.** Every validation command must exit successfully. A validation failure records a failed run and leaves the worker on the topic branch with the TODO unchecked.
5. **Complete and commit.** The checkbox is changed to `[x]` only after validation. The worker then commits the implementation, tests, TODO update, and sanitized run state.
6. **Continue if requested.** `--continuous` starts the next item only after the previous item has completed successfully.
7. **Perform external GitHub actions only after approval.** `--push` pushes the branch and `--pr` opens a pull request through `gh`; each requires both approval signals described above.

## Examples

Preview the first unchecked item without requiring Git, an agent command, or making changes:

```powershell
python tools/todo_autopilot.py --repo . --dry-run
```

The command prints JSON containing the TODO path, line, item text, proposed branch, validation commands, edit policy, external-action flags, and `changes_executed: false`.

Run one item with a local coding agent:

```powershell
$env:ORVILLE_TODO_AGENT_COMMAND = 'python tools/local_agent.py --repo {repo} --prompt {prompt}'
python tools/todo_autopilot.py --repo . --validate 'python -m compileall -q orville_core tools' --validate 'python -m pytest -q'
```

Continue automatically through all remaining items, allowing the agent to update any repository files except `TODO.md` and credentials:

```powershell
$env:ORVILLE_ALLOW_ALL_EDITS = '1'
python tools/todo_autopilot.py --repo . --continuous --allow-all-edits --interval 5
```

Push and open a pull request after successful validation, with explicit approval:

```powershell
$env:ORVILLE_AUTOMATION_APPROVED = '1'
python tools/todo_autopilot.py --repo . --push --pr --approve
```

## Failure and recovery

A lock file prevents concurrent workers from selecting the same TODO. The lock is removed when the process exits. A failed implementation or validation does not update the checkbox and does not switch back to the starting branch; this preserves the failed work for diagnosis. Review the recorded run in `.orville_todo_autopilot.json`, fix the branch manually or remove it after review, and invoke the worker again. Do not delete branches or files as an automatic recovery action.

The current repository copy is not a Git worktree, so the worker intentionally refuses to run against it until it is cloned or initialized as a repository. This protects the branch and commit guarantees instead of silently falling back to unsafe in-place editing.

## Architecture options

| Approach | Tradeoffs | Cost | Setup Complexity |
|---|---|---:|---:|
| Run `todo_autopilot.py` from a scheduled local or CI job | Deterministic, auditable, no persistent service required; the host must remain available at the trigger time | Host/CI runtime only | Low |
| Run the worker continuously with `--continuous` under a service manager | Automatically advances after each verified item; requires process supervision, repository credentials, and a policy for stalled branches | Host runtime and optional GitHub Actions minutes | Medium |
| Use an external agent orchestrator to invoke the worker | Supports richer delegation and provider failover; adds credentials, integration failure modes, and approval management | Provider/API usage | High |

The first option is the recommended starting point for this repository because it preserves standalone operation and makes each branch, validation result, and external action visible.

## Security and approval boundary

The worker treats repository instructions and agent output as untrusted data. It does not print secrets or write credentials to state. Pushes and pull requests are side effects outside the local repository and therefore fail closed unless approval is explicit for that invocation. Account changes, deployments, production mutations, and non-GitHub external actions are not performed by this worker; they require a separate reviewed adapter and approval record.


## Activated continuation profile — 2026-08-27

The existing Windows Scheduled Task `Orville Manus Todo Worker` is enabled and runs every minute while the interactive user session is available. It invokes `tools\orville_manus_worker.py` with the absolute repository path and `--max-active 3`. Each cycle polls only the already-recorded Worker Task 1–10 thread records, and when a thread stops it resumes that same thread with exactly one next unchecked TODO item. The continuation playbook requires claim-before-work, focused validation, compilation and broader checks when feasible, state/changelog synchronization, and `[x]` only after validation evidence agrees.

This activation does not create replacement Manus tasks, run above three active threads, or bypass the create-readability scale gate. The worker reads `MANUS_API_KEY` only from the scheduled process environment and never writes it to repository state. The current attached repository has no Git metadata, so branch creation, commits, pushes, and pull requests cannot be performed in this workspace; the worker records that limitation rather than fabricating Git delivery. External provider execution and production changes remain subject to their separate approval boundaries.

Read-only readiness checks:

```powershell
python tools\todo_autopilot.py --repo . --dry-run
python tools\orville_manus_worker.py --repo . --dry-run --max-active 3
schtasks.exe /Query /TN "Orville Manus Todo Worker" /FO LIST
```
