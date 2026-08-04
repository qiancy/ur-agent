import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page, expect

from conftest import API_BASE, BASE_URL

load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=False)


LOGIN = os.getenv("DEMO_RECORDING_LOGIN", "liuming")
PASSWORD = os.getenv("DEMO_LIUMING_PASSWORD", "").strip()
PERSONAL_OUID = os.getenv("DEMO_RECORDING_PERSONAL_OUID", "liuming_personal")
SHOP_OUID = os.getenv("DEMO_RECORDING_SHOP_OUID", "liuming_mingdeng_shop")
CAMPAIGN_OUID = os.getenv("DEMO_RECORDING_CAMPAIGN_OUID", "liuming_xinye_review")

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

if not PASSWORD:
    pytest.exit(
        "DEMO_LIUMING_PASSWORD 未设置（从仓库 .env 或环境变量读取）。"
        "密码不允许写死在测试/源码/文档中。",
    )


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


def _wait_for_space_view(page: Page, ctx: dict) -> None:
    if ctx.get("orgType") == "ecommerce":
        page.locator('[data-test="workbench"]').wait_for(state="visible", timeout=10_000)
    else:
        page.locator('[data-test="generic-space"]').wait_for(state="visible", timeout=10_000)


def _login(page: Page) -> dict:
    _goto_clean_login(page)
    page.locator('[data-test="login"]').fill(LOGIN)
    page.locator('[data-test="password"]').fill(PASSWORD)
    page.get_by_role("button", name=re.compile("登录")).click()
    page.locator('[data-test="app-header"]').wait_for(state="visible", timeout=10_000)
    ctx = page.evaluate("JSON.parse(localStorage.getItem('unires_ctx') || '{}')")
    _wait_for_space_view(page, ctx)
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
                    "response": "库存最低的商品是草船借箭纪念徽章，当前库存 3枚。",
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
    assert ctx["ouid"] == PERSONAL_OUID
    assert ctx["orgType"] == "personal"
    _assert_no_internal_keys(ctx)

    expect(page.locator('[data-test="generic-space"]')).to_be_visible()
    expect(page.locator('[data-test="ov-name"]')).to_contain_text("刘明的个人空间")
    expect(page.locator('[data-test="ov-type"]')).to_contain_text("personal")


@pytest.mark.recording
def test_02_header_no_ai_input_and_org_display(page: Page):
    _login(page)
    header = page.locator('[data-test="app-header"]')
    expect(header).to_be_visible()

    expect(header.locator("input")).to_have_count(0)
    expect(header.locator('[data-test*="ai" i]')).to_have_count(0)
    expect(header.get_by_text(re.compile("问\\s*AI|Seller AI", re.I))).to_have_count(0)

    expect(header).to_contain_text("刘明的个人空间")
    expect(header).to_contain_text("personal")
    expect(header).to_contain_text(LOGIN)


@pytest.mark.recording
def test_03_switch_organization_jwt_refresh(page: Page):
    _login(page)

    with page.expect_request(
        lambda req: req.method == "POST" and _path(req.url) == "/auth/switch-organization"
    ) as request_info:
        _switch_org(page, SHOP_OUID)

    request_body = json.loads(request_info.value.post_data or "{}")
    assert request_body == {"ouid": SHOP_OUID}
    _assert_no_internal_keys(request_body)

    page.locator('[data-test="workbench"]').wait_for(state="visible", timeout=10_000)
    expect(page.get_by_role("heading", name="经营工作台")).to_be_visible()

    ctx = page.evaluate("JSON.parse(localStorage.getItem('unires_ctx') || '{}')")
    assert ctx["ouid"] == SHOP_OUID
    assert ctx["orgType"] == "ecommerce"
    _assert_no_internal_keys(ctx)

    with page.expect_request(
        lambda req: req.method == "POST" and _path(req.url) == "/auth/switch-organization"
    ) as request_info:
        _switch_org(page, CAMPAIGN_OUID)
    assert json.loads(request_info.value.post_data or "{}") == {"ouid": CAMPAIGN_OUID}

    page.locator('[data-test="generic-space"]').wait_for(state="visible", timeout=10_000)
    expect(page.locator('[data-test="ov-name"]')).to_contain_text("新野火攻复盘空间")
    expect(page.locator('[data-test="ov-type"]')).to_contain_text("campaign")

    ctx = page.evaluate("JSON.parse(localStorage.getItem('unires_ctx') || '{}')")
    assert ctx["ouid"] == CAMPAIGN_OUID
    assert ctx["orgType"] == "campaign"
    _assert_no_internal_keys(ctx)


@pytest.mark.recording
def test_04_non_ecommerce_api_isolation(page: Page):
    _login(page)
    _switch_org(page, CAMPAIGN_OUID)
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

    expect(page.locator('[data-test="ov-name"]')).to_contain_text("新野火攻复盘空间")
    expect(page.locator('[data-test="ov-type"]')).to_contain_text("campaign")
    events_text = page.locator('[data-test="ov-events"]').inner_text()
    assert int(events_text) >= 8, f"ov-events={events_text} expected >= 8"

    expect(page.get_by_text("斥候确认曹军路线")).to_be_visible()
    expect(page.get_by_text("新野点火")).to_be_visible()
    expect(page.locator('[data-test="dim-info"]').first).to_be_visible()
    expect(page.locator('[data-test="dim-logistics"]').first).to_be_visible()
    expect(page.locator('[data-test="dim-people"]').first).to_be_visible()
    expect(page.locator('[data-test="flow-info"]')).to_contain_text("信息流")
    expect(page.locator('[data-test="flow-logistics"]')).to_contain_text("物流")
    expect(page.locator('[data-test="flow-people"]')).to_contain_text("人流")
    expect(page.locator('[data-test="group-knowledge"]')).to_contain_text("斥候简报")
    expect(page.locator('[data-test="group-physical"]')).to_contain_text("火油桶")


@pytest.mark.recording
def test_05_ecommerce_workbench_and_seller_ai(page: Page):
    _mock_seller_chat_if_requested(page)
    _login(page)

    _switch_org(page, SHOP_OUID)
    page.locator('[data-test="workbench"]').wait_for(state="visible", timeout=10_000)

    page.locator('button[data-view="stock"]').click()
    page.locator('[data-test="stock-view"]').wait_for(state="visible", timeout=10_000)
    page.get_by_text("星火羽扇礼盒").wait_for(state="visible", timeout=10_000)
    expect(page.locator('[data-test="stock-view"]')).to_contain_text("64")
    expect(page.locator('[data-test="stock-view"]')).to_contain_text("草船借箭纪念徽章")
    expect(page.locator('[data-test="stock-view"]')).to_contain_text("低库存")
    expect(page.locator('[data-test="stock-view"]')).to_contain_text("临界")

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
    expect(reply).to_contain_text(re.compile("草船借箭纪念徽章|3\\s*枚?"), timeout=30_000)
