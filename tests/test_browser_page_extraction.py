from orville_core.browser import BrowserSession


class _FakeLocator:
    def __init__(self, text="", metadata=None):
        self._text = text
        self._metadata = metadata or []

    def inner_text(self, **_kwargs):
        return self._text

    def evaluate_all(self, _script):
        return self._metadata


class _FakePage:
    url = "https://example.com/article"

    def title(self):
        return "Example Article"

    def locator(self, selector):
        if selector == "meta":
            return _FakeLocator(metadata=[{"name": "description", "property": None, "content": "Readable summary"}])
        return _FakeLocator(text="Heading\nReadable article text")


def test_extract_page_returns_title_text_metadata_and_source_reference():
    session = BrowserSession("browser-test", {"example.com"})
    session._ensure_page = lambda: _FakePage()

    result = session.extract_page()

    assert result["title"] == "Example Article"
    assert "Readable article text" in result["text"]
    assert result["metadata"][0]["name"] == "description"
    assert result["source_reference"]["url"] == "https://example.com/article"


def test_download_response_contains_source_reference_shape():
    session = BrowserSession("browser-test", {"example.com"})
    result = session.download("https://example.com/file.zip")
    assert result["takeover_required"] is True
    # Approval is intentionally required before any download source is touched.
    assert "approval_records" in result
