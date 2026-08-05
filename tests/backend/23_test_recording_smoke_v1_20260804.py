"""
DEMO-DATA-02 全新录屏冒烟测试（DEMO-DATA-02_全新录屏账号与数据开发测试安排 §4 T-TDD）。

在种子数据（scripts/seed_recording_data.py）之上验证 9 项必测：
1. liuming 登录默认进入 liuming_personal（MVP：先有自己的 personal 工作空间）。
2. /auth/me/organizations 至少含 liuming_personal / liuming_mingdeng_shop /
   liuming_xinye_review。
3. Header/后端切换请求只允许 { "ouid": ... }，不得含 DB ID（extra=forbid → 422）。
4. personal 与 campaign 空间访问 /seller/stock 返回 403。
5. ecommerce 空间 /seller/stock 至少 6 行，最低库存为 草船借箭纪念徽章 3。
6. ecommerce 空间 /seller/summary 有非零销售收入、采购支出、库存估值。
7. campaign 空间 /spaces/current/timeline 至少 8 条事件，含信息流/物流/人流。
8. ecommerce 商品不得出现在 campaign 资源中。
9. 所有认证、空间、seller、spaces 响应递归扫描无 DB 数字 ID。

约定：
- 默认测试使用脚本化 fake LLM（默认测试不触发真 LLM），数据仍来自真实 seeded DB。
- 需要的环境变量：DEMO_LIUMING_PASSWORD（liuming 演示密码），来自仓库 .env。
- 密码不写入源码/文档/测试；未设置时本模块跳过。
"""
import json
import os
import uuid
from pathlib import Path
from typing import Optional

import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

from src.app import app
from src.auth.auth import decode_access_token

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

client = TestClient(app)

PASSWORD = os.getenv("DEMO_LIUMING_PASSWORD", "").strip()

_PERSONAL_OUID = "liuming_personal"
_SHOP_OUID = "liuming_mingdeng_shop"
_CAMPAIGN_OUID = "liuming_xinye_review"
_LOWEST_ANCHOR = "草船借箭纪念徽章"

_FORBIDDEN_ID_FIELDS = {
    "id", "pid", "oid",
    "person_id", "organization_id", "membership_id",
    "resource_id", "warehouse_id", "transaction_id", "account_id",
    "resource_warehouse_id", "inventory_movement_id",
}

if not PASSWORD:
    pytest.skip(
        "DEMO_LIUMING_PASSWORD is not set; recording smoke tests skipped",
        allow_module_level=True,
    )


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _assert_no_db_ids(obj, path: str = "$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in _FORBIDDEN_ID_FIELDS, f"leaked db id field: {path}.{k}"
            assert not k.endswith("_id"), f"leaked db id field: {path}.{k}"
            _assert_no_db_ids(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _assert_no_db_ids(item, f"{path}[{i}]")


def _jwt(token: str) -> dict:
    payload = decode_access_token(token)
    assert payload is not None, "token did not decode"
    return payload


def _login() -> str:
    resp = client.post("/auth/login",
                       json={"login": "liuming", "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _switch(token: str, ouid: str) -> str:
    resp = client.post("/auth/switch-organization",
                       headers=_auth_header(token),
                       json={"ouid": ouid})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _stock_totals(rows: list) -> dict:
    """Aggregate per-location stock rows into per-product totals (multi-warehouse safe)."""
    totals: dict[str, dict] = {}
    for row in rows:
        uid = row["product_uid"]
        totals.setdefault(uid, {"quantity": 0.0, "unit": row.get("unit")})
        totals[uid]["quantity"] += float(row["quantity"])
    return totals


# ============================================================================
# 1. 登录默认进入个人空间
# ============================================================================


def test_login_defaults_to_personal_space():
    resp = client.post("/auth/login",
                       json={"login": "liuming", "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["person"]["puid"] == "liuming"
    assert body["person"]["name"] == "刘明"
    assert body["organization"]["ouid"] == _PERSONAL_OUID
    assert body["organization"]["type"] == "personal"
    assert body["membership"]["role"] == "owner"
    assert body["requires_organization"] is False

    payload = _jwt(body["access_token"])
    assert payload["puid"] == "liuming"
    assert payload["ouid"] == _PERSONAL_OUID
    assert payload["organization_type"] == "personal"
    assert payload["role"] == "owner"
    assert "id" not in payload
    for key in payload:
        assert not key.endswith("_id"), f"JWT leaked db id field: {key}"
    _assert_no_db_ids(body)


# ============================================================================
# 2. 组织列表
# ============================================================================


def test_organizations_include_three_spaces():
    token = _login()
    resp = client.get("/auth/me/organizations", headers=_auth_header(token))
    assert resp.status_code == 200, resp.text
    orgs = resp.json()
    by_ouid = {o["ouid"]: o for o in orgs}
    assert {_PERSONAL_OUID, _SHOP_OUID, _CAMPAIGN_OUID} <= set(by_ouid)
    assert by_ouid[_PERSONAL_OUID]["role"] == "owner"
    assert by_ouid[_SHOP_OUID]["role"] == "owner"
    assert by_ouid[_CAMPAIGN_OUID]["role"] == "member"
    for o in orgs:
        assert {"ouid", "name", "type", "role"} <= set(o.keys())
    _assert_no_db_ids(orgs)


# ============================================================================
# 3. 切换请求只允许 { ouid }，不得含 DB ID
# ============================================================================


def test_switch_request_only_accepts_ouid():
    token = _login()

    resp = client.post("/auth/switch-organization",
                       headers=_auth_header(token),
                       json={"ouid": _SHOP_OUID})
    assert resp.status_code == 200, resp.text
    assert _jwt(resp.json()["access_token"])["ouid"] == _SHOP_OUID

    for leaked in ("person_id", "organization_id", "membership_id", "id"):
        resp = client.post("/auth/switch-organization",
                           headers=_auth_header(token),
                           json={"ouid": _SHOP_OUID, leaked: 1})
        assert resp.status_code == 422, (
            f"switch-organization with {leaked} should be rejected: {resp.status_code}")


# ============================================================================
# 4. personal / campaign 不调用 Seller API
# ============================================================================


def test_personal_and_campaign_seller_endpoints_forbidden():
    personal_token = _login()
    for path in ("/seller/stock", "/seller/summary"):
        resp = client.get(path, headers=_auth_header(personal_token))
        assert resp.status_code == 403, f"personal {path} expected 403"
    resp = client.post("/seller/chat",
                       headers=_auth_header(personal_token),
                       json={"message": "hi"})
    assert resp.status_code == 403, "personal /seller/chat expected 403"

    campaign_token = _switch(personal_token, _CAMPAIGN_OUID)
    for path in ("/seller/stock", "/seller/summary"):
        resp = client.get(path, headers=_auth_header(campaign_token))
        assert resp.status_code == 403, f"campaign {path} expected 403"
    resp = client.post("/seller/chat",
                       headers=_auth_header(campaign_token),
                       json={"message": "hi"})
    assert resp.status_code == 403, "campaign /seller/chat expected 403"


# ============================================================================
# 5. ecommerce 库存
# ============================================================================


def test_ecommerce_stock_six_rows_with_lowest_anchor():
    token = _switch(_login(), _SHOP_OUID)
    resp = client.get("/seller/stock", headers=_auth_header(token))
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert len(rows) >= 6, f"expected >=6 stock rows, got {len(rows)}"
    stock = _stock_totals(rows)
    assert stock[_LOWEST_ANCHOR]["quantity"] == 3
    assert stock[_LOWEST_ANCHOR]["unit"] == "枚"
    assert stock["星火羽扇礼盒"]["quantity"] == 64
    assert stock["孔明灯夜读灯"]["quantity"] == 5
    _assert_no_db_ids(rows)


# ============================================================================
# 6. ecommerce summary 非零
# ============================================================================


def test_ecommerce_summary_nonzero_and_low_stock():
    token = _switch(_login(), _SHOP_OUID)
    resp = client.get("/seller/summary", headers=_auth_header(token))
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary["product_count"] >= 6
    assert summary["sales_amount"] > 0
    assert summary["purchase_amount"] > 0
    assert summary["net_cash_flow"] != 0
    assert summary["estimated_inventory_value"] > 0

    low = {item["product_uid"]: item for item in summary["low_stock_items"]}
    assert _LOWEST_ANCHOR in low
    assert "孔明灯夜读灯" in low
    assert low[_LOWEST_ANCHOR]["quantity"] == 3
    assert low["孔明灯夜读灯"]["quantity"] == 5
    _assert_no_db_ids(summary)


# ============================================================================
# 7. campaign 时间线
# ============================================================================


def test_campaign_timeline_eight_flow_events():
    token = _switch(_login(), _CAMPAIGN_OUID)
    resp = client.get("/spaces/current/timeline", headers=_auth_header(token))
    assert resp.status_code == 200, resp.text
    events = resp.json()["events"]
    assert len(events) >= 8, f"expected >=8 timeline events, got {len(events)}"
    titles = {e["title"] for e in events}
    for expect in ("斥候确认曹军路线", "新野点火", "刘备军民转移复盘"):
        assert expect in titles, f"missing event {expect}"
    seqs = sorted(e["seq"] for e in events)
    assert seqs == list(range(1, len(events) + 1)), f"seq not contiguous: {seqs}"
    for event in events:
        for dim in ("info_flow", "logistics_flow", "people_flow"):
            assert event["payload"].get(dim), (
                f"event {event['title']} missing payload.{dim}")
    _assert_no_db_ids(events)


# ============================================================================
# 8. ecommerce 商品不得出现在 campaign 资源
# ============================================================================


def test_ecommerce_products_absent_from_campaign_resources():
    token = _switch(_login(), _CAMPAIGN_OUID)
    resp = client.get("/spaces/current/resources", headers=_auth_header(token))
    assert resp.status_code == 200, resp.text
    grouped = resp.json()["grouped"]
    physical_names = [r["name"] for r in grouped.get("physical", [])]
    knowledge_names = [r["name"] for r in grouped.get("knowledge", [])]

    assert "新野城军粮" in physical_names
    assert "火油桶" in physical_names
    assert "撤离辎重车" in physical_names
    for leaked in ("星火羽扇礼盒", "木牛流马积木套装", "草船借箭纪念徽章"):
        assert leaked not in physical_names, f"ecommerce product leaked: {leaked}"
    assert "斥候简报" in knowledge_names
    assert "火攻布置图" in knowledge_names
    assert "百姓撤离名册" in knowledge_names
    _assert_no_db_ids(grouped)


# ============================================================================
# 9. 认证/空间/seller/spaces 响应递归扫描无 DB 数字 ID
# ============================================================================


def test_no_db_ids_scan_across_all_endpoints():
    token = _login()

    scans = []
    resp = client.get("/auth/me/organizations", headers=_auth_header(token))
    assert resp.status_code == 200, resp.text
    scans.append(("auth/me/organizations", resp.json()))

    shop_token = _switch(token, _SHOP_OUID)
    for path in ("/seller/stock", "/seller/summary", "/seller/inventory-movements"):
        resp = client.get(path, headers=_auth_header(shop_token))
        assert resp.status_code == 200, f"{path}: {resp.status_code}"
        scans.append((path, resp.json()))

    camp_token = _switch(token, _CAMPAIGN_OUID)
    for path in ("/spaces/current/timeline", "/spaces/current/resources",
                 "/spaces/current/overview"):
        resp = client.get(path, headers=_auth_header(camp_token))
        assert resp.status_code == 200, f"{path}: {resp.status_code}"
        scans.append((path, resp.json()))

    for name, payload in scans:
        _assert_no_db_ids(payload, name)


# ============================================================================
# Seller AI 查询（fake LLM，数据来自真实 seeded DB）
# ============================================================================


class _FakeSellerChatModel(BaseChatModel):
    """Calls the real seller_stock tool, then summarizes from the real result."""

    bound_tool_names: Optional[list] = None
    generation_count: int = 0

    @property
    def _llm_type(self) -> str:
        return "fake-recording-seller-chat-model"

    def bind(self, **kwargs):
        tools = kwargs.get("tools")
        if tools is not None:
            self.bound_tool_names = [
                t["function"]["name"] for t in tools
                if isinstance(t, dict) and t.get("function")
            ]
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.generation_count += 1
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        if not tool_msgs:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(
                content="", tool_calls=[{
                    "name": "seller_stock", "args": {},
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                }],
            ))])
        rows = json.loads(tool_msgs[-1].content)
        lowest = min(rows, key=lambda r: float(r["quantity"]))
        answer = ("库存最低的商品是{name}，当前库存 {qty} {unit}。".format(
            name=lowest["product_uid"], qty=int(float(lowest["quantity"])),
            unit=lowest.get("unit") or "件"))
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=answer))])


def _install_fake_llm(monkeypatch):
    fake = _FakeSellerChatModel()
    monkeypatch.setattr("src.agents.seller_agent.get_llm", lambda: fake)
    return fake


def test_seller_chat_answers_lowest_stock_from_real_data(monkeypatch):
    fake = _install_fake_llm(monkeypatch)
    token = _switch(_login(), _SHOP_OUID)

    resp = client.post("/seller/chat",
                       headers=_auth_header(token),
                       json={"message": "库存最低的商品是什么？"})
    assert resp.status_code == 200, resp.text
    assert fake.generation_count >= 1
    assert fake.bound_tool_names is not None
    assert set(fake.bound_tool_names) == {
        "seller_stock", "seller_summary",
        "seller_product_summary", "seller_inventory_movements",
    }
    body = resp.json()
    assert _LOWEST_ANCHOR in body["response"]
    assert "3" in body["response"]
    assert "枚" in body["response"]
    assert body["ouid"] == _SHOP_OUID
    _assert_no_db_ids(body)
