from __future__ import annotations

import pytest

from orville_core.browser_relay import BrowserRelayError, LocalBrowserRelay


def test_pair_navigation_and_revocation():
    relay = LocalBrowserRelay(ttl_seconds=60)
    session, secret = relay.pair("Chrome work profile", ["example.com"])
    assert relay.validate_navigation(session.session_id, secret, "https://app.example.com/path").session_id == session.session_id
    with pytest.raises(BrowserRelayError, match="outside"):
        relay.validate_navigation(session.session_id, secret, "https://evil.example.net")
    called = []
    assert relay.dispatch(session.session_id, secret, "extract", {"selector": "main"}, lambda action, payload: called.append((action, payload)) or "ok") == "ok"
    with pytest.raises(BrowserRelayError, match="explicit approval"):
        relay.dispatch(session.session_id, secret, "takeover_request", {}, lambda *_: None)
    assert relay.dispatch(session.session_id, secret, "takeover_request", {"approved": True}, lambda action, payload: action) == "takeover_request"
    revoked = relay.revoke(session.session_id, secret)
    assert revoked.active is False
    with pytest.raises(BrowserRelayError, match="expired or inactive"):
        relay.validate_navigation(session.session_id, secret, "https://example.com")
