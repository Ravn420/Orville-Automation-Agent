from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "orville_core" / "api.py"
DOC = ROOT / "docs" / "REALTIME_EXECUTION_EVENTS.md"


class RealtimeExecutionEventsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.api_text = API.read_text(encoding="utf-8")
        cls.doc_text = DOC.read_text(encoding="utf-8")

    def test_api_exposes_polling_and_sse_routes(self) -> None:
        for phrase in (
            '@app.get("/api/v1/runs/{run_id}/events", dependencies=[Depends(authenticate)])',
            '@app.get("/api/v1/runs/{run_id}/events/stream", dependencies=[Depends(authenticate)])',
            "StreamingResponse(event_generator(), media_type=\"text/event-stream\"",
            "Last-Event-ID",
            "X-Orville-Resume",
        ):
            self.assertIn(phrase, self.api_text)

    def test_documented_contract_covers_resume_order_and_terminal_behavior(self) -> None:
        for phrase in (
            "Polling",
            "SSE",
            "sequence",
            "deduplication key",
            "bounded backoff",
            "terminal state",
            "final checkpoint reconciliation",
        ):
            self.assertIn(phrase, self.doc_text)

    def test_delivery_contract_requires_auth_and_safe_reconciliation(self) -> None:
        for phrase in (
            "exact bearer authentication",
            "Missing or invalid credentials",
            "untrusted data",
            "must not infer authorization",
            "approval contracts",
            "bounded backoff",
        ):
            self.assertIn(phrase, self.doc_text)
        self.assertNotRegex(self.doc_text, r"(?i)sk-[A-Za-z0-9]{12,}|api[_-]?key\\s*=\\s*[\"'][^\"']{8,}[\"']")

    def test_reproduction_commands_reference_existing_paths(self) -> None:
        self.assertTrue(API.is_file())
        self.assertTrue(DOC.is_file())
        self.assertTrue((ROOT / "tests" / "test_realtime_execution_events.py").is_file())
        for command in (
            "python -m unittest tests.test_realtime_execution_events -v",
            "python -m py_compile orville_core\\api.py tests\\test_realtime_execution_events.py",
        ):
            self.assertIn(command, self.doc_text)


if __name__ == "__main__":
    unittest.main()
