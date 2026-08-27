from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "INCIDENT_RESPONSE_CREDENTIAL_ROTATION_RECOVERY.md"


class IncidentResponseProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")

    def test_runbook_covers_required_operational_stages(self) -> None:
        for heading in (
            "## Detection and intake",
            "## Containment",
            "## Credential rotation and revocation",
            "## Recovery and restoration",
            "## Closure and post-incident review",
        ):
            self.assertIn(heading, self.text)

    def test_runbook_covers_severity_and_recovery_validation(self) -> None:
        for value in ("Critical", "High", "Medium", "Low", "checksum", "canary", "duplicate events", "last safe checkpoint"):
            self.assertIn(value, self.text)

    def test_runbook_requires_explicit_confirmation_for_sensitive_actions(self) -> None:
        self.assertIn("separate explicit confirmation", self.text)
        self.assertIn("exact target and scope", self.text)
        self.assertIn("failed recovery", self.text.lower())
        self.assertIn("must not silently retry", self.text.lower())

    def test_runbook_is_secret_safe_and_standalone(self) -> None:
        for phrase in (
            "does not assume access to a provider",
            "Never copy credentials",
            "Do not commit the replacement value",
            "synthetic credentials and local endpoints only",
            "No responder may use a credential discovered",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotRegex(self.text, r"(?i)Bearer\s+[A-Za-z0-9._-]{8,}")


if __name__ == "__main__":
    unittest.main()
