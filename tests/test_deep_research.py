import json

import pytest

from orville_core.deep_research import DeepResearchEngine, ResearchConfig, ResearchSource


def search(query: str, limit: int):
    assert query == "compare local orchestration"
    return [
        {"url": "https://example.com/one", "title": "One", "snippet": "First finding"},
        {"url": "javascript:alert(1)", "title": "Unsafe", "snippet": "Ignore"},
        {"url": "https://example.com/two", "title": "Two", "snippet": "Second finding"},
    ][:limit]


def fetch(url: str, limit: int):
    return f"Fetched evidence from {url}."[:limit]


def test_deep_research_runs_bounded_stages_and_report():
    run = DeepResearchEngine(search, fetch).run(
        " compare   local orchestration ",
        config=ResearchConfig(max_sources=3, max_excerpt_chars=400, provider_name="local"),
    )
    assert run.status == "completed"
    assert run.stage == "report"
    assert len(run.sources) == 2
    assert "## Findings" in run.report
    assert "## Sources" in run.report
    assert run.to_dict()["privacy"]["query_leaves_local_boundary"] is False


def test_unconfigured_engine_fails_closed_without_fake_results():
    run = DeepResearchEngine().run("research this")
    assert run.status == "blocked"
    assert run.stage == "search"
    assert run.sources == []
    assert run.report == ""
    assert "No search provider" in run.errors[0]


def test_empty_search_is_visible_blocker():
    run = DeepResearchEngine(lambda _query, _limit: []).run("research this")
    assert run.status == "blocked"
    assert "no verified" in run.errors[0].lower()


def test_source_records_are_safe_and_content_is_not_persisted_in_summary():
    source = ResearchSource("https://example.com", "Example", content="private body")
    value = source.to_dict()
    assert value["source_id"]
    assert "content" not in value


def test_config_bounds_are_enforced():
    with pytest.raises(ValueError):
        ResearchConfig(max_sources=0)
    with pytest.raises(ValueError):
        ResearchConfig(max_excerpt_chars=100)
    with pytest.raises(ValueError):
        ResearchConfig(report_format="html")


def test_json_serializable_run():
    run = DeepResearchEngine(lambda _query, _limit: [{"url": "https://example.com", "title": "Example", "snippet": "ok"}]).run("x")
    json.dumps(run.to_dict())
