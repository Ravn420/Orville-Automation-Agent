"""Smoke test for automatic source and citation capture in research runs."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from orville_core.api import create_app


def research_handler(task, context):
    return {"text": "The fixture research result is supported by https://example.org/research/report and https://docs.example.org/guide."}


def main() -> int:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        app = create_app(api_token="citation-smoke-token", storage="json", checkpoint_dir=root / ".orville", handlers={"intake.objective": research_handler})
        client = TestClient(app)
        headers = {"Authorization": "Bearer citation-smoke-token"}
        created = client.post("/api/v1/objectives", headers=headers, json={"objective": "Research the fixture topic and cite sources", "generation_mode": "standard"})
        assert created.status_code == 200, created.text
        run_id = created.json()["run_id"]
        executed = client.post(f"/api/v1/objectives/{run_id}/execute", headers=headers, json={"context": {}})
        assert executed.status_code == 200, executed.text
        evidence = client.get(f"/api/v1/runs/{run_id}/sources", headers=headers)
        assert evidence.status_code == 200, evidence.text
        payload = evidence.json()
        if len(payload["sources"]) != 2:
            print("DEBUG_EVIDENCE", payload)
            debug_run = client.get(f"/api/v1/runs/{run_id}", headers=headers).json()
            print("DEBUG_TASKS", [(item.get("task_id"), item.get("status"), item.get("output"), item.get("error")) for item in debug_run["graph"]["tasks"]])
            print("DEBUG_CLASSIFICATION", debug_run.get("context", {}).get("classification"))
        assert len(payload["sources"]) == 2, payload
        assert len(payload["citations"]) == 1, payload
        assert payload["citations"][0]["capture_mode"] == "automatic"
        print(f"CITATION_SMOKE=PASS SOURCES={len(payload['sources'])} CITATIONS={len(payload['citations'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
