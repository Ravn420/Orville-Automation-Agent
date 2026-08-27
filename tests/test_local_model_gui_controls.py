from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROL_CENTER = ROOT / "docs" / "mockups" / "orville-control-center.html"
GENERATION = ROOT / "docs" / "mockups" / "generation-workspace.html"
MODEL_CONFIG = ROOT / "docs" / "mockups" / "model-configuration.html"


def test_broader_gui_exposes_local_model_selection():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in (CONTROL_CENTER, GENERATION, MODEL_CONFIG))
    for marker in ("local-model-select", "Local model · llama3.2", 'value="local_catalog"', "localFilter", "Select for generation"):
        assert marker in combined


def test_signal_room_exposes_explicit_local_model_lifecycle_controls():
    text = CONTROL_CENTER.read_text(encoding="utf-8")
    for marker in (
        'id="activate-local-model"',
        'id="pause-local-model"',
        'id="resume-local-model"',
        'id="choose-local-model"',
        "explicit approval is required",
        "remains resumable",
    ):
        assert marker in text


def test_generation_workspace_preserves_review_only_boundary():
    text = GENERATION.read_text(encoding="utf-8")
    for marker in ("model-lifecycle-status", "Activation requested", "No task has executed", "Local models only"):
        assert marker in text
