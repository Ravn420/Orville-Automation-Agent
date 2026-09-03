from __future__ import annotations

from orville_core.browser import BrowserSession


class _Locator:
    def __init__(self, content: str | None = None):
        self.content = content
        self.first = self

    def get_attribute(self, _name: str):
        return self.content

    def inner_text(self, timeout: int = 0):
        return "Readable page text"


class _Page:
    url = "https://example.test/page"

    def title(self):
        return "Example page"

    def locator(self, selector: str):
        if selector.startswith("meta") and "description" in selector:
            return _Locator("A bounded description")
        if selector.startswith("link"):
            return _Locator("https://example.test/canonical")
        return _Locator()


def test_metadata_projection_includes_safe_source_reference() -> None:
    session = BrowserSession("browser-1", {"example.test"}, current_url="https://example.test/page", title="Example page")
    session._page = _Page()
    result = session.extract_page_metadata()
    assert result["title"] == "Example page"
    assert result["canonical_url"] == "https://example.test/canonical"
    assert result["source_reference"]["url"] == "https://example.test/page"
    assert len(result["text_excerpt"]) < 12_001
