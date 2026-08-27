#!/usr/bin/env python3
"""Local executor for the first bounded TODO-autopilot task.

The executor intentionally accepts only the repository and prompt arguments
needed by ``todo_autopilot.py``. It performs no network, credential, publish,
deploy, or TODO.md operation.
"""
from __future__ import annotations

import argparse
from pathlib import Path


MEMORY_DOC = """# Memory Governance

## Purpose

This document defines the boundaries for task memory and long-term project memory. It is a policy artifact, not a storage implementation, and it does not authorize retaining secrets or user data.

## Short-term task memory

Short-term task memory contains only the minimum context required to complete the active task: the current request, user-approved constraints, selected repository paths, relevant validation output, and unresolved risks. It is scoped to the active task thread and is discarded when the task closes unless the user explicitly requests a sanitized handoff record.

Credentials, access tokens, private keys, browser cookies, raw authentication headers, and unrelated personal data are never eligible for short-term memory. Diagnostics must use references, redaction, and hashes rather than secret values.

## Long-term project memory

Long-term project memory contains durable project facts that remain useful across task turns: architecture decisions, approved operating constraints, dependency relationships, evidence locations, known blockers, and completed milestone records. It is stored only in reviewed project control files or explicitly approved project artifacts.

Long-term memory must not become a transcript archive. Raw prompts, full tool output, secrets, private user content, and transient scratch data are excluded unless a separate retention decision explicitly permits a sanitized excerpt.

## Retention and deletion

Each memory record has an owner, purpose, creation date, retention class, and deletion condition. Task-scoped context expires at task closure. Evidence records persist only for the project retention period or until the corresponding milestone is superseded. Deletion requests remove the applicable project-memory record and its derived copies, subject to a documented legal or audit hold.

Deletion is fail-closed: an incomplete deletion operation is reported as unresolved and does not claim completion. Backups, caches, logs, and generated artifacts must be included in the deletion inventory.

## Isolation

Memory is isolated by project, task thread, user authorization, and sensitivity class. A task may read only the project files and evidence required by its acceptance criteria. Memory from another project or user is not imported by default. Cross-project reuse requires an explicit, sanitized handoff reference.

## User editing and auditability

Users may inspect and edit project-memory policy records through reviewed project controls. Every edit records the actor, reason, timestamp, affected record, and resulting revision. User edits cannot bypass secret redaction, scope isolation, retention deletion, or approval gates.

## Acceptance rule

No memory feature is complete until the scope, retention, deletion, isolation, user-editing, secret-exclusion, and audit requirements are documented and covered by focused validation.
"""

TEST = '''"""Contract checks for memory-governance boundaries."""

from pathlib import Path


DOC = Path(__file__).resolve().parents[1] / "docs" / "MEMORY_GOVERNANCE.md"


def test_memory_governance_covers_required_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8").lower()
    for phrase in (
        "short-term task memory",
        "long-term project memory",
        "retention",
        "deletion",
        "isolation",
        "user editing",
        "credentials",
        "auditability",
    ):
        assert phrase in text


def test_memory_governance_is_explicitly_fail_closed() -> None:
    text = DOC.read_text(encoding="utf-8").lower()
    assert "fail-closed" in text
    assert "never eligible" in text
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()
    if "TODO-3108982ea7c3" not in args.prompt:
        raise SystemExit("executor is restricted to TODO-3108982ea7c3")
    repo = args.repo.resolve()
    (repo / "docs" / "MEMORY_GOVERNANCE.md").write_text(MEMORY_DOC, encoding="utf-8")
    (repo / "tests" / "test_memory_governance.py").write_text(TEST, encoding="utf-8")
    state = repo / "STATE.md"
    state_text = state.read_text(encoding="utf-8")
    marker = "**Memory governance checkpoint — 2026-08-27:**"
    if marker not in state_text:
        state_text = state_text.replace(
            "**M14.8 control-plane checkpoint — 2026-08-27:**",
            marker + " `docs/MEMORY_GOVERNANCE.md` defines short-term and long-term memory scope, retention, deletion, isolation, user editing, secret exclusion, and auditability. Focused memory-governance tests are included; no memory backend or user data was changed.\n\n**M14.8 control-plane checkpoint — 2026-08-27:**",
            1,
        )
        state.write_text(state_text, encoding="utf-8")
    changelog = repo / "CHANGELOG.md"
    changelog_text = changelog.read_text(encoding="utf-8")
    section = "## 2026-08-27 — Memory governance task\n\n### Added\n\n- Added `docs/MEMORY_GOVERNANCE.md` and focused contract tests defining short-term and long-term memory scope, retention, deletion, isolation, user editing, secret exclusion, and auditability. No memory backend or user data was changed.\n\n"
    if "## 2026-08-27 — Memory governance task" not in changelog_text:
        changelog.write_text(section + changelog_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
