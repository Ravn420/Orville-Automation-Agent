"""Credential-free initial cloud onboarding contract for Orville.

The initial experience is managed-service first. User-connected Blackbox access
is optional and is never represented as a prerequisite or sign-in requirement.
"""

from __future__ import annotations

from typing import Any


def initial_cloud_onboarding(*, relay_configured: bool = False) -> dict[str, Any]:
    """Return deterministic public onboarding state without credential material."""
    return {
        "provider": "blackbox",
        "default_access": "managed_cloud",
        "managed_access": {
            "available": bool(relay_configured),
            "required_for_start": False,
            "status": "available" if relay_configured else "pending_configuration",
        },
        "user_connection": {
            "available": True,
            "required_for_start": False,
            "action_label": "Connect with Blackbox API key",
            "action": {"label": "Connect with Blackbox API key", "route": "/api/v1/cloud/blackbox/user/api-key", "method": "POST", "optional": True},
            "method": "api_key",
            "authorization_status": "official_oauth_or_device_flow_not_confirmed",
            "authentication_policy": {
                "accepted_method": "api_key",
                "forbidden_methods": ["browser_cookie", "undocumented_session_endpoint", "private_web_api", "shared_orville_credential", "unverified_oauth_device_flow"],
            },
            "api_key_instructions": {
                "label": "View Blackbox API-key instructions",
                "url": "https://docs.blackbox.ai/api-reference/authentication",
            },
            "sign_in_required": False,
            "api_key_required": False,
            "connection_requires_api_key": True,
            "actions": {
                "test_connection": {"label": "Test Blackbox API key", "route": "/api/v1/cloud/blackbox/user/test", "method": "POST"},
                "select_provider_model": {"label": "Select Blackbox provider and model", "route": "/api/v1/cloud/blackbox/models", "method": "POST"},
                "replace_credential": {"label": "Replace Blackbox API key", "route": "/api/v1/cloud/blackbox/user/api-key", "method": "POST"},
                "disconnect": {"label": "Disconnect Blackbox", "route": "/api/v1/cloud/blackbox/user/disconnect", "method": "POST"},
                "delete_credential": {"label": "Delete stored Blackbox credential", "route": "/api/v1/cloud/blackbox/user/credential", "method": "DELETE"},
            },
        },
        "privacy_notice": "Managed cloud access is subject to Orville service limits, privacy terms, and availability.",
        "connection_disclosure": {
            "text": "Connecting a Blackbox account may require an eligible subscription and may incur usage charges according to Blackbox account terms.",
            "terms_url": "https://www.blackbox.ai/terms-of-service",
        },
        "remote_content_confirmation": {
            "required_before_send": True,
            "approval_field": "approved_remote",
            "scope": ["workspace_files", "repository_content", "images", "audio", "video", "tool_results"],
        },
        "validation_policy": {
            "tls_required": True,
            "allowed_hosts": ["api.blackbox.ai", "enterprise.blackbox.ai"],
            "credential_free_urls": True,
            "oauth_callback_state_required_if_official_flow_confirmed": True,
            "token_expiry_required_if_official_flow_confirmed": True,
        },
        "credential_returned": False,
    }


__all__ = ["initial_cloud_onboarding"]
