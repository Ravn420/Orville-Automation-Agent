from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).parents[1] / "tools" / "orville_manus_worker.py"
spec = importlib.util.spec_from_file_location("orville_manus_worker_continuous", MODULE_PATH)
worker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(worker)


def test_continuous_mode_runs_bounded_cycles(tmp_path, monkeypatch):
    (tmp_path / "TODO.md").write_text("- [ ] item\n", encoding="utf-8")
    calls = []
    sleeps = []

    def fake_run_once(repo, **kwargs):
        calls.append((repo, kwargs))
        return 0

    monkeypatch.setattr(worker, "run_once", fake_run_once)
    result = worker.run_continuously(
        tmp_path,
        interval_seconds=0.25,
        max_active_tasks=3,
        max_retries=2,
        lease_seconds=600,
        max_cycles=3,
        sleep_fn=sleeps.append,
    )

    assert result == 0
    assert len(calls) == 3
    assert sleeps == [0.25, 0.25]
    assert all(call[1]["max_active_tasks"] == 3 for call in calls)


def test_continuous_mode_stops_after_signal_request(tmp_path, monkeypatch):
    (tmp_path / "TODO.md").write_text("- [ ] item\n", encoding="utf-8")
    calls = []

    def fake_run_once(repo, **kwargs):
        calls.append(repo)
        return 0

    def sleep_and_request(_seconds):
        handler = worker.signal.getsignal(worker.signal.SIGINT)
        handler(worker.signal.SIGINT, None)

    monkeypatch.setattr(worker, "run_once", fake_run_once)
    result = worker.run_continuously(tmp_path, interval_seconds=1, sleep_fn=sleep_and_request)

    assert result == 0
    assert len(calls) == 1


def test_continuous_mode_rejects_invalid_bounds(tmp_path):
    (tmp_path / "TODO.md").write_text("- [ ] item\n", encoding="utf-8")

    for kwargs, expected in [
        ({"interval_seconds": -1}, "interval_seconds"),
        ({"max_cycles": 0}, "max_cycles"),
    ]:
        try:
            worker.run_continuously(tmp_path, **kwargs)
        except ValueError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"expected {expected} validation error")
