# Roadmap Task Identifiers

Every actionable TODO checklist item in `TODO.md` carries an inline marker in the form `<!-- task-id:TODO-xxxxxxxxxxxx -->`, where the suffix is twelve lowercase hexadecimal characters. The marker is machine-readable, remains on the same checklist line, and does not alter the human-readable task text or status marker.

Identifiers are generated deterministically from the checklist body using SHA-1 truncated to twelve hexadecimal characters. If identical bodies occur, the occurrence number is included in the digest input to preserve uniqueness. Existing valid markers are preserved exactly, making regeneration idempotent.

The identifier utility is `tools/assign_todo_ids.py`:

```text
python tools/assign_todo_ids.py TODO.md --write
```

The command is local-only and does not use credentials, network access, Git operations, or external services. It updates only checklist records and reports the number of identified records and changed lines. TODO automation can continue to parse the existing status prefix because the marker is appended after the task text.

Validation is provided by `tests/test_todo_identifiers.py`, which verifies that all checklist records have valid unique identifiers, regeneration is idempotent, and status markers and task text are preserved. The roadmap automation regression tests additionally confirm compatibility with existing selection behavior.
