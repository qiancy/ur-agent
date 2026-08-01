"""
BE-04 TDD (RED): POST /seller/chat — read-only Seller AI closed loop.

Security boundaries are verified under a scripted fake chat model (no real
LLM, no network):

- strict JWT + ecommerce org check (403 otherwise)
- identity / internal-PK query params rejected (400) and body fields
  rejected (400/422, extra=forbid)
- write-intent rejected at route level, never reaching the LLM
- agent mounts only Seller read-only tools, never calls remote prompt hub
- responses contain zero database numeric primary keys
"""
import json
import re
import uuid
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from src.app import app

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

client = TestClient(app)

_DB_ID_FIELDS = {
    "id", "resource_id", "warehouse_id", "resource_warehouse_id",
    "organization_id", "person_id", "transaction_id",
    "inventory_movement_id", "movement_id",
}

_SELLER_TOOL_NAMES = {
    "seller_stock",
    "seller_summary",
    "seller_product_summary",
    "seller_inventory_movements",
}


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _assert_no_db_ids(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in _DB_ID_FIELDS, f"leaked DB id field: {k}"
            _assert_no_db_ids(v)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_db_ids(item)


# ============================================================================
# Scripted fake chat model
# ============================================================================


class _FakeSellerChatModel(BaseChatModel):
    """Records bound tool names and replays scripted AIMessage responses."""

    responses: list = Field(default_factory=list)
    bound_tool_names: Optional[list] = None
    generation_count: int = 0

    @property
    def _llm_type(self) -> str:
        return "fake-seller-chat-model"

    def bind_tools(self, tools, **kwargs):
        self.bound_tool_names = [t.name for t in tools]
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.generation_count += 1
        if self.responses:
            msg = self.responses.pop(0)
        else:
            msg = AIMessage(content="ok")
        return ChatResult(generations=[ChatGeneration(message=msg)])


def _install_fake_llm(monkeypatch, responses=None):
    fake = _FakeSellerChatModel(responses=list(responses or []))
    monkeypatch.setattr("src.agents.seller_agent.get_llm", lambda: fake)
    return fake


def _tool_call(name: str, args: dict) -> AIMessage:
    return AIMessage(content="", tool_calls=[{
        "name": name, "args": args, "id": f"call_{uuid.uuid4().hex[:8]}",
    }])


# ============================================================================
# Fixtures
# ============================================================================


def _create_shop(tag: str) -> dict:
    s = uuid.uuid4().hex[:8]
    ouid = f"be04c_{tag}_{s}"
    resp = client.post("/organizations", json={
        "name": f"BE04C_{tag}_{s}", "org_type": "ecommerce", "ouid": ouid,
    })
    assert resp.status_code in (200, 201), resp.text

    login = f"seller_{tag}_{s}@{ouid}"
    resp = client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": f"卖家{tag}_{s}",
    })
    assert resp.status_code == 201, resp.text

    resp = client.post("/auth/seller-login", json={
        "login": login, "password": "pass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    token = data["access_token"]

    product_uid = f"prod_{tag}_{s}"
    resp = client.post(
        "/resource",
        headers=_auth_header(token),
        json={"name": product_uid, "resource_type": "physical", "unit": "件"},
    )
    assert resp.status_code == 201, resp.text

    wh_code = f"wh_{tag}_{s}"
    resp = client.post(
        "/warehouse",
        headers=_auth_header(token),
        json={"name": f"仓库{tag}_{s}", "code": wh_code},
    )
    assert resp.status_code == 201, resp.text

    return {
        "ouid": ouid,
        "token": token,
        "product_uid": product_uid,
        "warehouse_code": wh_code,
        "org_name": f"BE04C_{tag}_{s}",
    }


def _create_company_token(tag: str) -> dict:
    """Create a non-ecommerce (company) org and return a JWT for it."""
    s = uuid.uuid4().hex[:8]
    ouid = f"be04co_{tag}_{s}"
    resp = client.post("/organizations", json={
        "name": f"BE04CO_{tag}_{s}", "org_type": "company", "ouid": ouid,
    })
    assert resp.status_code in (200, 201), resp.text

    login = f"staff_{tag}_{s}@{ouid}"
    resp = client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": f"员工{tag}_{s}",
    })
    assert resp.status_code == 201, resp.text

    resp = client.post("/auth/login", json={
        "login": login, "password": "pass123",
    })
    assert resp.status_code == 200
    return {
        "ouid": ouid,
        "token": resp.json()["access_token"],
        "org_type": "company",
    }


def _chat(shop: dict, message: str, **params) -> object:
    return client.post(
        "/seller/chat",
        headers=_auth_header(shop["token"]),
        params=params,
        json={"message": message},
    )


def _purchase_in(shop: dict, quantity: float, total_amount: float = None) -> object:
    if total_amount is None:
        total_amount = quantity * 8
    return client.post(
        "/seller/purchase-in",
        headers=_auth_header(shop["token"]),
        json={
            "product_uid": shop["product_uid"],
            "warehouse_code": shop["warehouse_code"],
            "location_path": "A-01",
            "quantity": quantity,
            "unit": "件",
            "total_amount": total_amount,
            "counterparty_name": "BE04供应商",
        },
    )


def _sales_out(shop: dict, quantity: float, total_amount: float = None) -> object:
    if total_amount is None:
        total_amount = quantity * 15
    return client.post(
        "/seller/sales-out",
        headers=_auth_header(shop["token"]),
        json={
            "product_uid": shop["product_uid"],
            "warehouse_code": shop["warehouse_code"],
            "location_path": "A-01",
            "quantity": quantity,
            "unit": "件",
            "total_amount": total_amount,
            "counterparty_name": "BE04买家",
        },
    )


# ============================================================================
# 10-15. Auth & validation
# ============================================================================


def test_seller_chat_requires_jwt():
    resp = client.post("/seller/chat", json={"message": "库存多少"})
    assert resp.status_code == 401, resp.text


def test_seller_chat_rejects_non_ecommerce_org(monkeypatch):
    _install_fake_llm(monkeypatch)
    company = _create_company_token("ne")
    resp = _chat(company, "库存多少")
    assert resp.status_code == 403, resp.text


def test_seller_chat_rejects_identity_and_internal_pk_query_params(monkeypatch):
    _install_fake_llm(monkeypatch)
    shop = _create_shop("qid")
    for param in ["id", "resource_id", "organization_id", "puid", "ouid"]:
        resp = _chat(shop, "库存多少", **{param: "1"})
        assert resp.status_code == 400, f"{param}: {resp.text}"


def test_seller_chat_rejects_identity_and_internal_pk_body_fields(monkeypatch):
    _install_fake_llm(monkeypatch)
    shop = _create_shop("bid")
    for field in ["id", "resource_id", "organization_id", "puid", "ouid"]:
        resp = client.post(
            "/seller/chat",
            headers=_auth_header(shop["token"]),
            json={"message": "库存多少", field: "1"},
        )
        assert resp.status_code in (400, 422), f"{field}: {resp.text}"


def test_seller_chat_rejects_unknown_body_fields(monkeypatch):
    _install_fake_llm(monkeypatch)
    shop = _create_shop("uf")
    resp = client.post(
        "/seller/chat",
        headers=_auth_header(shop["token"]),
        json={"message": "库存多少", "extra": "x"},
    )
    assert resp.status_code in (400, 422), resp.text


def test_seller_chat_rejects_empty_message(monkeypatch):
    _install_fake_llm(monkeypatch)
    shop = _create_shop("em")
    for msg in ["", "   ", "\t\n"]:
        resp = _chat(shop, msg)
        assert resp.status_code == 422, resp.text


# ============================================================================
# 16-17. Agent wiring
# ============================================================================


def test_seller_chat_mounts_only_seller_tools(monkeypatch):
    fake = _install_fake_llm(monkeypatch, [
        _tool_call("seller_stock", {}),
        AIMessage(content="库存 10 件。"),
    ])
    shop = _create_shop("mnt")
    assert _purchase_in(shop, 10, 80).status_code == 200

    resp = _chat(shop, "查一下库存")
    assert resp.status_code == 200, resp.text
    assert fake.bound_tool_names is not None
    assert set(fake.bound_tool_names) == _SELLER_TOOL_NAMES


def test_seller_agent_does_not_pull_remote_prompt(monkeypatch):
    def _forbid_hub(*args, **kwargs):
        raise AssertionError("Seller Agent must not call remote prompt hub")

    monkeypatch.setattr("langchain.hub.pull", _forbid_hub)
    fake = _install_fake_llm(monkeypatch, [
        _tool_call("seller_summary", {}),
        AIMessage(content="今日销售收入 45.00 元。"),
    ])
    shop = _create_shop("hub")
    assert _purchase_in(shop, 10, 80).status_code == 200

    resp = _chat(shop, "今天卖了多少钱")
    assert resp.status_code == 200, resp.text


# ============================================================================
# 18-20. Functional answers
# ============================================================================


def test_seller_chat_identity_fast_path_has_no_db_ids(monkeypatch):
    fake = _install_fake_llm(monkeypatch)
    shop = _create_shop("fp")
    resp = _chat(shop, "我是谁")
    assert resp.status_code == 200, resp.text
    assert fake.generation_count == 0
    _assert_no_db_ids(resp.json())
    assert "当前" in resp.json()["response"]


def test_seller_chat_can_answer_summary_question(monkeypatch):
    fake = _install_fake_llm(monkeypatch, [
        _tool_call("seller_summary", {}),
        AIMessage(content="今日销售收入为 45.00 元。"),
    ])
    shop = _create_shop("sum")
    assert _purchase_in(shop, 10, 80).status_code == 200
    assert _sales_out(shop, 3, 45).status_code == 200

    resp = _chat(shop, "今天卖了多少钱")
    assert resp.status_code == 200, resp.text
    assert fake.generation_count >= 1
    assert "45" in resp.json()["response"]


def test_seller_chat_can_answer_stock_question(monkeypatch):
    fake = _install_fake_llm(monkeypatch, [
        _tool_call("seller_stock", {}),
        AIMessage(content="当前库存 10 件。"),
    ])
    shop = _create_shop("stk")
    assert _purchase_in(shop, 10, 80).status_code == 200

    resp = _chat(shop, "库存还有多少")
    assert resp.status_code == 200, resp.text
    assert fake.generation_count >= 1
    assert "10" in resp.json()["response"]


# ============================================================================
# 21-24. Write-intent rejection
# ============================================================================


def test_seller_chat_refuses_write_intent_before_llm(monkeypatch):
    fake = _install_fake_llm(monkeypatch)
    shop = _create_shop("wi")
    resp = _chat(shop, "帮我采购入库 10 件")
    assert resp.status_code == 200, resp.text
    assert fake.generation_count == 0
    assert "只支持经营查询" in resp.json()["response"]


def test_seller_chat_purchase_spend_question_not_blocked(monkeypatch):
    fake = _install_fake_llm(monkeypatch, [
        _tool_call("seller_summary", {}),
        AIMessage(content="采购支出为 80.00 元。"),
    ])
    shop = _create_shop("psp")
    assert _purchase_in(shop, 10, 80).status_code == 200

    resp = _chat(shop, "采购支出是多少")
    assert resp.status_code == 200, resp.text
    assert fake.generation_count >= 1
    assert "80" in resp.json()["response"]


def test_seller_chat_read_intent_phrases_not_blocked(monkeypatch):
    fake = _install_fake_llm(monkeypatch, [
        _tool_call("seller_inventory_movements", {}),
        AIMessage(content="流水如下。"),
    ])
    shop = _create_shop("rip")
    assert _purchase_in(shop, 10, 80).status_code == 200

    for message in ["看出库流水", "入库金额统计"]:
        resp = _chat(shop, message)
        assert resp.status_code == 200, resp.text
        assert fake.generation_count >= 1, message


# ============================================================================
# 25-26. ecommerce org check source & fast-path source
# ============================================================================


def test_seller_chat_org_type_from_jwt_not_param(monkeypatch):
    fake = _install_fake_llm(monkeypatch, [
        _tool_call("seller_summary", {}),
        AIMessage(content="ok"),
    ])
    shop = _create_shop("ot1")
    assert _purchase_in(shop, 10, 80).status_code == 200

    resp = _chat(shop, "今天卖了多少钱", org_type="company")
    assert resp.status_code == 200, resp.text

    company = _create_company_token("ot2")
    resp = _chat(company, "库存多少", org_type="ecommerce")
    assert resp.status_code == 403, resp.text


def test_seller_chat_identity_fast_path_uses_ctx_org_name(monkeypatch):
    _install_fake_llm(monkeypatch)
    shop = _create_shop("on")
    resp = _chat(shop, "当前店铺")
    assert resp.status_code == 200, resp.text
    assert shop["org_name"] in resp.json()["response"]
    assert shop["ouid"] in resp.json()["response"]


# ============================================================================
# 22. no DB ids in response
# ============================================================================


def test_seller_chat_response_has_no_db_ids(monkeypatch):
    _install_fake_llm(monkeypatch, [
        _tool_call("seller_summary", {}),
        AIMessage(content="当前库存 7.00 件，销售收入 45.00 元。"),
    ])
    shop = _create_shop("rid")
    assert _purchase_in(shop, 10, 80).status_code == 200
    assert _sales_out(shop, 3, 45).status_code == 200

    resp = _chat(shop, "经营情况怎么样")
    assert resp.status_code == 200, resp.text
    _assert_no_db_ids(resp.json())
