"""Focused tests for completed-task-graph failure-pattern review."""

from orville_core.failure_patterns import review_completed_task_graphs


def _run(run_id: str, *events: dict) -> dict:
    return {"run_id": run_id, "run_status": "completed", "events": list(events)}


def test_repeated_failure_patterns_are_aggregated_across_runs() -> None:
    report = review_completed_task_graphs(
        [
            _run("r1", {"event_type": "task_failed", "task_id": "a", "details": {"failure_class": "Provider Timeout"}}),
            _run("r2", {"event_type": "task_failed", "task_id": "b", "details": {"failure_class": "Provider Timeout"}}),
        ]
    )
    assert report["completed_runs"] == 2
    assert report["failure_event_count"] == 2
    assert report["repeated_pattern_count"] == 1
    assert report["patterns"] == [{
        "pattern": "task_failed:provider_timeout",
        "count": 2,
        "run_count": 2,
        "task_count": 2,
        "event_types": ["task_failed"],
    }]


def test_nonterminal_runs_and_nonfailure_events_do_not_create_patterns() -> None:
    report = review_completed_task_graphs(
        [
            {"run_id": "running", "run_status": "running", "events": [{"event_type": "task_failed"}]},
            _run("r1", {"event_type": "task_started", "task_id": "a"}),
            _run("r2", {"event_type": "task_failed", "task_id": "a", "details": {"error": "TimeoutError: secret-value"}}),
        ]
    )
    assert report["completed_runs"] == 2
    assert report["failure_event_count"] == 1
    assert report["repeated_pattern_count"] == 0
    assert "secret-value" not in str(report)


def test_threshold_and_limits_are_bounded() -> None:
    runs = [_run(str(index), {"event_type": "task_blocked", "task_id": "x"}) for index in range(3)]
    assert review_completed_task_graphs(runs, minimum_occurrences=4)["patterns"] == []
    assert len(review_completed_task_graphs(runs, max_patterns=1)["patterns"]) <= 1
