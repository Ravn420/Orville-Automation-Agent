import unittest

from orville_core.adapters import AdapterHealth, AdapterRegistry, AdapterStatus, default_adapter_registry


class AdapterTests(unittest.TestCase):
    def test_default_registry_reports_real_capability_boundaries(self):
        registry = default_adapter_registry()
        self.assertEqual(registry.get("browser").status, AdapterStatus.BLOCKED)
        self.assertEqual(registry.require("local-workspace", "revision").status, AdapterStatus.MOCK)
        with self.assertRaises(RuntimeError):
            registry.require("browser", "navigate")
        with self.assertRaises(RuntimeError):
            registry.require("deployment", "production")

    def test_health_checks_can_refresh_adapter_state(self):
        registry = AdapterRegistry()
        registry.register(AdapterHealth("test", "test", AdapterStatus.DEGRADED), health_check=lambda: AdapterHealth("test", "test", AdapterStatus.AVAILABLE, frozenset({"run"})))
        self.assertEqual(registry.require("test", "run").status, AdapterStatus.AVAILABLE)


if __name__ == "__main__":
    unittest.main()
