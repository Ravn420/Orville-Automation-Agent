"""Roadmap normalization checks for broad phases and implementation increments."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_provider_and_media_increments_are_separate() -> None:
    payload = json.loads((ROOT / "config/roadmap-phase-increments.json").read_text(encoding="utf-8"))
    increments = {
        item["id"]: item
        for phase in payload["phases"]
        for item in phase["increments"]
    }
    assert increments["phase-2.7"]["label"] == "Model Provider Integration"
    assert increments["phase-6.2"]["label"] == "Image, audio, and video"
    assert increments["phase-2.7"]["id"] != increments["phase-6.2"]["id"]


def test_phase_three_contains_reliability_increments_only() -> None:
    payload = json.loads((ROOT / "config/roadmap-phase-increments.json").read_text(encoding="utf-8"))
    phase_three = next(phase for phase in payload["phases"] if phase["id"] == "phase-3")
    labels = {item["label"] for item in phase_three["increments"]}
    assert labels == {"Runtime health", "Connector management", "Cloud and Local Model Endpoints"}
    assert all("provider" not in label.lower() and "media" not in label.lower() for label in labels)


def test_todo_item_records_the_mapping_evidence() -> None:
    todo = (ROOT / "TODO.md").read_text(encoding="utf-8")
    line = next(line for line in todo.splitlines() if "Split broad phase labels" in line)
    assert line.startswith("- [-] Split broad phase labels")
    assert "Phase 2 provider work" in line
    assert "Phase 3 media work" in line
