"""Focused validation for the frontend-backend contract artifacts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "frontend-backend.example.json"
CONTRACT_PATH = ROOT / "docs" / "FRONTEND_BACKEND_CONTRACTS.md"


class FrontendBackendContractTests(unittest.TestCase):
    """Verify the non-secret configuration and documented integration boundary."""

    def test_example_configuration_is_valid_and_secret_free(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        serialized = json.dumps(config)

        self.assertEqual(config["schema"], "orville.frontend-backend.environment")
        self.assertEqual(config["api"]["api_prefix"], "/api/v1")
        self.assertEqual(config["frontend"]["token_storage"], "memory-only")
        self.assertFalse(config["frontend"]["provider_credentials_exposed"])
        self.assertTrue(config["error_contract"]["message_must_be_secret_free"])
        self.assertNotRegex(serialized, re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,}|api[_-]?key\s*[:=])"))

    def test_contract_documents_routes_and_environment_boundaries(self) -> None:
        contract = CONTRACT_PATH.read_text(encoding="utf-8")

        for route in (
            "/api/v1/health",
            "/api/v1/objectives",
            "/api/v1/runs/{run_id}",
            "/api/v1/state",
            "/api/v1/artifacts",
        ):
            self.assertIn(route, contract)
        for variable in (
            "ORVILLE_API_HOST",
            "ORVILLE_API_PORT",
            "ORVILLE_API_TOKEN",
            "ORVILLE_API_BASE_URL",
            "ORVILLE_ALLOWED_ORIGINS",
        ):
            self.assertIn(variable, contract)
        self.assertIn("message` is safe for end-user display", contract)
        self.assertIn("provider credentials", contract)
        self.assertIn("memory only", contract)

    def test_operation_names_are_bounded_and_safe(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        pattern = re.compile(config["error_contract"]["allowed_operation_pattern"])
        for operation in (
            "health_check",
            "create_objective",
            "execute_run",
            "load_run",
            "get_artifact",
        ):
            self.assertRegex(operation, pattern)
        self.assertNotRegex("load_run?token=secret", pattern)


if __name__ == "__main__":
    unittest.main()
