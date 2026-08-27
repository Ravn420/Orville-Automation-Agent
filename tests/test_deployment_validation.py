from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.deployment_validation import preflight, smoke
from tests.fixtures.mock_external_service import deterministic_mock_service


ROOT = Path(__file__).resolve().parents[1]


class DeploymentValidationTests(unittest.TestCase):
    def test_preflight_accepts_all_supported_targets_with_repository_files(self) -> None:
        for target in ("sandbox", "web-hosting", "attached-desktop", "persistent-computing"):
            requirements = preflight(target, ROOT)
            self.assertTrue(requirements)
            self.assertTrue(all((ROOT / path).is_file() for path in requirements))

    def test_smoke_checks_local_fixture_and_returns_safe_evidence(self) -> None:
        with deterministic_mock_service() as base_url:
            result = smoke(base_url, path="/health")
        self.assertEqual(result, {"status": "healthy", "http_status": 200, "path": "/health"})
        self.assertNotIn("Authorization", str(result))

    def test_smoke_rejects_remote_hosts_without_explicit_opt_in(self) -> None:
        with self.assertRaisesRegex(ValueError, "explicit --allow-remote"):
            smoke("https://example.test", path="/health")

    def test_preflight_fails_when_target_prerequisite_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(FileNotFoundError, "missing sandbox prerequisites"):
                preflight("sandbox", root)


if __name__ == "__main__":
    unittest.main()
