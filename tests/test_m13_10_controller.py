from orville_core import CanaryCohort, CanaryPolicy, CanaryPolicyError, DurableCanaryController, HealthEvaluator, HealthThresholds, HealthWindow, RollbackLimits


class FakeAdapter:
    def __init__(self):
        self.calls = []

    def deploy(self, release_id):
        self.calls.append(("deploy", release_id))

    def set_traffic(self, release_id, traffic_percent):
        self.calls.append(("traffic", release_id, traffic_percent))

    def rollback(self, release_id, target):
        self.calls.append(("rollback", release_id, target))

    def quarantine(self, release_id):
        self.calls.append(("quarantine", release_id))


def policy():
    return CanaryPolicy(
        policy_id="p1",
        release_id="r1",
        rollback_target="good",
        cohorts=(CanaryCohort("internal", 1, hold_seconds=1), CanaryCohort("full", 100, hold_seconds=1)),
        health=HealthThresholds(min_samples=10, max_error_rate=0.05),
        rollback=RollbackLimits(max_attempts=2),
        max_hold_seconds=10,
        observation_window_seconds=1,
    )


def window(**overrides):
    values = dict(release_id="r1", cohort="internal", samples=10, error_rate=0.01, p95_latency_ms=10, p99_latency_ms=20, saturation_ratio=0.1, observed_seconds=1)
    values.update(overrides)
    return HealthWindow(**values)


def test_controller_progresses_and_recovers_from_restart(tmp_path):
    adapter = FakeAdapter()
    path = tmp_path / "canary.json"
    controller = DurableCanaryController(path, adapter)
    assert controller.start(policy()).state == "observing"
    assert controller.observe(policy(), window()).state == "observing"
    restarted = DurableCanaryController(path, adapter)
    assert restarted.state.cohort_index == 1
    assert restarted.observe(policy(), window(cohort="full")).state == "completed"
    assert ("traffic", "r1", 100) in adapter.calls


def test_health_evaluator_pauses_for_insufficient_samples_and_rolls_back_on_error():
    evaluator = HealthEvaluator()
    paused = evaluator.evaluate(policy(), window(samples=1), expected_release="r1", expected_cohort="internal")
    assert paused.outcome == "pause"
    assert "insufficient_samples" in paused.reasons
    rollback = evaluator.evaluate(policy(), window(error_rate=0.9), expected_release="r1", expected_cohort="internal")
    assert rollback.outcome == "rollback"
    assert "error_rate_threshold_exceeded" in rollback.reasons


def test_controller_bounds_rollback_attempts(tmp_path):
    adapter = FakeAdapter()
    controller = DurableCanaryController(tmp_path / "canary.json", adapter)
    controller.start(policy())
    controller.observe(policy(), window(error_rate=0.9))
    assert controller.state.state == "rolled_back"
    assert controller.state.rollback_attempts == 1
    assert len([call for call in adapter.calls if call[0] == "rollback"]) == 1
