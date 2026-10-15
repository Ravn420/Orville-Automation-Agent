# Orville External Provider Integration Guide

**Version:** 1.0.0  
**Last Updated:** 2026-10-16  
**Audience:** Deployment teams, system administrators, security engineers  
**Scope:** External model provider and connector integrations

---

## Table of Contents

1. [Overview](#overview)
2. [Supported Providers](#supported-providers)
3. [Provider Status Matrix](#provider-status-matrix)
4. [Credential Requirements](#credential-requirements)
5. [OAuth Flow Documentation](#oauth-flow-documentation)
6. [Local Fallback Behavior](#local-fallback-behavior)
7. [Step-by-Step Onboarding Procedures](#step-by-step-onboarding-procedures)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Security Considerations](#security-considerations)
10. [References](#references)

---

## Overview

Orville supports multiple external provider integration patterns to enable flexible AI model access while maintaining security and operational control. This guide documents the supported providers, their authentication requirements, and the procedures for safe integration.

### Integration Patterns

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Local-Only** | No external credentials required; uses local models via Ollama | Air-gapped environments, maximum privacy |
| **User-Connected** | User supplies their own API credentials | Personal quotas, custom plans |
| **Managed Relay** | Orville service manages provider credentials | Enterprise deployments, centralized billing |
| **Hybrid** | Automatic fallback between local and cloud providers | Resilient deployments |

---

## Supported Providers

### Model Providers

| Provider | Type | Authentication | Default Endpoint |
|----------|------|----------------|------------------|
| **Ollama** | Local | None | `http://127.0.0.1:11434` |
| **Gemini** | Cloud | API Key | `https://generativeai.googleapis.com` |
| **Anthropic** | Cloud | API Key | `https://api.anthropic.com` |
| **Blackbox** | Cloud | API Key / Managed Relay | `https://api.blackbox.ai` |
| **Stable Horde** | Distributed | API Key | `https://aihorde.net/api` |
| **OpenAI-Compatible** | Local/Cloud | API Key (optional) | User-configured |

### Connector Providers (External Services)

| Provider | Authentication Modes | Base URL |
|----------|---------------------|----------|
| **GitHub** | OAuth2, API Key | `https://api.github.com` |
| **Slack** | OAuth2, API Key | `https://slack.com/api` |
| **Notion** | OAuth2 | `https://api.notion.com` |
| **Gmail** | OAuth2 | `https://gmail.googleapis.com` |
| **Google Calendar** | OAuth2 | `https://www.googleapis.com` |
| **Outlook Mail** | OAuth2 | `https://graph.microsoft.com` |
| **Stripe** | API Key | `https://api.stripe.com` |
| **HubSpot** | OAuth2, API Key | `https://api.hubapi.com` |
| **n8n** | API Key | User-configured |

---

## Provider Status Matrix

### Implementation Status

| Provider | Status | Credentials Required | OAuth Available | Local Fallback |
|----------|--------|---------------------|-----------------|----------------|
| Ollama | ✅ Production | No | N/A | N/A (always local) |
| Gemini | ✅ Production | Yes | No | ✅ Yes |
| Anthropic | ✅ Production | Yes | No | ✅ Yes |
| Blackbox (API Key) | ✅ Production | Yes | ❌ No* | ✅ Yes |
| Blackbox (Managed) | ✅ Production | Server-side only | N/A | ✅ Yes |
| Stable Horde | ✅ Production | Yes | No | ✅ Yes |
| OpenAI-Compatible | ✅ Production | Optional | No | ✅ Yes |
| GitHub Connector | ✅ Production | Yes | ✅ Yes | N/A |
| Slack Connector | ✅ Production | Yes | ✅ Yes | N/A |
| Notion Connector | ✅ Production | Yes | ✅ Yes | N/A |
| Google Connectors | ✅ Production | Yes | ✅ Yes | N/A |
| Microsoft Connectors | ✅ Production | Yes | ✅ Yes | N/A |
| Stripe Connector | ✅ Production | Yes | No | N/A |
| HubSpot Connector | ✅ Production | Yes | ✅ Yes | N/A |
| n8n Connector | ✅ Production | Yes | No | N/A |

\* Blackbox does not currently offer an official third-party OAuth flow. See [OAuth Flow Documentation](#oauth-flow-documentation) for details.

---

## Credential Requirements

### Model Provider Credentials

#### Ollama (Local)
- **Requirements:** None
- **Setup:** Install Ollama locally; Orville connects to default endpoint
- **Security:** Local network only; no credentials to manage

#### Gemini
- **Requirements:** Google AI Studio API key
- **Obtain:** https://aistudio.google.com/app/apikey
- **Storage:** OS credential store (Windows DPAPI) or Fernet-encrypted
- **Header:** `Authorization: Bearer <api_key>`

#### Anthropic
- **Requirements:** Anthropic API key
- **Obtain:** https://console.anthropic.com/settings/keys
- **Storage:** OS credential store or Fernet-encrypted
- **Header:** `Authorization: Bearer <api_key>`

#### Blackbox
- **Requirements:** Blackbox API key + Pro subscription for Agent API
- **Obtain:** Blackbox dashboard (https://www.blackbox.ai)
- **Storage:** Server-side only for managed mode; OS credential store for user-connected
- **Header:** `Authorization: Bearer <api_key>`
- **Endpoints:**
  - Public: `https://api.blackbox.ai`
  - Enterprise: `https://enterprise.blackbox.ai`

#### Stable Horde
- **Requirements:** AI Horde API key (optional for anonymous, recommended for priority)
- **Obtain:** https://aihorde.net/register
- **Storage:** OS credential store or Fernet-encrypted
- **Header:** `apikey: <api_key>`

### Connector Credentials

#### API Key Authentication

| Provider | Header Name | Key Format |
|----------|-------------|------------|
| Stripe | `Authorization` | `Bearer sk_live_...` or `Bearer sk_test_...` |
| n8n | `X-N8N-API-KEY` | User-defined |
| GitHub (API Key) | `Authorization` | `Bearer ghp_...` or `token <token>` |
| Slack (API Key) | `Authorization` | `Bearer xoxb-...` |
| HubSpot (API Key) | `Authorization` | `Bearer <api_key>` |

#### OAuth2 Authentication

| Provider | Authorization URL | Token URL | Scopes |
|----------|-------------------|-----------|--------|
| GitHub | `https://github.com/login/oauth/authorize` | `https://github.com/login/oauth/access_token` | `read:user`, `repo` |
| Slack | `https://slack.com/oauth/v2/authorize` | `https://slack.com/api/oauth.v2.access` | `chat:write`, `channels:read`, `users:read` |
| Notion | `https://api.notion.com/v1/oauth/authorize` | `https://api.notion.com/v1/oauth/token` | `read_content`, `update_content` |
| Gmail | `https://accounts.google.com/o/oauth2/v2/auth` | `https://oauth2.googleapis.com/token` | `openid`, `email`, `profile`, `https://www.googleapis.com/auth/gmail.modify` |
| Google Calendar | `https://accounts.google.com/o/oauth2/v2/auth` | `https://oauth2.googleapis.com/token` | `openid`, `email`, `profile`, `https://www.googleapis.com/auth/calendar` |
| Outlook | `https://login.microsoftonline.com/common/oauth2/v2.0/authorize` | `https://login.microsoftonline.com/common/oauth2/v2.0/token` | `openid`, `email`, `offline_access`, `Mail.Read`, `Mail.Send` |
| HubSpot | `https://app.hubspot.com/oauth/authorize` | `https://api.hubapi.com/oauth/v1/token` | `crm.objects.contacts.read`, `crm.objects.contacts.write` |

---

## OAuth Flow Documentation

### Current OAuth Support

Orville implements standard OAuth2 authorization code flow for supported connectors. The following providers support OAuth2:

- GitHub
- Slack
- Notion
- Google (Gmail, Calendar)
- Microsoft (Outlook)
- HubSpot

### Blackbox OAuth Status

**⚠️ Important:** As of the latest research (2026-08-27), **Blackbox does not offer an official third-party OAuth or device-authorization flow** for external applications.

#### Verified Findings

Based on official Blackbox documentation review:

| Aspect | Status | Evidence |
|--------|--------|----------|
| Third-party OAuth | ❌ Not documented | No OAuth endpoints in public API docs |
| Device authorization | ❌ Not documented | No device flow in CLI or API docs |
| API Key authentication | ✅ Required | `Authorization: Bearer <api_key>` header |
| CLI token reuse | ❌ Not supported | CLI requires separate configuration |

#### Implications

1. **Do not implement browser cookie capture** - This is not a supported authentication method
2. **Do not use "Sign in with Blackbox"** - Use "Connect Blackbox API key" instead
3. **API key is the only documented integration path** - Until Blackbox publishes OAuth documentation

#### Open Questions for Blackbox

The following questions remain unverified and require Blackbox confirmation:

1. Does Blackbox offer an official third-party OAuth authorization-code flow?
2. Does Blackbox offer a device-code flow suitable for desktop applications?
3. Can an official Blackbox CLI login session be used by another application?
4. What scopes are available for API, Agent API, GitHub, workspace files?
5. What subscription and usage limits apply to each endpoint?
6. What are the rate limits, retry requirements, and idempotency rules?
7. Are API keys intended for desktop-client distribution?
8. What privacy, retention, training, and data-location guarantees apply?

### OAuth Flow Implementation

For providers that support OAuth2, Orville implements the following flow:

```
┌─────────┐                                    ┌──────────┐
│  User   │──(1) Initiate OAuth──▶│  Orville │
└─────────┘                                    └──────────┘
                                                    │
                                                    ▼
┌─────────┐                                    ┌──────────┐
│  User   │◀──(2) Redirect to Provider──│  Orville │
└─────────┘                                    └──────────┘
    │
    ▼
┌─────────┐
│Provider │──(3) User Authorizes──▶
│  OAuth  │◀──(4) Authorization Code──
│ Server  │
└─────────┘
    │
    ▼
┌─────────┐                                    ┌──────────┐
│  User   │──(5) Return with Code────▶│  Orville │
└─────────┘                                    └──────────┘
                                                    │
                                                    ▼
                                              ┌──────────┐
                                              │  Orville │──(6) Exchange Code for Token──▶ Provider
                                              │  Server  │◀──(7) Access/Refresh Tokens───
                                              └──────────┘
                                                    │
                                                    ▼
                                              ┌──────────┐
                                              │  Secure  │
                                              │ Storage  │
                                              └──────────┘
```

---

## Local Fallback Behavior

### Fallback Policy Overview

When a cloud provider is unavailable or not configured, Orville automatically falls back to local providers to ensure continuous operation.

### Fallback Decision Matrix

| Primary Provider Status | Action | Fallback Provider |
|------------------------|--------|-------------------|
| `ready` | Use primary | None (primary active) |
| `not_connected` | Fallback to local | First configured local provider |
| `expired` | Fallback to local | First configured local provider |
| `invalid` | Fallback to local | First configured local provider |
| `rate_limited` | Fallback to local | First configured local provider |
| `unavailable` | Fallback to local | First configured local provider |
| `disabled` | Fallback to local | First configured local provider |

### Fallback Provider Selection

The `BlackboxFallbackPolicy` selects the first explicitly configured local provider as a fallback candidate:

1. **Ollama** (if configured)
2. **Custom Local** (OpenAI-compatible local endpoint)
3. **Stable Horde** (if configured for local-like operation)

If no local provider exists, the system returns an actionable unavailable state instructing the operator to configure a local provider or repair the relay.

### Fallback Status Response

Public fallback status contains only:
- `state`: Current fallback state
- `provider_id`: Selected fallback provider ID
- `available`: Whether fallback is available
- `remediation`: Actionable guidance text

**Credentials are never included in fallback status responses.**

### Privacy Class Handling

| Privacy Class | Remote Execution | Fallback Behavior |
|---------------|------------------|-------------------|
| `local_only` | ❌ Never | Always use local |
| `cloud_approved` | ✅ Allowed | Fallback if cloud unavailable |
| `restricted` | ⚠️ Requires explicit approval | Fallback if not approved |

---

## Step-by-Step Onboarding Procedures

### Procedure 1: Local-Only Setup (No Credentials)

**Use Case:** Air-gapped environments, maximum privacy, no external dependencies

1. **Install Ollama**
   ```bash
   # Windows
   winget install Ollama.Ollama
   
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Start Ollama Service**
   ```bash
   ollama serve
   ```

3. **Pull Required Models**
   ```bash
   ollama pull llama3.2
   ollama pull codellama
   ```

4. **Configure Orville**
   - Open Orville GUI
   - Navigate to **Provider Setup**
   - Select **Ollama** preset
   - Verify endpoint: `http://127.0.0.1:11434`
   - Click **Test Provider Health**
   - Save configuration

5. **Verify Operation**
   ```bash
   python -m pytest tests/test_providers.py -v
   ```

### Procedure 2: User-Connected Cloud Provider

**Use Case:** Personal API keys, custom quotas, direct provider billing

1. **Obtain API Key**
   - Visit provider's developer console
   - Generate new API key
   - Copy key to secure location (do not commit)

2. **Open Orville Provider Setup**
   - Launch Orville GUI
   - Click **Provider Setup** in sidebar
   - Select provider type (Gemini, Anthropic, etc.)

3. **Configure Provider**
   - Enter provider ID (e.g., `gemini-primary`)
   - Verify default endpoint URL
   - Enter model name (e.g., `gemini-2.5-flash`)
   - Paste API key in secure field
   - Set timeout (default: 60s)
   - Select capabilities (text, code, streaming, etc.)

4. **Test Connection**
   - Click **Test Provider Health**
   - Verify green status indicator
   - Review redacted response

5. **Save Configuration**
   - Click **Save Provider**
   - API key is encrypted and stored in OS credential store
   - Key is cleared from form after submission

### Procedure 3: Managed Blackbox Relay (Enterprise)

**Use Case:** Enterprise deployments, centralized billing, credential isolation

1. **Deploy Relay Service**
   ```bash
   # Server-side configuration
   export BLACKBOX_API_KEY="server-only-key"
   export ORVILLE_RELAY_CLIENT_TOKEN="high-entropy-client-token"
   python tools/run_blackbox_relay.py
   ```

2. **Configure Desktop Client**
   Set environment variables:
   ```bash
   ORVILLE_BLACKBOX_RELAY_URL=https://relay.example.com/v1
   ORVILLE_BLACKBOX_RELAY_ALLOWED_HOSTS=relay.example.com
   ORVILLE_BLACKBOX_RELAY_MODEL=blackboxai/openai/gpt-5.5
   ORVILLE_BLACKBOX_RELAY_ENABLED=1
   ORVILLE_BLACKBOX_RELAY_PLAN=managed
   ORVILLE_RELAY_SUBJECT=device-or-session-id
   ```

3. **Verify Relay Status**
   ```bash
   curl -H "Authorization: Bearer $ORVILLE_RELAY_CLIENT_TOKEN" \
        https://relay.example.com/v1/cloud/blackbox/status
   ```

4. **Test Managed Access**
   - Open Orville GUI
   - Navigate to **Cloud Status**
   - Verify managed mode shows `ready`
   - Test inference request

### Procedure 4: Connector OAuth Setup

**Use Case:** External service integration (GitHub, Slack, etc.)

1. **Initiate OAuth Flow**
   - Open Orville GUI
   - Navigate to **Connectors**
   - Select connector (e.g., GitHub)
   - Click **Connect with OAuth**

2. **Authorize Application**
   - Browser opens to provider OAuth page
   - Review requested scopes
   - Click **Authorize**

3. **Complete Connection**
   - Return to Orville
   - Verify connection status shows `connected`
   - Test connector health

4. **Manage Connection**
   - View connected scopes
   - Disconnect if needed
   - Rotate credentials periodically

### Procedure 5: Connector API Key Setup

**Use Case:** Server-to-server integration, automated workflows

1. **Generate API Key**
   - Visit provider's developer settings
   - Create new API key/token
   - Copy key immediately (may not be shown again)

2. **Configure in Orville**
   - Open **Connectors** panel
   - Select connector type
   - Choose **API Key** authentication
   - Paste key in secure field
   - Click **Save**

3. **Verify Connection**
   - Click **Test Connection**
   - Review permissions granted
   - Confirm operational status

---

## Troubleshooting Guide

### Common Issues

#### Issue: Provider shows `not_connected`

**Symptoms:**
- Provider status shows red indicator
- Health check fails
- Cannot execute remote tasks

**Diagnosis:**
```bash
# Check provider status
curl -H "Authorization: Bearer $ORVILLE_API_TOKEN" \
     http://localhost:8787/api/v1/providers/{provider_id}/health
```

**Solutions:**
1. Verify API key is configured: Check OS credential store
2. Test endpoint connectivity: `curl <provider_endpoint>`
3. Verify API key validity with provider's test endpoint
4. Check firewall/proxy settings
5. Review provider-specific error codes below

#### Issue: Blackbox returns 401 Unauthorized

**Symptoms:**
- HTTP 401 error from Blackbox
- "Invalid API key" message

**Solutions:**
1. Verify API key is active in Blackbox dashboard
2. Check key has not expired or been revoked
3. Ensure Pro subscription is active (for Agent API)
4. Regenerate key if necessary
5. Update stored credential in Orville

#### Issue: Blackbox returns 403 Forbidden

**Symptoms:**
- HTTP 403 error from Blackbox
- "Insufficient plan access" message

**Solutions:**
1. Verify active Pro subscription
2. Check model access permissions
3. Review usage limits and quotas
4. Contact Blackbox support if plan issues persist

#### Issue: Blackbox returns 429 Rate Limited

**Symptoms:**
- HTTP 429 error
- "Too many requests" message

**Solutions:**
1. Implement exponential backoff
2. Check rate limit headers in response
3. Reduce request frequency
4. Contact provider to increase limits
5. Enable local fallback for resilience

#### Issue: OAuth flow fails

**Symptoms:**
- Cannot complete OAuth authorization
- "Invalid state" or "Code expired" errors

**Solutions:**
1. Clear browser cookies for provider domain
2. Restart OAuth flow
3. Check system clock is synchronized
4. Verify redirect URI is registered correctly
5. Ensure OAuth app is not suspended

#### Issue: Local fallback not working

**Symptoms:**
- Cloud provider fails
- No fallback to local provider
- Tasks fail with "no provider available"

**Solutions:**
1. Verify local provider is configured:
   ```bash
   curl http://localhost:11434/api/tags  # Ollama
   ```
2. Check local provider health in Orville GUI
3. Verify fallback policy configuration
4. Ensure at least one local provider has `enabled: true`

#### Issue: Credentials not persisting

**Symptoms:**
- API key required on every restart
- "Credential not found" errors

**Solutions (Windows):**
1. Verify Windows Credential Manager is accessible
2. Check DPAPI is functioning: `certutil -user -store MY`
3. Ensure user has permission to write to credential store

**Solutions (Non-Windows):**
1. Verify `ORVILLE_CONNECTOR_MASTER_KEY` is set
2. Check key is valid Fernet key (32-byte base64)
3. Ensure key is injected from secure source, not hardcoded

### Error Code Reference

| Error Code | Meaning | Action |
|------------|---------|--------|
| `401` | Authentication failed | Check API key, reconnect provider |
| `402` | Payment required | Check subscription/billing status |
| `403` | Forbidden | Check permissions, plan access |
| `404` | Not found | Verify endpoint URL, model ID |
| `429` | Rate limited | Retry after delay, reduce frequency |
| `500` | Provider error | Retry, contact provider if persistent |
| `503` | Service unavailable | Enable fallback, retry later |

### Diagnostic Commands

```bash
# Test Ollama connectivity
curl http://localhost:11434/api/tags

# Test provider health via Orville API
curl -H "Authorization: Bearer $ORVILLE_API_TOKEN" \
     http://localhost:8787/api/v1/providers/{provider_id}/health

# Check Blackbox relay status
curl -H "Authorization: Bearer $ORVILLE_API_TOKEN" \
     http://localhost:8787/api/v1/cloud/blackbox/status

# List configured providers
curl -H "Authorization: Bearer $ORVILLE_API_TOKEN" \
     http://localhost:8787/api/v1/providers

# View provider usage metrics
curl -H "Authorization: Bearer $ORVILLE_API_TOKEN" \
     http://localhost:8787/api/v1/provider-usage/{provider_id}
```

---

## Security Considerations

### Credential Storage

| Platform | Storage Method | Encryption |
|----------|---------------|------------|
| Windows | Windows Credential Manager (DPAPI) | AES-256 |
| macOS | Keychain (via Fernet) | AES-128-CBC |
| Linux | File-based (via Fernet) | AES-128-CBC |

### Security Best Practices

1. **Never commit credentials to source control**
   - API keys, OAuth tokens, and passwords must never be in code
   - Use environment variables or secure secret managers

2. **Use OS credential store when available**
   - Windows: DPAPI-protected credential manager
   - Non-Windows: Fernet with runtime-only master key

3. **Rotate credentials regularly**
   - Set calendar reminders for key rotation
   - Revoke old keys after rotation
   - Monitor for unauthorized usage

4. **Implement least privilege**
   - Request minimum required OAuth scopes
   - Use read-only keys where possible
   - Restrict API key permissions

5. **Monitor and audit**
   - Review provider usage metrics
   - Set up alerts for unusual activity
   - Maintain audit logs of credential operations

6. **Secure fallback configuration**
   - Local fallback prevents data exfiltration
   - Privacy classes control data routing
   - Explicit approval required for sensitive operations

### Data Privacy

| Privacy Mode | Data Leaves Device | Use Case |
|--------------|-------------------|----------|
| `local_only` | ❌ Never | Sensitive code, proprietary data |
| `cloud_approved` | ✅ Yes (approved) | General tasks, public data |
| `restricted` | ⚠️ Requires explicit approval | Mixed sensitivity |

### Compliance Notes

- **GDPR:** User-connected credentials are user data; provide export/deletion
- **SOC 2:** Audit all credential operations; rotate regularly
- **HIPAA:** Use `local_only` mode for PHI; encrypt at rest
- **PCI-DSS:** Never store payment credentials; use tokenization

---

## References

### Internal Documentation

- [BLACKBOX_INTEGRATION.md](BLACKBOX_INTEGRATION.md) - Blackbox integration details
- [BLACKBOX_INTEGRATION_RESEARCH.md](BLACKBOX_INTEGRATION_RESEARCH.md) - Research findings
- [PROVIDER_SETUP_WORKFLOW.md](PROVIDER_SETUP_WORKFLOW.md) - GUI setup workflow
- [PROVIDER_OPERATIONS_ENTERPRISE.md](PROVIDER_OPERATIONS_ENTERPRISE.md) - Enterprise operations
- [MODEL_PROVIDERS.md](../MODEL_PROVIDERS.md) - Model provider layer
- [API_BRIDGE.md](../API_BRIDGE.md) - API bridge documentation

### External Documentation

- [Blackbox API Docs](https://docs.blackbox.ai/api-reference/introduction)
- [Blackbox Agent API](https://docs.blackbox.ai/api-reference/v1/introduction)
- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/README.md)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [Anthropic API](https://docs.anthropic.com/en/api/getting-started)
- [AI Horde Documentation](https://aihorde.net/api)

### Support

For provider-specific issues:
1. Check provider's status page
2. Review provider's API documentation
3. Contact provider support with error details

For Orville-specific issues:
1. Review this guide
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. File issue with logs and reproduction steps

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-10-16 | Initial release |

---

**Note:** This document is a living guide. Provider capabilities and authentication methods change over time. Always verify current provider documentation before implementation.
