"""Focused tests for long-running job state and restart recovery contract."""

from __future__ import annotations

import unittest
from pathlib import Path


class LongRunningJobStateTests(unittest.TestCase):
    """Verify durable state and restart rules are explicit and complete."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.document = (root / "docs" / "LONG_RUNNING_JOB_STATE.md").read_text(encoding="utf-8")

    def test_contract_defines_durable_records_and_state_machine(self) -> None:
        for phrase in ("Workflow run", "Task checkpoint", "Event cursor", "Execution lease", "Artifact reference", "Recovery record", "interrupted", "dead_letter"):
            self.assertIn(phrase, self.document)

    def test_contract_defines_checkpoint_lease_and_restart_reconciliation(self) -> None:
        for phrase in ("committed atomically", "stale worker", "latest verified checkpoint", "expired leases", "idempotent", "blocked"):
            self.assertIn(phrase, self.document)

    def test_contract_defines_security_retention_and_acceptance_gates(self) -> None:
        for phrase in ("credentials", "bearer tokens", "redacted diagnostics", "retention period", "fail closed", "Acceptance checks", "crash injection"):
            self.assertIn(phrase.lower(), self.document.lower())


if __name__ == "__main__":
    unittest.main()
