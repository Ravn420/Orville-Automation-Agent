from __future__ import annotations

import unittest

from orville_core import AutomationSpec, ContractError, WorkloadClassification, classify_workload


class WorkloadClassificationTests(unittest.TestCase):
    def test_classifies_the_five_supported_workload_types(self) -> None:
        cases = (
            (AutomationSpec(objective="run once", trigger_type="manual"), "one_shot"),
            ({"trigger_type": "schedule", "trigger_config": {"expression": "0 * * * *"}}, "recurring"),
            ({"trigger_type": "event", "trigger_config": {"source": "queue"}}, "event_triggered"),
            ({"trigger_type": "webhook", "trigger_config": {"source": "git", "signature": "hmac"}}, "webhook_driven"),
            ({"trigger_type": "manual", "requires_persistent_runtime": True}, "persistent_service"),
        )
        for specification, expected in cases:
            with self.subTest(expected=expected):
                result = classify_workload(specification)
                self.assertIsInstance(result, WorkloadClassification)
                self.assertEqual(result.workload_type, expected)
                self.assertTrue(result.required_fields)

    def test_persistent_runtime_takes_precedence_over_trigger(self) -> None:
        result = classify_workload({
            "trigger_type": "schedule",
            "trigger_config": {"expression": "*/5 * * * *"},
            "requires_persistent_runtime": True,
        })
        self.assertEqual(result.workload_type, "persistent_service")
        self.assertIn("health checks", result.required_fields)

    def test_explicit_type_must_agree_with_inferred_type(self) -> None:
        result = classify_workload({
            "trigger_type": "webhook",
            "trigger_config": {"source": "git"},
            "workload_type": "webhook_driven",
        })
        self.assertEqual(result.to_dict()["workload_type"], "webhook_driven")
        with self.assertRaisesRegex(ContractError, "conflicts"):
            classify_workload({"trigger_type": "schedule", "workload_type": "one_shot"})

    def test_unsupported_trigger_and_workload_fail_closed(self) -> None:
        with self.assertRaisesRegex(ContractError, "unsupported trigger"):
            classify_workload({"trigger_type": "unknown"})
        with self.assertRaisesRegex(ContractError, "unsupported workload"):
            classify_workload({"trigger_type": "manual", "workload_type": "continuous"})

    def test_classification_does_not_execute_side_effects(self) -> None:
        result = classify_workload({"trigger_type": "data", "trigger_config": {"source": "local-file"}})
        self.assertEqual(result.workload_type, "event_triggered")
        self.assertEqual(result.to_dict()["required_fields"], ["event source", "deduplication key"])


if __name__ == "__main__":
    unittest.main()
