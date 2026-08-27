from __future__ import annotations

from orville_core.cloud_onboarding import initial_cloud_onboarding


def test_initial_cloud_onboarding_never_requires_user_credentials() -> None:
    state = initial_cloud_onboarding(relay_configured=False)
    assert state["default_access"] == "managed_cloud"
    assert state["managed_access"]["required_for_start"] is False
    assert state["user_connection"]["required_for_start"] is False
    assert state["user_connection"]["api_key_required"] is False
    assert state["user_connection"]["sign_in_required"] is False
    assert state["user_connection"]["connection_requires_api_key"] is True
    assert state["user_connection"]["action_label"] == "Connect with Blackbox API key"
    assert state["user_connection"]["action"] == {
        "label": "Connect with Blackbox API key",
        "route": "/api/v1/cloud/blackbox/user/api-key",
        "method": "POST",
        "optional": True,
    }
    assert state["user_connection"]["authorization_status"] == "official_oauth_or_device_flow_not_confirmed"
    assert state["user_connection"]["authentication_policy"] == {
        "accepted_method": "api_key",
        "forbidden_methods": ["browser_cookie", "undocumented_session_endpoint", "private_web_api", "shared_orville_credential", "unverified_oauth_device_flow"],
    }
    assert state["user_connection"]["api_key_instructions"] == {
        "label": "View Blackbox API-key instructions",
        "url": "https://docs.blackbox.ai/api-reference/authentication",
    }
    assert set(state["user_connection"]["actions"]) == {
        "test_connection",
        "select_provider_model",
        "replace_credential",
        "disconnect",
        "delete_credential",
    }
    assert state["user_connection"]["actions"]["test_connection"]["route"] == "/api/v1/cloud/blackbox/user/test"
    assert state["user_connection"]["actions"]["delete_credential"]["route"] == "/api/v1/cloud/blackbox/user/credential"
    assert state["credential_returned"] is False
    assert state["privacy_notice"] == (
        "Managed cloud access is subject to Orville service limits, privacy terms, and availability."
    )
    assert state["connection_disclosure"] == {
        "text": "Connecting a Blackbox account may require an eligible subscription and may incur usage charges according to Blackbox account terms.",
        "terms_url": "https://www.blackbox.ai/terms-of-service",
    }
    assert state["remote_content_confirmation"] == {
        "required_before_send": True,
        "approval_field": "approved_remote",
        "scope": ["workspace_files", "repository_content", "images", "audio", "video", "tool_results"],
    }
    assert state["validation_policy"] == {
        "tls_required": True,
        "allowed_hosts": ["api.blackbox.ai", "enterprise.blackbox.ai"],
        "credential_free_urls": True,
        "oauth_callback_state_required_if_official_flow_confirmed": True,
        "token_expiry_required_if_official_flow_confirmed": True,
    }


def test_configured_relay_is_presented_as_available_managed_access() -> None:
    state = initial_cloud_onboarding(relay_configured=True)
    assert state["managed_access"] == {
        "available": True,
        "required_for_start": False,
        "status": "available",
    }
