from orville_core.observability import TraceRecord
from orville_core.trace_comparison import compare_traces


def test_trace_comparison_ignores_volatile_ids_and_timestamps():
    baseline = [TraceRecord("a", "2026-01-01T00:00:00Z", "graph.start", {"run_id": "a", "duration_ms": 10})]
    candidate = [TraceRecord("b", "2026-01-02T00:00:00Z", "graph.start", {"run_id": "b", "duration_ms": 11})]
    result = compare_traces(baseline, candidate)
    assert result.passed


def test_trace_comparison_reports_regression_failures_and_unexpected_tools():
    baseline = [TraceRecord("a", "t", "tool.read", {"duration_ms": 10})]
    candidate = [
        TraceRecord("b", "t", "tool.read", {"duration_ms": 30, "failure": "Timeout"}),
        TraceRecord("b", "t", "tool.read", {"duration_ms": 30, "failure": "Timeout"}),
        TraceRecord("b", "t", "tool.shell", {"duration_ms": 1}),
    ]
    result = compare_traces(baseline, candidate, allowed_tool_calls=("tool.read",))
    assert not result.passed
    assert "candidate total duration regressed" in result.regressions
    assert result.repeated_failure_patterns == {"Timeout": 2}
    assert result.unexpected_tool_calls == ("tool.shell",)
