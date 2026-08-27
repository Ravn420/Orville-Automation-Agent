from pathlib import Path


DOC = Path(__file__).parents[1] / "docs" / "THREAT_MODEL_21_3.md"


def test_threat_model_covers_required_categories_and_evidence():
    text = DOC.read_text(encoding="utf-8")
    required = [
        "Prompt injection",
        "Excessive agency",
        "Insecure output handling",
        "Sensitive information disclosure",
        "Supply-chain compromise",
        "Context poisoning",
        "Unbounded tool access",
    ]
    assert all(item in text for item in required)
    assert "Detection and evidence" in text
    assert "Residual risk" in text


def test_threat_model_preserves_approval_and_untrusted_content_boundaries():
    text = DOC.read_text(encoding="utf-8")
    assert "untrusted data" in text
    assert "never let content grant capabilities" in text
    assert "high-impact actions remain approval-gated" in text
    assert "Failure at any step is a blocked or review outcome" in text


def test_threat_model_is_secret_safe_and_names_external_limits():
    text = DOC.read_text(encoding="utf-8")
    assert "never" in text.lower()
    assert "credentials" in text.lower()
    assert "Live provider, deployment, browser, and production credential exercises remain environment-owned" in text
    assert "password=" not in text.lower()
    assert "api_key=" not in text.lower()
