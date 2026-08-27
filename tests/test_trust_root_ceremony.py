from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orville_core.trust_root_ceremony import CeremonyApproval, ProductionTrustRootCeremony, TrustRootCeremonyError, canonical_digest


ROOT = {"signed": {"version": 1, "roles": {"root": {"keyids": ["key"], "threshold": 1}}, "keys": {"key": {"scheme": "ed25519", "keyval": {"public": "AA=="}}}}}


class TrustRootCeremonyTests(unittest.TestCase):
    def approval(self, root=ROOT) -> CeremonyApproval:
        return CeremonyApproval("operator-1", "change-123", "2026-08-27T00:00:00+00:00", canonical_digest(root), "approved production root")

    def test_bootstrap_requires_pinned_digest_and_records_secret_free_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            ceremony = ProductionTrustRootCeremony(Path(directory) / "root.json", Path(directory) / "evidence.json")
            with patch("orville_core.trust_root_ceremony.TufRepositoryVerifier.bootstrap") as bootstrap:
                bootstrap.return_value = object()
                evidence = ceremony.bootstrap(ROOT, self.approval())
            self.assertEqual(evidence["status"], "committed")
            self.assertEqual(evidence["root_sha256"], canonical_digest(ROOT))
            self.assertNotIn("token", json.dumps(evidence).lower())

    def test_digest_mismatch_and_missing_approval_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            ceremony = ProductionTrustRootCeremony(Path(directory) / "root.json", Path(directory) / "evidence.json")
            bad = CeremonyApproval("operator-1", "change-123", "2026-08-27T00:00:00+00:00", "0" * 64, "approved")
            with self.assertRaises(TrustRootCeremonyError):
                ceremony.bootstrap(ROOT, bad)
            with self.assertRaises(TrustRootCeremonyError):
                CeremonyApproval("", "", "bad", "0" * 64, "").validate()

    def test_status_is_safe_before_and_after_revocation(self):
        with tempfile.TemporaryDirectory() as directory:
            root_path = Path(directory) / "root.json"
            evidence_path = Path(directory) / "evidence.json"
            ceremony = ProductionTrustRootCeremony(root_path, evidence_path)
            self.assertEqual(ceremony.status()["status"], "not_initialized")
            root_path.write_text(json.dumps(ROOT), encoding="utf-8")
            evidence = ceremony.revoke(self.approval(), "compromised test key")
            self.assertEqual(evidence["action"], "revoke")
            self.assertEqual(ceremony.status()["status"], "recorded")


if __name__ == "__main__":
    unittest.main()
