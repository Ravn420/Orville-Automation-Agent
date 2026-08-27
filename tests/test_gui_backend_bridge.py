from __future__ import annotations

from pathlib import Path
import unittest

from orville_core.secrets_audit import AuditStore


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "orville_core" / "api.py"
DOC = ROOT / "docs" / "GUI_BACKEND_BRIDGE.md"


class GuiBackendBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.api_text = API.read_text(encoding="utf-8")
        cls.doc_text = DOC.read_text(encoding="utf-8")

    def test_api_defines_required_bridge_controls(self) -> None:
        for phrase in (
            "def create_app",
            "def authenticate",
            "CORSMiddleware",
            "allow_credentials=False",
            "requests_per_minute",
            "status_code=429",
            "RequestValidationError",
            "_safe_api_error_message",
            "audit_store = AuditStore",
        ):
            self.assertIn(phrase, self.api_text)

    def test_documentation_covers_required_controls_and_boundaries(self) -> None:
        for phrase in (
            "Authentication",
            "Authorization",
            "Request validation",
            "CORS",
            "Rate limiting",
            "Audit logging",
            "Error handling",
            "confirmation and approval contracts",
            "untrusted data",
            "TLS termination",
        ):
            self.assertIn(phrase, self.doc_text)

    def test_audit_store_redacts_sensitive_metadata(self) -> None:
        with self.subTest("synthetic secret redaction"):
            import tempfile

            with tempfile.TemporaryDirectory() as directory:
                record = AuditStore(Path(directory) / "audit.db").append(
                    "gui-user",
                    "connector.invoke",
                    "synthetic-target",
                    "rejected",
                    metadata={"api_key": "synthetic-secret", "authorization": "Bearer synthetic-token", "safe": "ok"},
                )
                self.assertEqual(record.metadata["api_key"], "[REDACTED]")
                self.assertEqual(record.metadata["authorization"], "[REDACTED]")
                self.assertEqual(record.metadata["safe"], "ok")

    def test_no_credential_shaped_literals_are_in_bridge_contract(self) -> None:
        combined = self.api_text + self.doc_text
        self.assertNotRegex(combined, r"(?i)sk-[A-Za-z0-9]{12,}|Bearer\\s+[A-Za-z0-9._-]{12,}|api[_-]?key\\s*=\\s*[\"'][^\"']{8,}[\"']")


if __name__ == "__main__":
    unittest.main()
