# Orville Manus Roadmap Worker

## Summary

`tools/orville_manus_worker.py` is a standalone polling worker for existing Manus task threads. It persists active task records in `.orville_manus_worker_state.json`, uses an exclusive invocation lock, and monitors at most ten existing tasks by default. For a real CLI run above three tasks, it can optionally create one harmless private validation task and require immediate `task.detail` readability before polling existing records.

When an existing task reports `stopped`, the worker resumes that same task thread with the next actionable unchecked TODO item. The continuation prompt binds the task to the configured Orville repository directory and instructs the agent to use that directory's control files and implementation state.

The worker does not mark roadmap items complete itself. Each continued task must claim one item, implement it, validate it, update required state, and mark it `[x]` only after acceptance criteria pass. The worker only advances a task thread when the prior turn has stopped and a new unchecked item is available.

## Runtime requirements

Python 3.11 or newer is required. `MANUS_API_KEY` must be present in the process environment when making live API calls. The key is never written to the worker state or log files. The repository must contain `TODO.md` and the project control files used by the continued task. The state file may contain up to ten allowed task records named `Worker Task 1` through `Worker Task 10`. Those records hold the IDs of the already-created Manus tasks that the worker is allowed to continue; any other task record is ignored.

## Local invocation

From the repository root, run:

```powershell
$env:MANUS_API_KEY = '<value supplied through a protected environment mechanism>'
python tools\orville_manus_worker.py --repo 'C:\Users\Zeref\Documents\Manus Projects\Orville' --max-active 10 --validate-create-readability --validation-retries 3 --validation-interval 5
```

For a credential-free state inspection from the repository root:

```powershell
python tools\orville_manus_worker.py --repo 'C:\Users\Zeref\Documents\Manus Projects\Orville' --dry-run --max-active 10
```

If the script is launched from another directory, including `C:\Windows\System32`, pass the absolute repository root explicitly. The scheduled installer does this automatically so every background invocation uses the Orville repository directory rather than the scheduler's working directory.

`--max-active` accepts values from 1 through 10. The default is 10. Real CLI invocations above three require `--validate-create-readability`; the gate creates one private diagnostic task and retries its `task.detail` lookup on 404 and transient transport failures. If the task remains unreadable after `--validation-retries` attempts, the worker exits with code 2 and does not poll or mutate existing task state. Use `--validation-interval` to bound the delay between checks. The worker is safe to invoke repeatedly: `.orville_manus_worker.lock` prevents overlapping invocations, while the state file prevents duplicate reservation of TODO lines.

## Windows background execution

Run `tools\install_orville_manus_worker.ps1` from an elevated PowerShell session after configuring `MANUS_API_KEY` for the scheduled-task execution context. The installer registers a once-per-minute task with an explicit absolute `--repo` path, starts when available, ignores overlapping scheduled instances, and limits each invocation to 50 seconds.

The one-minute trigger is a continuation check, not a task-creation or task-completion delay. A stopped existing task is resumed on the next invocation with the next eligible TODO item. If no existing task IDs are present in the state file, the worker remains idle and logs that it will not create a new task. The startup validation task is an exception used only when explicitly requested to prove that scaled concurrency can safely use the API identity; it is not added to worker state.

## State and recovery

The state file contains only already-created task IDs and non-secret roadmap metadata. If the worker process or host restarts, the next invocation reloads the active task list and resumes polling. If a persisted state file contains more than ten entries, the worker retains the first ten and rewrites the state file at the configured limit. API errors leave active records intact so a later invocation can retry status checks.

A task that reports `stopped` is not removed. Instead, the worker selects the next unchecked TODO item and sends a follow-up message to the same task ID through the Manus continuation API. If no eligible item exists, the task remains recorded and the worker logs an idle state. The delegated task is responsible for changing its TODO item from `[-]` to `[x]` or `[!]`; the worker never performs that roadmap mutation because it cannot independently verify the delegated implementation's acceptance criteria.

## Validation

Run the focused worker checks with:

```powershell
python -m pytest -q tests/test_orville_manus_worker.py
python -m py_compile tools/orville_manus_worker.py tests/test_orville_manus_worker.py
```

Tests use synthetic environment values and mocked API boundaries. They do not contact Manus or use production credentials.

## Known limitations

The worker polls Manus task status rather than receiving a provider webhook. It treats `stopped` as the signal that a follow-up turn may be sent and does not independently inspect delegated repository changes. A task-detail HTTP 404 is logged with the worker slot's task ID and exact polling URL, then skipped so the other task slots continue processing. The state file must be populated with the designated task IDs; task discovery and ordinary new-task creation are disabled. The opt-in startup gate performs only its single harmless validation create and never adds that diagnostic task to the worker state. IDs are only considered live after a read-only `task.detail` check under the scheduled worker's API identity; this local dry-run verifies loading and persistence but cannot prove remote task validity. The allowlist is `Worker Task 1` through `Worker Task 10`. The worker requires a persistent host; the default ephemeral sandbox is not a suitable long-running deployment target.
