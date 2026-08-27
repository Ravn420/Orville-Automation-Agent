"""Focused tests for operation-aware, secret-safe API errors."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
    from orville_core.api import create_app
except ImportError:  # pragma: no cover - optional API dependency
    TestClient = None
    create_app = None


@unittest.skipIf(TestClient is None, "FastAPI API extras are not installed")
class ApiErrorMessageTests(unittest.TestCase):
    """Verify errors identify operations without echoing sensitive details."""

    def test_authentication_error_identifies_health_operation_without_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret-token"))
            response = client.get("/api/v1/health", headers={"Authorization": "Bearer secret-token"})
            self.assertEqual(response.status_code, 200)
            response = client.get("/api/v1/health", headers={"Authorization": "Bearer wrong-token"})
            body = response.json()
            self.assertEqual(response.status_code, 401)
            self.assertEqual(body["error"]["operation"], "get_health")
            self.assertIn("get_health failed", body["error"]["message"])
            self.assertEqual(body["detail"], body["error"]["message"])
            self.assertNotIn("wrong-token", response.text)
            self.assertNotIn("secret-token", response.text)

    def test_validation_error_identifies_objective_operation_without_payload_echo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret-token"))
            response = client.post(
                "/api/v1/objectives",
                headers={"Authorization": "Bearer secret-token"},
                json={"objective": "", "api_key": "sk-live-secret123"},
            )
            body = response.json()
            self.assertEqual(response.status_code, 422)
            self.assertEqual(body["error"]["code"], "invalid_request")
            self.assertEqual(body["error"]["operation"], "post_objectives")
            self.assertIn("post_objectives failed", body["error"]["message"])
            self.assertNotIn("sk-live-secret123", response.text)
            self.assertNotIn("secret-token", response.text)

    def test_not_found_error_uses_route_template_not_resource_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret-token"))
            response = client.get(
                "/api/v1/runs/run-with-sensitive-token/events",
                headers={"Authorization": "Bearer secret-token"},
            )
            body = response.json()
            self.assertEqual(response.status_code, 404)
            self.assertEqual(body["error"]["operation"], "get_runs_run_id_events")
            self.assertIn("failed", body["error"]["message"])
            self.assertNotIn("run-with-sensitive-token", response.text)


if __name__ == "__main__":
    unittest.main()
