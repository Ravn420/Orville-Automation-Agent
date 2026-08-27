"""Fail-closed local browser sessions for user-approved research and takeover."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from tempfile import gettempdir
from urllib.parse import urlparse
from uuid import uuid4

from .security import SecurityViolation


@dataclass
class BrowserSession:
    session_id: str
    allowed_domains: set[str]
    headless: bool = True
    download_root: str = field(default_factory=lambda: str(Path(gettempdir()) / "orville-browser-downloads"))
    status: str = "created"
    current_url: str | None = None
    title: str | None = None
    takeover_required: bool = False
    audit: list[dict[str, str]] = field(default_factory=list)
    _playwright: object | None = field(default=None, repr=False)
    _browser: object | None = field(default=None, repr=False)
    _context: object | None = field(default=None, repr=False)
    _page: object | None = field(default=None, repr=False)

    def record(self, event: str, detail: str = "") -> None:
        self.audit.append({"at": datetime.now(UTC).isoformat(), "event": event, "detail": detail[:1000]})

    def check_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise SecurityViolation("browser navigation requires an http(s) URL")
        hostname = parsed.hostname.lower().rstrip(".")
        if not any(hostname == domain or hostname.endswith("." + domain) for domain in self.allowed_domains):
            self.record("navigation.blocked", hostname)
            raise SecurityViolation(f"browser domain is not allowlisted: {hostname}")

    def _ensure_page(self) -> object:
        if self._page is not None:
            return self._page
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("browser runtime unavailable; install the playwright optional dependency") from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(accept_downloads=True)
        self._page = self._context.new_page()
        return self._page

    def navigate(self, url: str, *, approved: bool = False) -> dict[str, object]:
        self.check_url(url)
        if not approved:
            self.takeover_required = True
            self.record("navigation.approval_required", url)
            return self.to_dict()
        page = self._ensure_page()
        response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        self.current_url = page.url
        self.title = page.title()
        self.status = "active"
        self.takeover_required = False
        self.record("navigation.approved", self.current_url)
        return {**self.to_dict(), "http_status": response.status if response else None, "text_excerpt": page.locator("body").inner_text(timeout=5_000)[:12_000]}

    def submit_form(self, selector: str, fields: dict[str, str], *, approved: bool = False) -> dict[str, object]:
        if not selector.strip() or not fields:
            raise ValueError("form submission requires a selector and fields")
        if not approved:
            self.takeover_required = True
            self.record("form_submission.approval_required", f"selector={selector}; fields={','.join(sorted(fields))}")
            return self.to_dict()
        page = self._ensure_page()
        for name, value in fields.items():
            page.locator(selector).get_by_label(name).fill(value)
        page.locator(selector).locator("button[type=submit], input[type=submit]").first.click()
        self.status = "active"
        self.takeover_required = False
        self.record("form_submission.approved", f"selector={selector}; fields={','.join(sorted(fields))}")
        return {**self.to_dict(), "text_excerpt": page.locator("body").inner_text(timeout=5_000)[:12_000]}

    def download(self, url: str, *, approved: bool = False) -> dict[str, object]:
        self.check_url(url)
        if not approved:
            self.takeover_required = True
            self.record("download.approval_required", url)
            return self.to_dict()
        page = self._ensure_page()
        destination = Path(self.download_root)
        destination.mkdir(parents=True, exist_ok=True)
        with page.expect_download(timeout=30_000) as download_info:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            except Exception as exc:  # Playwright raises when navigation becomes a download.
                if "Download is starting" not in str(exc):
                    raise
        download = download_info.value
        filename = Path(download.suggested_filename).name
        target = destination / filename
        download.save_as(target)
        self.takeover_required = False
        self.status = "active"
        self.record("download.approved", f"{url} -> {filename}")
        return {**self.to_dict(), "download": {"name": filename, "path": str(target), "url": url}}

    def request_takeover(self, *, approved: bool = False) -> dict[str, object]:
        if not approved:
            self.takeover_required = True
            self.record("takeover.requested")
            return self.to_dict()
        if self._browser is not None:
            self.record("takeover.approved", "existing browser remains in current mode")
            self.status = "user_takeover"
            self.takeover_required = False
            return self.to_dict()
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("browser runtime unavailable; install the playwright optional dependency") from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=False)
        self._context = self._browser.new_context(accept_downloads=True)
        self._page = self._context.new_page()
        self.status = "user_takeover"
        self.takeover_required = False
        self.record("takeover.approved", "visible browser launched")
        return self.to_dict()

    def close(self, *, final: bool = True) -> dict[str, object]:
        for resource in (self._context, self._browser, self._playwright):
            if resource is not None:
                try:
                    resource.close()
                except Exception:
                    pass
        if final:
            self.status = "closed"
            self.record("session.closed")
        else:
            self.record("browser.handle_closed")
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        return self.to_dict()

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "allowed_domains": sorted(self.allowed_domains),
            "headless": self.headless,
            "download_root": self.download_root,
            "status": self.status,
            "current_url": self.current_url,
            "title": self.title,
            "takeover_required": self.takeover_required,
            "audit": list(self.audit[-100:]),
        }


class BrowserSessionManager:
    def __init__(self, state_path: str | Path | None = None) -> None:
        self.sessions: dict[str, BrowserSession] = {}
        self.state_path = Path(state_path).expanduser().resolve() if state_path else None
        self._load()

    def _load(self) -> None:
        if not self.state_path or not self.state_path.exists():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        for item in payload if isinstance(payload, list) else []:
            try:
                session = BrowserSession(str(item["session_id"]), set(item["allowed_domains"]), bool(item.get("headless", True)), str(item.get("download_root", str(Path(gettempdir()) / "orville-browser-downloads"))), "recovered", item.get("current_url"), item.get("title"), True, list(item.get("audit", [])))
                session.record("session.recovered", "browser handles require explicit restart approval")
                self.sessions[session.session_id] = session
            except (KeyError, TypeError, ValueError):
                continue

    def persist(self) -> None:
        if not self.state_path:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [session.to_dict() for session in self.sessions.values() if session.status != "closed"]
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.state_path)

    def shutdown(self) -> None:
        for session in tuple(self.sessions.values()):
            if session.status not in {"closed", "recovered"}:
                session.status = "recovered"
                session.takeover_required = True
                session.record("session.shutdown", "browser handles closed; explicit recovery required")
            session.close(final=False)
        self.persist()

    @staticmethod
    def normalize_domains(domains: list[str]) -> set[str]:
        normalized: set[str] = set()
        for raw in domains:
            value = raw.strip().lower().rstrip(".")
            if not value or "://" in value or "/" in value or not re.fullmatch(r"[a-z0-9.-]+", value):
                raise ValueError(f"invalid browser allowlist domain: {raw}")
            normalized.add(value)
        if not normalized:
            raise ValueError("browser allowlist must contain at least one domain")
        return normalized

    def create(self, domains: list[str], *, headless: bool = True) -> BrowserSession:
        session = BrowserSession(f"browser-{uuid4().hex[:12]}", self.normalize_domains(domains), headless=headless)
        session.record("session.created", "read-only navigation default")
        self.sessions[session.session_id] = session
        self.persist()
        return session

    def get(self, session_id: str) -> BrowserSession:
        try:
            return self.sessions[session_id]
        except KeyError as exc:
            raise KeyError(f"browser session not found: {session_id}") from exc
