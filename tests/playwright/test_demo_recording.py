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
# 每个数据屏加载完成后停留的毫秒数，便于录屏观众看清数据（默认 4s）。
HOLD_MS = int(os.getenv("E2E_HOLD_MS", "4000"))

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


def _hold(page: Page) -> None:
    """停留几秒，让录屏观众能看清刚加载出来的数据。"""
    if HOLD_MS > 0:
        page.wait_for_timeout(HOLD_MS)


def _read_ctx(page: Page) -> dict:
    return page.evaluate("JSON.parse(localStorage.getItem('unires_ctx') || '{}')")


def _login(page: Page) -> dict:
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="domcontentloaded")
    page.locator('[data-test="login-form"]').wait_for(state="visible", timeout=10_000)
    page.locator('[data-test="login"]').fill(LOGIN)
    page.locator('[data-test="password"]').fill(PASSWORD)
    page.get_by_role("button", name=re.compile("登录")).click()
    page.locator('[data-test="app-header"]').wait_for(state="visible", timeout=10_000)
    ctx = _read_ctx(page)
    view = '[data-test="workbench"]' if ctx.get("orgType") == "ecommerce" \
        else '[data-test="generic-space"]'
    page.locator(view).wait_for(state="visible", timeout=10_000)
    return ctx


def _switch_org(page: Page, ouid: str) -> dict:
    with page.expect_request(
        lambda req: req.method == "POST" and _path(req.url) == "/auth/switch-organization"
    ) as request_info:
        page.locator('[data-test="org-switch"]').select_option(ouid)
    body = json.loads(request_info.value.post_data or "{}")
    assert body == {"ouid": ouid}, f"switch request must be {{ouid}} only, got {body}"
    _assert_no_internal_keys(body)
    ctx = _read_ctx(page)
    return ctx


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
def test_recording_main_flow(page: Page):
    """录屏主流程：只登录一次，Header 切换全部业务空间。

    1. 登录 liuming，默认进入 刘明的个人空间 (personal)。
    2. Header 无 AI 输入框，只显示用户/空间/类型/角色。
    3. Header 切到 明灯文创小店，进入 Seller 工作台。
    4. 展示库存（低库存/临界）、库存流水、经营摘要、Seller AI（数据停留给观众看）。
    5. Header 切到 新野火攻复盘空间，展示 8 条时间线与信息流/物流/人流。
    6. 回到电商空间，总结多空间隔离（全程只有一次登录）。
    """
    _mock_seller_chat_if_requested(page)

    # ── 1. 登录一次，默认进入个人空间 ─────────────────────────────
    ctx = _login(page)
    assert ctx["puid"] == LOGIN
    assert ctx["ouid"] == PERSONAL_OUID
    assert ctx["orgType"] == "personal"
    _assert_no_internal_keys(ctx)

    expect(page.locator('[data-test="generic-space"]')).to_be_visible()
    expect(page.locator('[data-test="ov-name"]')).to_contain_text("刘明的个人空间")
    expect(page.locator('[data-test="ov-type"]')).to_contain_text("personal")
    page.locator('[data-test="block-overview"]').wait_for(state="visible", timeout=10_000)
    _hold(page)

    # ── 2. Header 去 AI 化 + 空间展示 ─────────────────────────────
    header = page.locator('[data-test="app-header"]')
    expect(header).to_be_visible()
    expect(header.locator("input")).to_have_count(0)
    expect(header.locator('[data-test*="ai" i]')).to_have_count(0)
    expect(header.get_by_text(re.compile("问\\s*AI|Seller AI", re.I))).to_have_count(0)
    expect(header).to_contain_text("刘明的个人空间")
    expect(header).to_contain_text("personal")
    expect(header).to_contain_text(LOGIN)

    # ── 3. 切到 明灯文创小店（Seller 工作台） ─────────────────────
    ctx = _switch_org(page, SHOP_OUID)
    assert ctx["ouid"] == SHOP_OUID
    assert ctx["orgType"] == "ecommerce"
    _assert_no_internal_keys(ctx)
    page.locator('[data-test="workbench"]').wait_for(state="visible", timeout=10_000)
    expect(page.get_by_role("heading", name="经营工作台")).to_be_visible()

    # ── 4. 库存：6 商品 + 低库存/临界 ─────────────────────────────
    page.locator('button[data-view="stock"]').click()
    page.locator('[data-test="stock-view"]').wait_for(state="visible", timeout=10_000)
    page.get_by_text("星火羽扇礼盒").wait_for(state="visible", timeout=10_000)
    expect(page.locator('[data-test="stock-view"]')).to_contain_text("64")
    expect(page.locator('[data-test="stock-view"]')).to_contain_text("草船借箭纪念徽章")
    expect(page.locator('[data-test="stock-view"]')).to_contain_text("低库存")
    expect(page.locator('[data-test="stock-view"]')).to_contain_text("临界")
    stock_header = page.locator('[data-test="stock-view"] thead').inner_text()
    assert "数量" in stock_header
    assert "商品编码" in stock_header or "商品" in stock_header
    assert not re.search(r"\b[a-z_]*id\b", stock_header, re.I), stock_header
    _hold(page)

    # ── 4b. 库存流水：12 条 ───────────────────────────────────────
    page.locator('button[data-view="movements"]').click()
    page.locator('[data-test="movements-view"]').wait_for(state="visible", timeout=10_000)
    page.get_by_text("星火羽扇礼盒").first.wait_for(state="visible", timeout=10_000)
    expect(page.locator('[data-test="movements-view"]')).to_contain_text("草船借箭纪念徽章")
    _hold(page)

    # ── 4c. 经营摘要：非零销售收入/采购支出/净现金流 ───────────────
    page.locator('button[data-view="summary"]').click()
    page.locator('[data-test="summary"]').wait_for(state="visible", timeout=10_000)
    expect(page.locator('[data-test="metric-sales"]')).to_be_visible()
    expect(page.locator('[data-test="metric-purchase"]')).to_be_visible()
    expect(page.locator('[data-test="metric-cashflow"]')).to_be_visible()
    sales_text = page.locator('[data-test="metric-sales"]').inner_text()
    assert float(sales_text.replace(",", "").replace("¥", "").strip()) > 0, sales_text
    expect(page.locator('[data-test="low-stock"]')).to_contain_text("草船借箭纪念徽章")
    _hold(page)

    # ── 4d. Seller AI：基于真实库存指出最低商品 ────────────────────
    page.locator('button[data-view="chat"]').click()
    page.locator('[data-test="chat-view"]').wait_for(state="visible", timeout=10_000)
    page.locator('[data-test="chat-input"]').fill("库存最低的商品是什么？")
    with page.expect_request(
        lambda req: req.method == "POST" and _path(req.url) == "/seller/chat"
    ):
        page.locator('[data-test="chat-send"]').click()
    reply = page.locator('[data-test="messages"] .msg-ai').last
    expect(reply).to_contain_text(re.compile("草船借箭纪念徽章|3\\s*枚?"), timeout=30_000)
    _hold(page)

    # ── 5. 切到 新野火攻复盘空间（时间线 + 信息/物流/人流） ─────────
    ctx = _switch_org(page, CAMPAIGN_OUID)
    assert ctx["ouid"] == CAMPAIGN_OUID
    assert ctx["orgType"] == "campaign"
    _assert_no_internal_keys(ctx)
    page.locator('[data-test="generic-space"]').wait_for(state="visible", timeout=10_000)
    expect(page.locator('[data-test="ov-name"]')).to_contain_text("新野火攻复盘空间")
    expect(page.locator('[data-test="ov-type"]')).to_contain_text("campaign")
    page.locator('[data-test="block-overview"]').wait_for(state="visible", timeout=10_000)

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
    _hold(page)

    # ── 6. 回到电商空间，总结多空间隔离（仍无需重新登录） ──────────
    ctx = _switch_org(page, SHOP_OUID)
    assert ctx["ouid"] == SHOP_OUID
    assert ctx["orgType"] == "ecommerce"
    page.locator('[data-test="workbench"]').wait_for(state="visible", timeout=10_000)
    expect(page.get_by_role("heading", name="经营工作台")).to_be_visible()
    expect(page.locator('[data-test="workbench"]')).to_contain_text("星火羽扇礼盒")
    expect(page.locator('[data-test="workbench"]')).to_contain_text("草船借箭纪念徽章")
    _hold(page)
