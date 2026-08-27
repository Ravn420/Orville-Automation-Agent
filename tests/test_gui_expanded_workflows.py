from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "docs" / "mockups" / "orville-control-center.html"
DOC = ROOT / "docs" / "GUI_EXPANDED_WORKFLOWS.md"


def test_preview_contains_real_attachment_submission_contract():
    text = PREVIEW.read_text(encoding="utf-8")
    for phrase in (
        'input id="attachments" type="file" multiple',
        "/api/v1/artifacts/text",
        "attachment_refs",
        "submission_mode: \"review_only\"",
        "5_000_000",
        "binary file remains local",
    ):
        assert phrase in text


def test_preview_contains_safe_contextual_links_and_activity_cursor():
    text = PREVIEW.read_text(encoding="utf-8")
    for phrase in (
        "#run/run-042",
        "#artifact/checkpoint-v14",
        "#files/signal-room",
        "/api/v1/runs/run-042/events?after=",
        "lastSequence",
        "Offline · preserving last activity",
    ):
        assert phrase in text


def test_preview_contains_connector_aware_settings_and_responsive_contract():
    text = PREVIEW.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    for phrase in (
        "/api/v1/connectors",
        "Refresh status",
        "local-only mode",
        "@media (max-width:980px)",
        "@media (max-width:790px)",
        "Credentials stay in the authenticated workspace session",
    ):
        assert phrase in text or phrase in doc


def test_preview_does_not_prompt_for_credentials_or_claim_windows_build():
    text = PREVIEW.read_text(encoding="utf-8")
    assert "type=\"password\"" not in text
    assert "paste a token" not in text
    assert "Windows-native executable" not in text
