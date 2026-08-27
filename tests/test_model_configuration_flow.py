"""Focused validation for the secret-safe model configuration flow."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOCKUP_PATH = ROOT / "docs" / "mockups" / "model-configuration.html"
CONTRACT_PATH = ROOT / "docs" / "MODEL_CONFIGURATION_FLOW.md"


class ModelConfigurationFlowTests(unittest.TestCase):
    """Verify that model configuration metadata is reviewable without secrets."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mockup = MOCKUP_PATH.read_text(encoding="utf-8")
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_provider_presets_and_required_fields_are_present(self) -> None:
        for provider in ("ollama", "gemini", "openai_compatible", "anthropic"):
            self.assertIn(f'value="{provider}"', self.mockup)
            self.assertIn(provider.lower(), self.contract.lower())
        for field in ("provider", "model", "endpoint", "api-key", "timeout", "privacy"):
            self.assertIn(f'id="{field}"', self.mockup)
        self.assertIn('type="password"', self.mockup)

    def test_endpoint_validation_and_explicit_health_check_are_defined(self) -> None:
        for marker in ("new URL", "http:", "https:", "Health check is ready", "no request was made by this preview"):
            self.assertIn(marker, self.mockup)
        for phrase in ("syntactically valid", "A health check is a separate, user-visible action", "does not authorize network access"):
            self.assertIn(phrase, self.contract)

    def test_redacted_review_clears_credentials_and_blocks_unsafe_storage(self) -> None:
        for marker in ("api_key_configured", 'document.getElementById("api-key").value = ""', "Redacted configuration review", "credential value is displayed"):
            self.assertIn(marker, self.mockup)
        for phrase in ("never persists credential values", "project files", "STATE.md", "TASK_GRAPH.md", "local draft storage"):
            self.assertIn(phrase, self.contract)

    def test_configuration_states_and_approval_boundaries_are_explicit(self) -> None:
        for state in ("draft", "ready_for_review", "saved", "health_check_pending", "healthy", "blocked", "failed"):
            self.assertIn(f"`{state}`", self.contract)
        for phrase in ("External cloud routing", "explicit approval gate", "safe operation ID", "Production credentials must never be used"):
            self.assertIn(phrase, self.contract)
        self.assertNotRegex(
            self.mockup + self.contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
