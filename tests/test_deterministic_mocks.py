from __future__ import annotations

import json
import unittest
from pathlib import Path
from orville_core.providers import JsonHttpClient, ProviderError
from tests.fixtures.mock_external_service import deterministic_mock_service


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests" / "fixtures" / "deterministic_external_cases.json"


class DeterministicMockServiceTests(unittest.TestCase):
    """Exercise local external-boundary behavior without credentials or internet access."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads(CASES.read_text(encoding="utf-8"))

    def test_health_and_echo_match_deterministic_cases(self) -> None:
        with deterministic_mock_service() as base_url:
            client = JsonHttpClient()
            self.assertEqual(client.request("GET", base_url + self.cases["health"]["path"]), self.cases["health"]["body"])
            self.assertEqual(client.request("POST", base_url + self.cases["echo"]["path"], payload=self.cases["echo"]["request"]), self.cases["echo"]["body"])

    def test_unavailable_fixture_returns_safe_provider_error(self) -> None:
        with deterministic_mock_service() as base_url:
            with self.assertRaises(ProviderError) as raised:
                JsonHttpClient().request("GET", base_url + self.cases["unavailable"]["path"])
            self.assertEqual(raised.exception.status_code, self.cases["unavailable"]["status"])
            self.assertNotIn("synthetic-unavailable", str(raised.exception))

    def test_fixture_data_contains_no_credential_headers_or_secret_values(self) -> None:
        payload_only = {key: value for key, value in self.cases.items() if key != "prohibited"}
        rendered = json.dumps(payload_only, sort_keys=True)
        for prohibited in self.cases["prohibited"]:
            self.assertNotIn(prohibited, rendered)
        self.assertNotIn("sk-", rendered)
        self.assertNotIn("Bearer ", rendered)


if __name__ == "__main__":
    unittest.main()
