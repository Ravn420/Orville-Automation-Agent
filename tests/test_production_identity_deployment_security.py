from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (ROOT / "docs" / "PRODUCTION_IDENTITY_DEPLOYMENT_SECURITY.md").read_text(encoding="utf-8")


def test_production_security_contract_covers_required_boundaries():
    for phrase in (
        "Identity provider",
        "Scoped authorization",
        "TLS",
        "Deployment secrets",
        "CORS allowlist",
        "Audit-log sink",
        "issuer",
        "audience",
        "PKCE",
        "least-privilege",
        "HTTPS origins",
        "append-only",
        "fails closed",
    ):
        assert phrase in CONTRACT


def test_production_security_contract_has_no_live_secret_material():
    lowered = CONTRACT.lower()
    assert "-----begin" not in lowered
    assert "sk-live" not in lowered
    assert "eyj" not in lowered
    assert "example.invalid" in lowered
    assert "never place values in source" in lowered
