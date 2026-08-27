"""Provider authentication presets; values are public endpoints, never credentials."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class ProviderPreset:
    connector_id: str
    display_name: str
    auth_modes: tuple[str, ...]
    base_url: str
    documentation_url: str
    authorization_url: str | None = None
    token_url: str | None = None
    revoke_url: str | None = None
    scopes: tuple[str, ...] = ()
    credential_header: str = "Authorization"
    api_key_header: str | None = None
    version: str = "1.0.0"

    def public(self) -> dict[str, Any]:
        return asdict(self)


def provider_presets() -> tuple[ProviderPreset, ...]:
    google_scopes = ("openid", "email", "profile")
    return (
        ProviderPreset("github", "GitHub", ("oauth2", "api_key"), "https://api.github.com", "https://docs.github.com/en/rest", "https://github.com/login/oauth/authorize", "https://github.com/login/oauth/access_token", scopes=("read:user", "repo")),
        ProviderPreset("slack", "Slack", ("oauth2", "api_key"), "https://slack.com/api", "https://api.slack.com/authentication/oauth-v2", "https://slack.com/oauth/v2/authorize", "https://slack.com/api/oauth.v2.access", "https://slack.com/api/auth.revoke", scopes=("chat:write", "channels:read", "users:read")),
        ProviderPreset("notion", "Notion", ("oauth2",), "https://api.notion.com", "https://developers.notion.com/reference/intro", "https://api.notion.com/v1/oauth/authorize", "https://api.notion.com/v1/oauth/token", scopes=("read_content", "update_content")),
        ProviderPreset("google-gmail", "Gmail", ("oauth2",), "https://gmail.googleapis.com", "https://developers.google.com/gmail/api", "https://accounts.google.com/o/oauth2/v2/auth", "https://oauth2.googleapis.com/token", "https://oauth2.googleapis.com/revoke", (*google_scopes, "https://www.googleapis.com/auth/gmail.modify")),
        ProviderPreset("google-calendar", "Google Calendar", ("oauth2",), "https://www.googleapis.com", "https://developers.google.com/calendar/api", "https://accounts.google.com/o/oauth2/v2/auth", "https://oauth2.googleapis.com/token", "https://oauth2.googleapis.com/revoke", (*google_scopes, "https://www.googleapis.com/auth/calendar")),
        ProviderPreset("microsoft-outlook", "Outlook Mail", ("oauth2",), "https://graph.microsoft.com", "https://learn.microsoft.com/graph/api/resources/mail-api-overview", "https://login.microsoftonline.com/common/oauth2/v2.0/authorize", "https://login.microsoftonline.com/common/oauth2/v2.0/token", scopes=("openid", "email", "offline_access", "Mail.Read", "Mail.Send")),
        ProviderPreset("stripe", "Stripe", ("api_key",), "https://api.stripe.com", "https://docs.stripe.com/api", credential_header="Authorization"),
        ProviderPreset("hubspot", "HubSpot", ("oauth2", "api_key"), "https://api.hubapi.com", "https://developers.hubspot.com/docs/api/overview", "https://app.hubspot.com/oauth/authorize", "https://api.hubapi.com/oauth/v1/token", scopes=("crm.objects.contacts.read", "crm.objects.contacts.write")),
        ProviderPreset("n8n", "n8n", ("api_key",), "https://n8n.example.com", "https://docs.n8n.io/api/", credential_header="X-N8N-API-KEY", api_key_header="X-N8N-API-KEY"),
    )
