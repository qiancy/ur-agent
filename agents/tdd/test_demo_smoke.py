"""
DEMO 双场景回归冒烟测试（DEMO_双场景回归测试计划 §4）。

在种子数据（scripts/seed_demo_data.py）之上验证 5 个核心场景：
1. 登录鉴权 —— zhansan 登录，JWT 只含业务身份字段（puid/ouid/...），不含 DB 数字 ID。
2. 组织列表 —— /auth/me/organizations 含 taobao_shop_a 与 xinye_campaign。
3. 上下文切换 —— switch-organization 往返 taobao_shop_a <-> xinye_campaign。
4. 资产隔离 —— 淘宝库存不出现在火烧新野空间（致命红线）。
5. Seller AI 查询 —— /seller/chat 回答“库存最低的商品”指向 木牛流马模型 12 件。

约定：
- 默认测试使用脚本化 fake LLM（§1.3：默认测试不触发真 LLM），数据仍来自真实
  seeded DB：fake 发出 seller_stock 工具调用 -> 真实工具查询真实库存 -> fake 从
  工具返回的真实数据中归纳回答。
- 需要的环境变量：DEMO_ZHANSAN_PASSWORD（zhansan 演示密码），来自仓库 .env。
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
from pydantic import Field

client = TestClient(app)

PASSWORD = os.getenv("DEMO_ZHANSAN_PASSWORD", "").strip()

_TAOBAO_OUID = "taobao_shop_a"
_XINYE_OUID = "xinye_campaign"

_FORBIDDEN_ID_FIELDS = {
    "id", "pid", "oid",
    "person_id", "organization_id", "membership_id",
    "resource_id", "warehouse_id", "transaction_id", "account_id",
    "resource_warehouse_id", "inventory_movement_id",
}

if not PASSWORD:
    pytest.skip(
        "DEMO_ZHANSAN_PASSWORD is not set; demo smoke tests skipped",
        allow_module_level=True,
    )


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _assert_no_db_ids(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in _FORBIDDEN_ID_FIELDS, f"leaked db id field: {k}"
            assert not k.endswith("_id"), f"leaked db id field: {k}"
            _assert_no_db_ids(v)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_db_ids(item)


def _jwt(token: str) -> dict:
    payload = decode_access_token(token)
    assert payload is not None, "token did not decode"
    return payload


# ============================================================================
# 1. 登录鉴权
# ============================================================================


def test_login_returns_business_only_jwt():
    resp = client.post("/auth/seller-login",
                       json={"login": "zhansan", "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["person"]["puid"] == "zhansan"
    assert body["organization"]["ouid"] == _TAOBAO_OUID
    assert body["organization"]["type"] == "ecommerce"
    assert body["membership"]["role"] == "owner"

    payload = _jwt(body["access_token"])
    assert payload["puid"] == "zhansan"
    assert payload["ouid"] == _TAOBAO_OUID
    assert payload["organization_type"] == "ecommerce"
    assert payload["role"] == "owner"
    assert "id" not in payload
    for key in payload:
        assert not key.endswith("_id"), f"JWT leaked db id field: {key}"
    _assert_no_db_ids(body)


# ============================================================================
# 2. 组织列表
# ============================================================================


def _login_token() -> str:
    resp = client.post("/auth/seller-login",
                       json={"login": "zhansan", "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def test_organizations_list_has_both_core_spaces():
    token = _login_token()
    resp = client.get("/auth/me/organizations", headers=_auth_header(token))
    assert resp.status_code == 200, resp.text
    orgs = resp.json()
    ouids = {o["ouid"] for o in orgs}
    assert _TAOBAO_OUID in ouids
    assert _XINYE_OUID in ouids
    for o in orgs:
        assert {"ouid", "name", "type", "role"} <= set(o.keys())
    _assert_no_db_ids(orgs)


# ============================================================================
# 3. 上下文切换
# ============================================================================


def test_switch_organization_roundtrip():
    token = _login_token()
    resp = client.post("/auth/switch-organization",
                       headers=_auth_header(token),
                       json={"ouid": _XINYE_OUID})
    assert resp.status_code == 200, resp.text
    xinye_body = resp.json()
    assert _jwt(xinye_body["access_token"])["ouid"] == _XINYE_OUID
    assert xinye_body["organization"]["ouid"] == _XINYE_OUID

    resp = client.post("/auth/switch-organization",
                       headers=_auth_header(xinye_body["access_token"]),
                       json={"ouid": _TAOBAO_OUID})
    assert resp.status_code == 200, resp.text
    assert _jwt(resp.json()["access_token"])["ouid"] == _TAOBAO_OUID


# ============================================================================
# 4. 资产隔离（致命红线）
# ============================================================================


def test_taobao_stock_visible_in_shop_context():
    token = _login_token()
    resp = client.get("/seller/stock", headers=_auth_header(token))
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    stock = {r["product_uid"]: r for r in rows}
    assert stock["诸葛亮联名羽扇"]["quantity"] == 50
    assert stock["木牛流马模型"]["quantity"] == 12
    _assert_no_db_ids(rows)


def test_taobao_assets_absent_from_xinye_context():
    token = _login_token()
    resp = client.post("/auth/switch-organization",
                       headers=_auth_header(token),
                       json={"ouid": _XINYE_OUID})
    assert resp.status_code == 200, resp.text
    xinye_token = resp.json()["access_token"]

    resp = client.get("/spaces/current/resources", headers=_auth_header(xinye_token))
    assert resp.status_code == 200, resp.text
    resources = resp.json()["grouped"]
    names = [r["name"] for r in resources.get("physical", [])]
    assert "军粮" in names
    assert "箭矢" in names
    assert "诸葛亮联名羽扇" not in names
    assert "木牛流马模型" not in names

    resp = client.get("/assets", params={"name": "羽扇"},
                      headers=_auth_header(xinye_token))
    assert resp.status_code == 200, resp.text
    assert resp.json() == []

    # Seller endpoints must not be reachable from a campaign space.
    resp = client.get("/seller/stock", headers=_auth_header(xinye_token))
    assert resp.status_code == 403, resp.text


# ============================================================================
# 5. Seller AI 查询（fake LLM，数据来自真实 seeded DB）
# ============================================================================


class _FakeSellerChatModel(BaseChatModel):
    """Calls the real seller_stock tool, then summarizes from the real result."""

    bound_tool_names: Optional[list] = None
    generation_count: int = 0

    @property
    def _llm_type(self) -> str:
        return "fake-demo-seller-chat-model"

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
        answer = ("库存最低的商品是{name}，当前库存 {qty} 件。".format(
            name=lowest["product_uid"], qty=int(float(lowest["quantity"]))))
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=answer))])


def _install_fake_llm(monkeypatch):
    fake = _FakeSellerChatModel()
    monkeypatch.setattr("src.agents.seller_agent.get_llm", lambda: fake)
    return fake


def test_seller_chat_answers_lowest_stock_from_real_data(monkeypatch):
    fake = _install_fake_llm(monkeypatch)
    token = _login_token()

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
    assert "木牛流马模型" in body["response"]
    assert "12" in body["response"]
    assert body["ouid"] == _TAOBAO_OUID
    _assert_no_db_ids(body)
