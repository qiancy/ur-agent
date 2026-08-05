import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright


BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:5173")
API_BASE = os.getenv("E2E_API_BASE", "http://localhost:8000")
VIDEOS_DIR = Path(__file__).resolve().parent / "videos"
WATCHED_PREFIXES = ("/auth/", "/seller/")
SENSITIVE_KEYS = {"password", "access_token", "token"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("<redacted>" if key.lower() in SENSITIVE_KEYS else _redact(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _format_post_data(raw: str | None) -> str:
    if not raw:
        return "{}"
    try:
        return json.dumps(_redact(json.loads(raw)), ensure_ascii=False)
    except Exception:
        return "<non-json body>"


def _is_watched_url(url: str) -> bool:
    path = urlparse(url).path
    return any(path.startswith(prefix) for prefix in WATCHED_PREFIXES)


@pytest.fixture(scope="session")
def browser(pytestconfig) -> Browser:
    headed = bool(pytestconfig.getoption("--headed", default=False))
    slowmo_raw = pytestconfig.getoption("--slowmo", default="0")
    try:
        slowmo = int(slowmo_raw)
    except (TypeError, ValueError):
        slowmo = 0

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed, slow_mo=slowmo)
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture(scope="function")
def browser_context(browser: Browser) -> BrowserContext:
    """1440x900 recording context with request audit for auth/seller APIs."""
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        record_video_dir=str(VIDEOS_DIR),
        ignore_https_errors=True,
    )

    def audit_route(route):
        request = route.request
        if _is_watched_url(request.url):
            body = _format_post_data(request.post_data)
            print(f"[api-audit] {request.method} {request.url} body={body}")
        route.continue_()

    context.route("**/*", audit_route)
    try:
        yield context
    finally:
        context.close()


@pytest.fixture(scope="function")
def page(browser_context: BrowserContext) -> Page:
    page = browser_context.new_page()
    page.set_default_timeout(10_000)
    page.set_default_navigation_timeout(15_000)
    try:
        yield page
    finally:
        page.close()
