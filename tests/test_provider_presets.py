from orville_core.provider_presets import provider_presets


def test_priority_provider_presets_are_public_and_unique():
    presets = provider_presets()
    ids = [item.connector_id for item in presets]
    assert len(ids) == len(set(ids))
    assert {"github", "slack", "notion", "google-gmail", "google-calendar", "microsoft-outlook", "stripe", "hubspot", "n8n"} <= set(ids)
    for preset in presets:
        data = preset.public()
        assert data["connector_id"]
        assert data["base_url"].startswith("https://")
        assert data["documentation_url"].startswith("https://")
        assert data["auth_modes"]
        if "oauth2" in data["auth_modes"]:
            assert data["authorization_url"] and data["token_url"]


def test_api_key_presets_have_safe_header_metadata():
    by_id = {item.connector_id: item for item in provider_presets()}
    assert by_id["stripe"].credential_header == "Authorization"
    assert by_id["n8n"].api_key_header == "X-N8N-API-KEY"
