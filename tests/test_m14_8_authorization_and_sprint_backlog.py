"""Contract checks for M14.8 authorization and upcoming-sprint planning artifacts."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = ROOT / "docs" / "M14_8_CHANGE_WINDOW_AUTHORIZATION_TEMPLATE.md"
SPRINT_BACKLOG = ROOT / "docs" / "UPCOMING_SPRINT_BACKLOG.md"


def test_m14_8_authorization_template_requires_scoped_approvals_and_live_evidence() -> None:
    text = AUTHORIZATION.read_text(encoding="utf-8")
    for phrase in (
        "This is a request template, not an authorization.",
        "M14.1 environment and responsibility matrix",
        "M14.2 trust root",
        "M14.3 sandbox",
        "M14.4 identity",
        "M14.5 secrets",
        "M14.6 provider adapter",
        "M14.7 metrics",
        "Fault-Injection Authorization Matrix",
        "Automatic stop conditions",
        "Authorization Decision Record",
        "no production action, route, tenant, credential, or customer data was used",
    ):
        assert phrase in text
    assert not re.search(r"(?i)sk-[A-Za-z0-9]{12,}|Bearer\s+[A-Za-z0-9._-]{8,}|api[_-]?key\s*=\s*[^\s,]+", text)


def test_upcoming_sprint_backlog_preserves_active_ownership_and_external_gates() -> None:
    text = SPRINT_BACKLOG.read_text(encoding="utf-8")
    for phrase in (
        "437 open",
        "13 in-progress",
        "14 blocked",
        "TODO-175df4cecc51",
        "TODO-2b113eb0e255",
        "TODO-45ea939505f7",
            "do not create a competing implementation.",
        "no live drill is authorized by this plan",
        "M14.2–M14.7 evidence",
        "Durable Task-Thread Vertical Slice",
    ):
        assert phrase in text
