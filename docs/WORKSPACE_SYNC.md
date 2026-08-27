# Attached Workspace Synchronization Rules

The attached Windows workspace is the authoritative working tree for source changes. Sandbox artifacts are temporary execution outputs and must not overwrite source files automatically. Changes produced in the sandbox may be synchronized to the attached workspace only when the target path is inside the confirmed repository root and the change is explicitly part of the active task.

Synchronization is one-way by default: reviewed source and documentation changes move to the attached workspace; generated logs, caches, credentials, `.env` files, private keys, browser state, and temporary artifacts never move into the repository. Preserve UTF-8 text, repository line-ending conventions, executable bits where supported, and relative paths portable to Windows and POSIX environments.

Before copying a file, compare its expected checksum and reject stale writes. Never merge silently when both sides changed; preserve both versions or stop for review. After synchronization, inspect `git diff`, run the repository’s platform-appropriate tests, and verify that no secret path or credential-shaped value was introduced. Do not delete unrelated files or clean the workspace destructively.

The synchronization record must include source and destination roots, changed paths, checksums, validation commands, and any skipped or conflicted files. If the attached workspace is unavailable, keep work in the sandbox and report the unsynchronized state rather than using an unverified alternate path.
