import json
import os
import re
from typing import Any
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Page, expect

from conftest import API_BASE, BASE_URL


LOGIN = os.getenv("DEMO_ZHANSAN_LOGIN", "zhansan")
PASSWORD = os.getenv("DEMO_ZHANSAN_PASSWORD", "demo123")
SHOP_OUID = "taobao_shop_a"
XINYE_OUID = "xinye_campaign"

INTERNAL_KEYS = {
    "id",
    "pid",
    "oid",
    "person" + "_id",
    "organization" + "_id",
    "membership" + "_id",
    "account" + "_id",
    "resource" + "_id",
    "warehouse" + "_id",
    "transaction" + "_id",
}


def _path(url: str) -> str:
    return urlparse(url).path


def _assert_no_internal_keys(obj: Any, path: str = "$") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            assert key not in INTERNAL_KEYS, f"{path}.{key} leaked an internal key"
            assert not key.endswith("_id"), f"{path}.{key} leaked an internal key"
            _assert_no_internal_keys(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            _assert_no_internal_keys(item, f"{path}[{index}]")


def _goto_clean_login(page: Page) -> None:
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="domcontentloaded")
    page.locator('[data-test="login-form"]').wait_for(state="visible", timeout=10_000)


def _login(page: Page) -> dict:
    _goto_clean_login(page)
    page.locator('[data-test="login"]').fill(LOGIN)
    page.locator('[data-test="password"]').fill(PASSWORD)
    page.get_by_role("button", name=re.compile("登录")).click()
    page.locator('[data-test="app-header"]').wait_for(state="visible", timeout=10_000)
    page.locator('[data-test="workbench"]').wait_for(state="visible", timeout=10_000)
    ctx = page.evaluate("JSON.parse(localStorage.getItem('unires_ctx') || '{}')")
    return ctx


def _switch_org(page: Page, ouid: str) -> None:
    page.locator('[data-test="org-switch"]').select_option(ouid)


def _mock_seller_chat_if_requested(page: Page) -> None:
    if os.getenv("E2E_FAKE_SELLER_CHAT", "").lower() not in {"1", "true", "yes"}:
        return

    def fulfill(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "response": "库存最低的商品是木牛流马模型，当前库存 12件。",
                    "ouid": SHOP_OUID,
                },
                ensure_ascii=False,
            ),
        )

    page.route(f"{API_BASE}/seller/chat", fulfill)


@pytest.mark.recording
def test_01_login_and_context_storage(page: Page):
    ctx = _login(page)

    assert ctx["puid"] == LOGIN
    assert ctx["ouid"] == SHOP_OUID
    assert ctx["orgType"] == "ecommerce"
    _assert_no_internal_keys(ctx)

    expect(page.locator('[data-test="workbench"]')).to_be_visible()
    expect(page.get_by_role("heading", name="经营工作台")).to_be_visible()


@pytest.mark.recording
def test_02_header_no_ai_input_and_org_display(page: Page):
    _login(page)
    header = page.locator('[data-test="app-header"]')
    expect(header).to_be_visible()

    expect(header.locator("input")).to_have_count(0)
    expect(header.locator('[data-test*="ai" i]')).to_have_count(0)
    expect(header.get_by_text(re.compile("问\\s*AI|Seller AI", re.I))).to_have_count(0)

    expect(header).to_contain_text("淘宝小店 A")
    expect(header).to_contain_text("ecommerce")
    expect(header).to_contain_text(LOGIN)


@pytest.mark.recording
def test_03_switch_organization_jwt_refresh(page: Page):
    _login(page)

    with page.expect_request(
        lambda req: req.method == "POST" and _path(req.url) == "/auth/switch-organization"
    ) as request_info:
        _switch_org(page, XINYE_OUID)

    request_body = json.loads(request_info.value.post_data or "{}")
    assert request_body == {"ouid": XINYE_OUID}
    _assert_no_internal_keys(request_body)

    page.locator('[data-test="generic-space"]').wait_for(state="visible", timeout=10_000)
    expect(page.locator('[data-test="ov-name"]')).to_contain_text("火烧新野战役")
    expect(page.locator('[data-test="ov-type"]')).to_contain_text("campaign")

    ctx = page.evaluate("JSON.parse(localStorage.getItem('unires_ctx') || '{}')")
    assert ctx["ouid"] == XINYE_OUID
    assert ctx["orgType"] == "campaign"
    _assert_no_internal_keys(ctx)


@pytest.mark.recording
def test_04_non_ecommerce_api_isolation(page: Page):
    _login(page)
    _switch_org(page, XINYE_OUID)
    page.locator('[data-test="generic-space"]').wait_for(state="visible", timeout=10_000)
    page.locator('[data-test="block-overview"]').wait_for(state="visible", timeout=10_000)

    observed_urls: list[str] = []
    page.on("request", lambda request: observed_urls.append(request.url))
    page.locator('[data-test="btn-refresh"]').click()
    page.locator('[data-test="ov-name"]').wait_for(state="visible", timeout=10_000)
    page.wait_for_load_state("networkidle", timeout=10_000)

    forbidden_paths = {"/seller/summary", "/seller/stock", "/seller/chat"}
    leaks = [
        url for url in observed_urls
        if _path(url) in forbidden_paths
    ]
    assert leaks == [], f"non-ecommerce space leaked seller API calls: {leaks}"


@pytest.mark.recording
def test_05_ecommerce_workbench_and_seller_ai(page: Page):
    _mock_seller_chat_if_requested(page)
    _login(page)

    _switch_org(page, XINYE_OUID)
    page.locator('[data-test="generic-space"]').wait_for(state="visible", timeout=10_000)
    _switch_org(page, SHOP_OUID)
    page.locator('[data-test="workbench"]').wait_for(state="visible", timeout=10_000)

    page.locator('button[data-view="stock"]').click()
    page.locator('[data-test="stock-view"]').wait_for(state="visible", timeout=10_000)
    page.get_by_text("诸葛亮联名羽扇").wait_for(state="visible", timeout=10_000)
    expect(page.locator('[data-test="stock-view"]')).to_contain_text("50")

    header_text = page.locator('[data-test="stock-view"] thead').inner_text()
    assert "数量" in header_text
    assert "商品编码" in header_text or "商品" in header_text
    assert not re.search(r"\b[a-z_]*id\b", header_text, re.I), header_text

    page.locator('button[data-view="chat"]').click()
    page.locator('[data-test="chat-view"]').wait_for(state="visible", timeout=10_000)
    page.locator('[data-test="chat-input"]').fill("库存最低的商品是什么？")

    with page.expect_request(
        lambda req: req.method == "POST" and _path(req.url) == "/seller/chat"
    ):
        page.locator('[data-test="chat-send"]').click()

    reply = page.locator('[data-test="messages"] .msg-ai').last
    expect(reply).to_contain_text(re.compile("木牛流马模型|12\\s*件?"), timeout=30_000)

