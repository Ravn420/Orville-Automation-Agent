from __future__ import annotations

from orville_core.wide_research import ResearchItem, WideResearchRunner


def test_wide_research_runs_items_and_persists_resume(tmp_path):
    runner = WideResearchRunner(tmp_path / "research.json", max_workers=3)
    items = [ResearchItem("one", "One"), ResearchItem("two", "Two"), ResearchItem("three", "Three")]
    calls = []
    def worker(item):
        calls.append(item.item_id)
        return {"answer": item.prompt.lower(), "sources": [{"url": f"https://example.com/{item.item_id}"}]}
    summary = runner.run(items, worker, job_id="job-1")
    assert summary.completed == 3
    assert all(result.sources for result in summary.results)
    calls.clear()
    resumed = runner.run(items, worker, job_id="job-1")
    assert resumed.completed == 3
    assert calls == []


def test_wide_research_isolates_failures_and_retries(tmp_path):
    runner = WideResearchRunner(tmp_path / "research.json", max_workers=2, max_attempts=2)
    attempts = {"bad": 0}
    def worker(item):
        if item.item_id == "bad":
            attempts["bad"] += 1
            raise RuntimeError("fixture failure")
        return {"answer": "ok"}
    summary = runner.run([ResearchItem("bad", "Bad"), ResearchItem("good", "Good")], worker)
    assert summary.failed == 1
    assert summary.completed == 1
    assert attempts["bad"] == 2
