from pathlib import Path

from orville_core.browser import BrowserSession


def test_form_approval_record_keeps_field_names_but_not_values() -> None:
    session = BrowserSession("browser-test", {"example.com"})
    result = session.submit_form("#login", {"username": "alice", "password": "do-not-store"})

    assert result["takeover_required"] is True
    record = session.to_dict()["approval_records"][-1]
    assert record["action"] == "form_submission"
    assert record["approved"] is False
    assert record["details"]["field_names"] == ["password", "username"]
    assert "do-not-store" not in str(record)


def test_download_approval_record_redacts_query_and_waits_for_approval() -> None:
    session = BrowserSession("browser-test", {"example.com"})
    result = session.download("https://example.com/file.zip?token=secret#fragment")

    assert result["takeover_required"] is True
    record = session.to_dict()["approval_records"][-1]
    assert record["action"] == "download"
    assert record["approved"] is False
    assert record["target"] == "https://example.com/file.zip"
    assert "secret" not in str(record)


def test_approval_records_are_bounded_and_persisted(tmp_path: Path) -> None:
    session = BrowserSession("browser-test", {"example.com"})
    for _ in range(120):
        session.record_approval("download", "/tmp/file.bin", approved=False, details={"value": "secret"})
    assert len(session.to_dict()["approval_records"]) == 100
    assert all(item["details"]["value"] == "[REDACTED]" for item in session.to_dict()["approval_records"])
