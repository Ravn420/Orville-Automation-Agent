from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from orville_core.canary import CanaryController, CanaryHealthEvaluator, CanaryStateStore, CanaryError, HealthObservation, SyntheticDeploymentAdapter
from orville_core.canary_policy import CanaryCohort, CanaryPolicy


def policy() -> CanaryPolicy:
    return CanaryPolicy(release_id="release-2", rollback_target="release-1", cohorts=(CanaryCohort("canary", 10, hold_seconds=1), CanaryCohort("full", 100, hold_seconds=1)), health=__import__("orville_core.canary_policy", fromlist=["HealthThresholds"]).HealthThresholds(min_samples=10, max_error_rate=0.1))


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


if __name__ == "__main__":
    unittest.main()
