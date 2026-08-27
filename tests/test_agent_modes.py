import unittest

from orville_core.agent_modes import AgentModeRegistry, ModelOption, ModelSelector


class AgentModeTests(unittest.TestCase):
    def test_modes_are_explicit_and_model_selection_is_capability_aware(self):
        registry = AgentModeRegistry()
        self.assertEqual(registry.get("planning").mode_id, "planning")
        selector = ModelSelector([
            ModelOption("cloud", "code-model", frozenset({"code", "text"}), local=False),
            ModelOption("local", "local-code", frozenset({"code", "text"}), local=True),
        ])
        self.assertEqual(selector.select({"code"}, local_only=True).provider_id, "local")
        self.assertEqual(selector.select({"code"}, preferred_provider="cloud").provider_id, "cloud")
        with self.assertRaises(LookupError):
            selector.select({"vision"})


if __name__ == "__main__":
    unittest.main()
