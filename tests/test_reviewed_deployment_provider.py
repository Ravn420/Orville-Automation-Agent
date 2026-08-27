from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from orville_core.canary import CanaryError, SyntheticDeploymentAdapter
from orville_core.reviewed_deployment_provider import ReviewedDeploymentAdapter


class SlowBackend(SyntheticDeploymentAdapter):
    def deploy(self, release_id: str, rollback_target: str) -> None:
        time.sleep(0.05)
        super().deploy(release_id, rollback_target)


class ReviewedDeploymentProviderTests(unittest.TestCase):
    def test_dry_run_never_calls_backend_and_is_idempotent(self):
        backend = SyntheticDeploymentAdapter()
        adapter = ReviewedDeploymentAdapter(backend, provider_id="local", credential_reference="secret-ref-1", dry_run=True)
        adapter.deploy("release-2", "release-1")
        adapter.deploy("release-2", "release-1")
        adapter.set_traffic("release-2", 10)
        self.assertEqual(backend.releases, {})
        self.assertEqual(len(adapter.operation_history()), 2)
        self.assertEqual(adapter.status("release-2")["status"], "dry_run")

    def test_live_backend_operations_are_bounded_and_idempotent(self):
        backend = SyntheticDeploymentAdapter()
        adapter = ReviewedDeploymentAdapter(backend, provider_id="local", credential_reference="secret-ref-1", dry_run=False, timeout_seconds=1)
        adapter.deploy("release-2", "release-1")
        adapter.deploy("release-2", "release-1")
        adapter.set_traffic("release-2", 25)
        self.assertEqual(backend.releases["release-2"]["traffic_percent"], 25)
        self.assertEqual(len(adapter.operation_history()), 2)

    def test_rejects_raw_credential_like_reference_and_invalid_traffic(self):
        with self.assertRaises(ValueError):
            ReviewedDeploymentAdapter(SyntheticDeploymentAdapter(), provider_id="local", credential_reference="api_key=raw-value")
        adapter = ReviewedDeploymentAdapter(SyntheticDeploymentAdapter(), provider_id="local", credential_reference="secret-ref-1")
        with self.assertRaises(CanaryError):
            adapter.set_traffic("release-2", 101)

    def test_timeout_fails_closed(self):
        adapter = ReviewedDeploymentAdapter(SlowBackend(), provider_id="local", credential_reference="secret-ref-1", dry_run=False, timeout_seconds=0.01)
        with self.assertRaises(CanaryError):
            adapter.deploy("release-2", "release-1")

    def test_status_is_redacted(self):
        class LeakyBackend(SyntheticDeploymentAdapter):
            def status(self, release_id: str):
                return {"status": "deployed", "authorization": "Bearer hidden", "release_id": release_id}
        adapter = ReviewedDeploymentAdapter(LeakyBackend(), provider_id="local", credential_reference="secret-ref-1", dry_run=False)
        status = adapter.status("release-2")
        self.assertNotIn("hidden", str(status))


if __name__ == "__main__":
    unittest.main()
