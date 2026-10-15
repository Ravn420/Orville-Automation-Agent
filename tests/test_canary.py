from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from orville_core.canary import CanaryController, CanaryHealthEvaluator, CanaryStateStore, CanaryError, HealthObservation, SyntheticDeploymentAdapter
from orville_core.canary_policy import CanaryCohort, CanaryPolicy, HealthThresholds, RollbackLimits


def policy() -> CanaryPolicy:
    return CanaryPolicy(release_id="release-2", rollback_target="release-1", cohorts=(CanaryCohort("canary", 10, hold_seconds=1), CanaryCohort("full", 100, hold_seconds=1)), health=HealthThresholds(min_samples=10, max_error_rate=0.1))


def m14_8_policy() -> CanaryPolicy:
    """M14.8 canonical canary policy with 1% → 10% → 50% → 100% traffic progression."""
    return CanaryPolicy(
        policy_id="m14-8-canary-v1",
        release_id="release-candidate",
        rollback_target="release-stable",
        cohorts=(
            CanaryCohort("canary-1pct", 1, hold_seconds=1),
            CanaryCohort("canary-10pct", 10, hold_seconds=1),
            CanaryCohort("canary-50pct", 50, hold_seconds=1),
            CanaryCohort("full", 100, hold_seconds=1),
        ),
        health=HealthThresholds(
            min_samples=100,
            max_error_rate=0.02,
            max_p95_latency_ms=1000.0,
            max_p99_latency_ms=2000.0,
            max_saturation_ratio=0.90,
            critical_security_findings=0,
            min_business_health=0.95,
        ),
        rollback=RollbackLimits(
            max_attempts=3,
            timeout_seconds=300,
            quarantine_seconds=3600,
            require_known_good_target=True,
            pause_on_critical_security=True,
        ),
        approval_mode="per_step",
        observation_window_seconds=300,
    )


class CanaryTests(unittest.TestCase):
    def test_health_evaluator_fails_closed_for_sparse_or_security_bad_data(self):
        decision = CanaryHealthEvaluator().evaluate(policy(), HealthObservation(1, 0, 1, 1, 0, observed_at=1, release_id="release-2"))
        self.assertFalse(decision.passed)
        self.assertIn("insufficient_samples", decision.reasons)
        decision = CanaryHealthEvaluator().evaluate(policy(), HealthObservation(10, 0, 1, 1, 0, 1, observed_at=1, release_id="release-2"))
        self.assertIn("critical_security_findings", decision.reasons)

    def test_controller_is_durable_approval_gated_and_idempotent(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = CanaryStateStore(Path(directory) / "canary.db")
            adapter = SyntheticDeploymentAdapter()
            controller = CanaryController(store, adapter)
            run_id = controller.start(policy())
            controller.deploy(run_id)
            observation = HealthObservation(10, 0, 1, 1, 0, observed_at=1, release_id="release-2")
            awaiting = controller.observe(run_id, observation)
            self.assertEqual(awaiting["state"], "awaiting_approval")
            observing = controller.observe(run_id, observation, approval=True)
            self.assertEqual(observing["state"], "observing")
            resumed = CanaryController(CanaryStateStore(Path(directory) / "canary.db"), adapter).store.get(run_id)
            self.assertEqual(resumed["cohort_index"], 0)
            controller.rollback(run_id, "test")
            self.assertEqual(controller.rollback(run_id, "duplicate")["state"], "rolled_back")
            events = store.audit_events(run_id)
            self.assertTrue(all("token" not in event["metadata"] for event in events))

    def test_mismatched_release_is_rejected_and_critical_security_pauses(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = CanaryStateStore(Path(directory) / "canary.db")
            adapter = SyntheticDeploymentAdapter()
            controller = CanaryController(store, adapter)
            run_id = controller.start(policy())
            controller.deploy(run_id)
            bad = HealthObservation(10, 0, 1, 1, 0, observed_at=1, release_id="wrong")
            self.assertIn("observation_release_mismatch", controller.observe(run_id, bad)["last_decision"]["reasons"])

    def test_m14_8_traffic_progression_1_10_50_100(self):
        """M14.8: Verify 1% → 10% → 50% → 100% traffic progression with health gates."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = CanaryStateStore(Path(directory) / "canary.db")
            adapter = SyntheticDeploymentAdapter()
            controller = CanaryController(store, adapter)
            run_id = controller.start(m14_8_policy())
            controller.deploy(run_id)

            # Healthy observation at each stage
            healthy = HealthObservation(
                samples=100, error_rate=0.01, p95_latency_ms=500, p99_latency_ms=1000,
                saturation_ratio=0.5, business_health=0.98, observed_at=1, release_id="release-candidate"
            )

            # Stage 1: 1% traffic (awaiting approval)
            state = controller.observe(run_id, healthy)
            self.assertEqual(state["state"], "awaiting_approval")
            self.assertEqual(state["cohort_index"], -1)

            # Approve and advance to 1%
            state = controller.observe(run_id, healthy, approval=True)
            self.assertEqual(state["state"], "observing")
            self.assertEqual(state["cohort_index"], 0)
            self.assertEqual(adapter.releases["release-candidate"]["traffic_percent"], 1)

            # Stage 2: 10% traffic
            state = controller.observe(run_id, healthy, approval=True)
            self.assertEqual(state["state"], "observing")
            self.assertEqual(state["cohort_index"], 1)
            self.assertEqual(adapter.releases["release-candidate"]["traffic_percent"], 10)

            # Stage 3: 50% traffic
            state = controller.observe(run_id, healthy, approval=True)
            self.assertEqual(state["state"], "observing")
            self.assertEqual(state["cohort_index"], 2)
            self.assertEqual(adapter.releases["release-candidate"]["traffic_percent"], 50)

            # Stage 4: 100% traffic
            state = controller.observe(run_id, healthy, approval=True)
            self.assertEqual(state["state"], "observing")
            self.assertEqual(state["cohort_index"], 3)
            self.assertEqual(adapter.releases["release-candidate"]["traffic_percent"], 100)

            # Final observation to complete the canary
            state = controller.observe(run_id, healthy, approval=True)
            self.assertEqual(state["state"], "completed")

    def test_m14_8_automatic_rollback_on_health_threshold_violations(self):
        """M14.8: Verify automatic rollback triggers on severe health violations."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = CanaryStateStore(Path(directory) / "canary.db")
            adapter = SyntheticDeploymentAdapter()
            controller = CanaryController(store, adapter)
            run_id = controller.start(m14_8_policy())
            controller.deploy(run_id)

            healthy = HealthObservation(
                samples=100, error_rate=0.01, p95_latency_ms=500, p99_latency_ms=1000,
                saturation_ratio=0.5, business_health=0.98, observed_at=1, release_id="release-candidate"
            )

            # Advance to 10% traffic
            controller.observe(run_id, healthy, approval=True)  # 1%
            controller.observe(run_id, healthy, approval=True)  # 10%
            self.assertEqual(adapter.releases["release-candidate"]["traffic_percent"], 10)

            # Inject high error rate - should trigger automatic rollback
            unhealthy = HealthObservation(
                samples=100, error_rate=0.10, p95_latency_ms=500, p99_latency_ms=1000,
                saturation_ratio=0.5, business_health=0.98, observed_at=2, release_id="release-candidate"
            )
            state = controller.observe(run_id, unhealthy)
            self.assertEqual(state["state"], "rolled_back")
            self.assertEqual(adapter.releases["release-candidate"]["traffic_percent"], 0)

            # Verify rollback audit event
            events = store.audit_events(run_id)
            rollback_events = [e for e in events if e["event"] == "canary.rollback"]
            self.assertEqual(len(rollback_events), 1)
            self.assertEqual(rollback_events[0]["outcome"], "completed")

    def test_m14_8_health_evaluation_all_thresholds(self):
        """M14.8: Verify health evaluation covers all required metrics."""
        evaluator = CanaryHealthEvaluator()
        policy = m14_8_policy()

        # Test error rate threshold
        obs = HealthObservation(
            samples=100, error_rate=0.05, p95_latency_ms=500, p99_latency_ms=1000,
            saturation_ratio=0.5, business_health=0.98, observed_at=1, release_id="release-candidate"
        )
        decision = evaluator.evaluate(policy, obs)
        self.assertFalse(decision.passed)
        self.assertIn("error_rate_exceeded", decision.reasons)

        # Test p95 latency threshold
        obs = HealthObservation(
            samples=100, error_rate=0.01, p95_latency_ms=1500, p99_latency_ms=2000,
            saturation_ratio=0.5, business_health=0.98, observed_at=1, release_id="release-candidate"
        )
        decision = evaluator.evaluate(policy, obs)
        self.assertFalse(decision.passed)
        self.assertIn("p95_latency_exceeded", decision.reasons)

        # Test p99 latency threshold
        obs = HealthObservation(
            samples=100, error_rate=0.01, p95_latency_ms=500, p99_latency_ms=2500,
            saturation_ratio=0.5, business_health=0.98, observed_at=1, release_id="release-candidate"
        )
        decision = evaluator.evaluate(policy, obs)
        self.assertFalse(decision.passed)
        self.assertIn("p99_latency_exceeded", decision.reasons)

        # Test saturation threshold
        obs = HealthObservation(
            samples=100, error_rate=0.01, p95_latency_ms=500, p99_latency_ms=1000,
            saturation_ratio=0.95, business_health=0.98, observed_at=1, release_id="release-candidate"
        )
        decision = evaluator.evaluate(policy, obs)
        self.assertFalse(decision.passed)
        self.assertIn("saturation_exceeded", decision.reasons)

        # Test business health threshold
        obs = HealthObservation(
            samples=100, error_rate=0.01, p95_latency_ms=500, p99_latency_ms=1000,
            saturation_ratio=0.5, business_health=0.90, observed_at=1, release_id="release-candidate"
        )
        decision = evaluator.evaluate(policy, obs)
        self.assertFalse(decision.passed)
        self.assertIn("business_health_below_minimum", decision.reasons)

        # Test all healthy
        obs = HealthObservation(
            samples=100, error_rate=0.01, p95_latency_ms=500, p99_latency_ms=1000,
            saturation_ratio=0.5, business_health=0.98, observed_at=1, release_id="release-candidate"
        )
        decision = evaluator.evaluate(policy, obs)
        self.assertTrue(decision.passed)
        self.assertEqual(len(decision.reasons), 0)

    def test_m14_8_rollback_authority_and_verification(self):
        """M14.8: Verify rollback authority assignment and verification."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = CanaryStateStore(Path(directory) / "canary.db")
            adapter = SyntheticDeploymentAdapter()
            controller = CanaryController(store, adapter)
            run_id = controller.start(m14_8_policy())
            controller.deploy(run_id)

            # Verify rollback target is recorded
            record = store.get(run_id)
            self.assertEqual(record["policy"]["rollback_target"], "release-stable")

            # Rollback with reason
            state = controller.rollback(run_id, "operator_initiated")
            self.assertEqual(state["state"], "rolled_back")

            # Verify audit trail
            events = store.audit_events(run_id)
            rollback_events = [e for e in events if e["event"] == "canary.rollback"]
            self.assertEqual(len(rollback_events), 1)
            self.assertIn("release-stable", rollback_events[0]["metadata"]["rollback_target"])

            # Verify idempotency - second rollback should not fail
            state = controller.rollback(run_id, "duplicate")
            self.assertEqual(state["state"], "rolled_back")


if __name__ == "__main__":
    unittest.main()
