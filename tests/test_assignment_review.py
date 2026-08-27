"""Focused tests for agent-assignment performance review."""

from orville_core.assignment_review import review_assignment_performance


def _run(*tasks: dict) -> dict:
    return {"run_status": "completed", "tasks": list(tasks)}


def test_assignment_review_aggregates_outcomes_without_ranking_agents() -> None:
    report = review_assignment_performance(
        [
            _run(
                {"agent": "research", "status": "verified", "attempts": 1, "duration_seconds": 2.0},
                {"owner": "coding", "status": "failed", "attempts": 2, "duration_seconds": 4.0, "verification_failed": True},
            ),
            _run({"agent": "research", "status": "completed", "attempts": 2, "duration_seconds": 4.0}),
        ]
    )
    assert report["considered_runs"] == 2
    assert report["considered_tasks"] == 3
    assert report["assignment_count"] == 2
    research = next(row for row in report["assignments"] if row["agent"] == "research")
    coding = next(row for row in report["assignments"] if row["agent"] == "coding")
    assert research["completed"] == 2
    assert research["failure_rate"] == 0.0
    assert research["attempts_mean"] == 1.5
    assert coding["failed"] == 1
    assert coding["verification_failures"] == 1
    assert "reassign" not in report["recommendation"].lower()


def test_assignment_review_is_secret_safe_and_ignores_nonterminal_runs() -> None:
    report = review_assignment_performance(
        [
            {"run_status": "running", "tasks": [{"agent": "ignored", "status": "failed"}]},
            _run({"status": "blocked", "details": {"agent": "fallback"}, "task_id": "secret-path"}),
            _run({"status": "verified", "agent": "  local  ", "duration_seconds": 1.0}),
        ]
    )
    assert report["considered_runs"] == 2
    assert report["considered_tasks"] == 2
    assert {row["agent"] for row in report["assignments"]} == {"fallback", "local"}
    assert "secret-path" not in str(report)


def test_assignment_review_bounds_input_and_normalizes_labels() -> None:
    long_agent = "a" * 200
    report = review_assignment_performance([_run({"agent": long_agent, "status": "verified", "attempts": -1, "duration_seconds": -1})])
    assert report["assignments"][0]["agent"] == "a" * 96
    assert report["assignments"][0]["attempts_mean"] == 0.0
    assert report["assignments"][0]["duration_mean"] == 0.0
