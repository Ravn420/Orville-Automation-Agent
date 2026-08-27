from __future__ import annotations

from orville_core.browser import BrowserSessionManager


def main() -> None:
    session = BrowserSessionManager().create(["example.com"], headless=True)
    pending = session.navigate("https://example.com", approved=False)
    assert pending["takeover_required"] is True
    result = session.navigate("https://example.com", approved=True)
    assert result["status"] == "active"
    assert result["current_url"].startswith("https://example.com")
    assert result["http_status"] == 200
    assert any(item["event"] == "navigation.approved" for item in result["audit"])
    session.close()
    print("browser runtime smoke passed")


if __name__ == "__main__":
    main()
