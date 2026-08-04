"""
Seller chat LIVE LLM integration test (manual, not part of the default suite).

Exercises POST /seller/chat against the REAL LLM configured via environment
variables (LLM_BASE_URL / LLM_API_KEY / LLM_MODEL) and a REAL database
(DB_*). Default pytest run skips this file via pytest.ini
``addopts = -m "not integration"``. Run explicitly:

    pytest -m integration agents/tdd/test_seller_chat_live_llm.py

Load secrets from your local .env (never commit them), e.g.:
    set -a; source .env; set +a

If the real LLM is unreachable or too slow, the endpoint returns 502/504 and
the query test fails by design.
"""
import os
import uuid

import pytest

from fastapi.testclient import TestClient

from src.config import get_llm_config

pytestmark = pytest.mark.integration


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def live_env():
    """Skip live integration tests unless local secrets are configured."""
    cfg = get_llm_config()
    missing = []
    if not os.getenv("JWT_SECRET"):
        missing.append("JWT_SECRET")
    if cfg["api_key"] in ("", "fake-key"):
        missing.append("LLM_API_KEY")
    if missing:
        pytest.skip(f"set {', '.join(missing)} in .env or shell env")
    return cfg


@pytest.fixture(scope="module")
def client(live_env):
    """Import the app lazily so default deselection never needs JWT_SECRET."""
    from src.app import app
    return TestClient(app)


def _create_shop(client: TestClient, tag: str) -> dict:
    s = uuid.uuid4().hex[:8]
    login = f"seller_{tag}_{s}"
    resp = client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": f"卖家{tag}_{s}",
    })
    assert resp.status_code == 201, resp.text

    ouid = f"be04live_{tag}_{s}"
    resp = client.post("/spaces", headers=_auth_header(resp.json()["access_token"]), json={
        "name": f"BE04LIVE_{tag}_{s}", "org_type": "ecommerce", "ouid": ouid,
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]

    product_uid = f"prod_{tag}_{s}"
    resp = client.post(
        "/resource",
        headers=_auth_header(token),
        json={"name": product_uid, "resource_type": "physical", "unit": "件"},
    )
    assert resp.status_code == 201, resp.text

    warehouse_code = f"wh_{tag}_{s}"
    resp = client.post(
        "/warehouse",
        headers=_auth_header(token),
        json={"name": f"仓库{tag}_{s}", "code": warehouse_code},
    )
    assert resp.status_code == 201, resp.text

    return {
        "ouid": ouid,
        "token": token,
        "product_uid": product_uid,
        "warehouse_code": warehouse_code,
    }


def _purchase_in(client: TestClient, shop: dict, quantity: float):
    return client.post(
        "/seller/purchase-in",
        headers=_auth_header(shop["token"]),
        json={
            "product_uid": shop["product_uid"],
            "warehouse_code": shop["warehouse_code"],
            "location_path": "A-01",
            "quantity": quantity,
            "unit": "件",
            "total_amount": quantity * 8,
            "counterparty_name": "BE04供应商",
        },
    )


def _chat(client: TestClient, shop: dict, message: str):
    return client.post(
        "/seller/chat",
        headers=_auth_header(shop["token"]),
        json={"message": message},
    )


def test_live_llm_config_present(live_env):
    """Guard: real LLM env must be configured, otherwise skip the real test."""
    assert live_env["api_key"] not in ("", "fake-key")


def test_live_llm_answers_stock_query(client):
    shop = _create_shop(client, "livellm")
    resp = _purchase_in(client, shop, quantity=10)
    assert resp.status_code == 200, resp.text
    resp = _chat(client, shop, "当前库存怎么样？请列出各商品当前数量")
    assert resp.status_code == 200, resp.text
    response = (resp.json().get("response") or "").strip()
    assert response, "LLM returned empty response"


def test_live_identity_fast_path(client):
    """Identity fast-path returns shop info without calling the LLM."""
    shop = _create_shop(client, "livellmid")
    resp = _chat(client, shop, "我是谁")
    assert resp.status_code == 200, resp.text
    assert shop["ouid"] in resp.json()["response"]


def test_live_write_intent_blocked_without_llm(client):
    """Write intent is intercepted at the route, never reaches the LLM."""
    shop = _create_shop(client, "livellmwi")
    resp = _chat(client, shop, "帮我入库 10 件")
    assert resp.status_code == 200, resp.text
    assert "只支持经营查询" in resp.json()["response"]
