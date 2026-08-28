from pathlib import Path


GUI_SOURCE = Path(__file__).resolve().parents[1] / "windows_gui.py"


def test_objective_submission_launches_the_live_code_viewer():
    source = GUI_SOURCE.read_text(encoding="utf-8")

    assert "def open_live_code_generation_viewer(self, run_id: str)" in source
    assert "self.open_live_code_generation_viewer(run_id)" in source
    assert '"generation_mode": "code"' in source
    assert '"context": {"stream": True}' in source


def test_live_viewer_polls_persisted_run_output_and_stops_at_terminal_state():
    source = GUI_SOURCE.read_text(encoding="utf-8")

    assert 'f"/api/v1/runs/{quote(run_id, safe=\'\')}"' in source
    assert 'task_output.get("text")' in source
    assert '"completed", "failed", "blocked", "cancelled"' in source
    assert "window.after(750, refresh)" in source
