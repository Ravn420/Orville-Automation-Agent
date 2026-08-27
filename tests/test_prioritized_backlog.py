"""Focused contract tests for the prioritized backlog."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "config" / "priority-backlog.json"
DOC = ROOT / "docs" / "PRIORITIZED_BACKLOG.md"


def _load() -> dict:
    return json.loads(BACKLOG.read_text(encoding="utf-8"))


def test_backlog_has_unique_existing_roadmap_records_and_valid_scores() -> None:
    data = _load()
    items = data["items"]
    assert len(items) >= 3
    assert len({item["id"] for item in items}) == len(items)
    for item in items:
        assert item["todo_text"]
        assert item["owner"]
        assert item["status"] in {"planned", "in_progress", "blocked", "completed"}
        assert item["priority"] in {"critical", "high", "medium", "low", "deferred"}
        assert 1 <= item["impact"] <= 4
        assert 1 <= item["effort"] <= 4
        assert 1 <= item["risk"] <= 4
        assert item["dependencies"]
        assert item["acceptance_test"]
        assert item["acceptance_evidence"]
        assert item["artifact_reference"]
        for reference in item["artifact_reference"]:
            assert (ROOT / reference).exists()
        if item["status"] == "blocked":
            assert item.get("blocker")


def test_backlog_items_match_todo_wording_and_documented_contract() -> None:
    data = _load()
    todo = (ROOT / "TODO.md").read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    for item in data["items"]:
        assert item["todo_text"] in todo
    for term in ("impact", "effort", "risk", "owner", "dependencies", "acceptance_test", "acceptance_evidence", "artifact_reference", "dependency", "blocker"):
        assert term in doc
    assert "credentials" not in BACKLOG.read_text(encoding="utf-8").lower()


def test_backlog_defines_dependency_and_blocker_priority_overrides() -> None:
    data = _load()
    assert "priority_rule" in data["scoring"]
    assert "dependencies and blockers override the score" in data["scoring"]["priority_rule"]
    assert any(item["status"] == "blocked" and item.get("blocker") for item in data["items"])
