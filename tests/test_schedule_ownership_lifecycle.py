"""Focused tests for the schedule ownership and lifecycle contract."""

from __future__ import annotations

import unittest
from pathlib import Path


class ScheduleOwnershipLifecycleTests(unittest.TestCase):
    """Verify the scheduling contract covers each selected TODO requirement."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.document = (root / "docs" / "SCHEDULE_OWNERSHIP_LIFECYCLE.md").read_text(encoding="utf-8")

    def test_contract_defines_ownership_timezone_and_expiration(self) -> None:
        for phrase in ("exactly one project/workspace", "IANA timezone", "UTC", "expires_at", "expired", "DST gaps"):
            self.assertIn(phrase, self.document)

    def test_contract_defines_pause_resume_and_missed_run_policy(self) -> None:
        for phrase in ("paused", "Resume", "skip", "catch-up count", "idempotent", "auditable"):
            self.assertIn(phrase, self.document)

    def test_contract_defines_safe_failure_notifications_and_acceptance(self) -> None:
        for phrase in ("durably recorded before notification", "approved non-secret references", "bounded retry budget", "deduplication key", "raw provider responses", "Acceptance checks"):
            self.assertIn(phrase, self.document)


if __name__ == "__main__":
    unittest.main()
