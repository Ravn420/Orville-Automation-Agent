import os
import unittest

from orville_core.adapters import default_adapter_registry
from orville_core.readiness import ProductionReadiness


class ReadinessTests(unittest.TestCase):
    def test_readiness_reports_local_passes_and_production_blockers(self):
        previous = os.environ.pop("ORVILLE_API_TOKEN", None)
        try:
            report = ProductionReadiness(default_adapter_registry()).evaluate(tests_passed=True, compile_passed=True, required_adapters=(("local-workspace", "revision"), ("browser", "navigate")))
            self.assertFalse(report.ready)
            self.assertIn("api_token", report.blocking_checks)
            self.assertIn("adapter:browser:navigate", report.blocking_checks)
        finally:
            if previous is not None:
                os.environ["ORVILLE_API_TOKEN"] = previous

    def test_configured_token_allows_local_readiness(self):
        previous = os.environ.get("ORVILLE_API_TOKEN")
        os.environ["ORVILLE_API_TOKEN"] = "test-token"
        try:
            report = ProductionReadiness(default_adapter_registry()).evaluate(tests_passed=True, compile_passed=True, required_adapters=(("local-workspace", "revision"),))
            self.assertTrue(report.ready)
        finally:
            if previous is None:
                os.environ.pop("ORVILLE_API_TOKEN", None)
            else:
                os.environ["ORVILLE_API_TOKEN"] = previous


if __name__ == "__main__":
    unittest.main()
