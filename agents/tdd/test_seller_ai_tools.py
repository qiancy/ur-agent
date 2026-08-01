"""
BE-04 TDD (RED): Seller read-only AI tool factory.

Exercises ``make_seller_tools()`` directly against a real test database,
with no LLM involved. Business identifiers only (product_uid,
warehouse_code, location_path, movement_uid, operation_type, ...); zero
database numeric primary keys in tool signatures, outputs, or contracts.
"""
import json
import uuid

from fastapi.testclient import TestClient

from src.app import app
from src.db.database import query_organization_by_ouid
from src.tools.seller_tools import make_seller_tools

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


def _shop_key(shop: dict) -> int:
    return query_organization_by_ouid(shop["ouid"])[0]["id"]


def _tools(shop: dict):
    return make_seller_tools(_shop_key(shop))


def _create_shop(tag: str) -> dict:
    s = uuid.uuid4().hex[:8]
    ouid = f"be04t_{tag}_{s}"
    resp = client.post("/organizations", json={
        "name": f"BE04T_{tag}_{s}", "org_type": "ecommerce", "ouid": ouid,
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
    token = resp.json()["access_token"]

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
    }


def _purchase_in(shop: dict, quantity: float, total_amount: float = None,
                 product_uid: str = None) -> object:
    if total_amount is None:
        total_amount = quantity * 8
    return client.post(
        "/seller/purchase-in",
        headers=_auth_header(shop["token"]),
        json={
            "product_uid": product_uid or shop["product_uid"],
            "warehouse_code": shop["warehouse_code"],
            "location_path": "A-01",
            "quantity": quantity,
            "unit": "件",
            "total_amount": total_amount,
            "counterparty_name": "BE04供应商",
        },
    )


def _sales_out(shop: dict, quantity: float, total_amount: float = None,
               product_uid: str = None) -> object:
    if total_amount is None:
        total_amount = quantity * 15
    return client.post(
        "/seller/sales-out",
        headers=_auth_header(shop["token"]),
        json={
            "product_uid": product_uid or shop["product_uid"],
            "warehouse_code": shop["warehouse_code"],
            "location_path": "A-01",
            "quantity": quantity,
            "unit": "件",
            "total_amount": total_amount,
            "counterparty_name": "BE04买家",
        },
    )


# ============================================================================
# 1. seller_stock
# ============================================================================


def test_seller_stock_tool_returns_current_stock():
    shop = _create_shop("stock")
    assert _purchase_in(shop, quantity=10, total_amount=80).status_code == 200

    tools = {t.name: t for t in _tools(shop)}
    result = tools["seller_stock"].invoke({"product_uid": shop["product_uid"]})
    rows = json.loads(result)
    assert isinstance(rows, list) and len(rows) == 1
    assert rows[0]["product_uid"] == shop["product_uid"]
    assert rows[0]["warehouse_code"] == shop["warehouse_code"]
    assert float(rows[0]["quantity"]) == 10.0


# ============================================================================
# 2. seller_summary
# ============================================================================


def test_seller_summary_tool_returns_business_metrics():
    shop = _create_shop("sum")
    assert _purchase_in(shop, quantity=10, total_amount=80).status_code == 200
    assert _sales_out(shop, quantity=3, total_amount=45).status_code == 200

    tools = {t.name: t for t in _tools(shop)}
    data = json.loads(tools["seller_summary"].invoke({}))
    assert data["status"] == "ok"
    assert data["purchase_amount"] == 80.0
    assert data["sales_amount"] == 45.0
    assert data["net_cash_flow"] == -35.0
    assert data["movement_count"] == 2
    assert data["current_stock_quantity"] == 7.0


# ============================================================================
# 3. seller_product_summary
# ============================================================================


def test_seller_product_summary_tool_returns_product_metrics():
    shop = _create_shop("psum")
    assert _purchase_in(shop, quantity=10, total_amount=80).status_code == 200
    assert _sales_out(shop, quantity=3, total_amount=45).status_code == 200

    tools = {t.name: t for t in _tools(shop)}
    data = json.loads(tools["seller_product_summary"].invoke({}))
    assert data["status"] == "ok"
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_uid"] == shop["product_uid"]
    assert item["purchase_quantity"] == 10.0
    assert item["sales_quantity"] == 3.0
    assert item["purchase_amount"] == 80.0
    assert item["sales_amount"] == 45.0
    assert item["current_quantity"] == 7.0


# ============================================================================
# 4. seller_inventory_movements
# ============================================================================


def test_seller_movements_tool_filters_and_limits():
    shop = _create_shop("mov")
    assert _purchase_in(shop, quantity=10, total_amount=80).status_code == 200
    assert _sales_out(shop, quantity=3, total_amount=45).status_code == 200

    tools = {t.name: t for t in _tools(shop)}

    purchase = json.loads(tools["seller_inventory_movements"].invoke(
        {"operation_type": "purchase_in"}))
    assert len(purchase) == 1
    assert purchase[0]["operation_type"] == "purchase_in"

    limited = json.loads(tools["seller_inventory_movements"].invoke({"limit": 1}))
    assert len(limited) == 1


# ============================================================================
# 5. isolation
# ============================================================================


def test_seller_tools_are_isolated_by_shop():
    a = _create_shop("isoA")
    b = _create_shop("isoB")
    assert _purchase_in(a, quantity=10, total_amount=80).status_code == 200

    tools_a = {t.name: t for t in _tools(a)}
    tools_b = {t.name: t for t in _tools(b)}

    rows_a = json.loads(tools_a["seller_stock"].invoke(
        {"product_uid": a["product_uid"]}))
    assert len(rows_a) == 1 and float(rows_a[0]["quantity"]) == 10.0

    rows_b = json.loads(tools_b["seller_stock"].invoke(
        {"product_uid": a["product_uid"]}))
    assert rows_b == []

    sum_b = json.loads(tools_b["seller_summary"].invoke({}))
    assert sum_b["purchase_amount"] == 0.0


# ============================================================================
# 6. no DB ids in outputs
# ============================================================================


def test_seller_tool_outputs_have_no_db_ids():
    shop = _create_shop("noid")
    assert _purchase_in(shop, quantity=10, total_amount=80).status_code == 200
    assert _sales_out(shop, quantity=3, total_amount=45).status_code == 200

    tools = {t.name: t for t in _tools(shop)}
    for name, args in [
        ("seller_stock", {"product_uid": shop["product_uid"]}),
        ("seller_summary", {}),
        ("seller_product_summary", {}),
        ("seller_inventory_movements", {}),
    ]:
        result = tools[name].invoke(args)
        _assert_no_db_ids(json.loads(result))


# ============================================================================
# 7. signatures carry no identity / internal PK args
# ============================================================================


def test_seller_tool_signatures_have_no_identity_or_internal_pk_args():
    shop = _create_shop("sig")
    for tool in _tools(shop):
        args = set(tool.args.keys())
        assert not (args & _DB_ID_FIELDS), f"{tool.name} exposes DB id args: {args}"
        assert not (args & {"puid", "ouid", "pid", "oid"}), \
            f"{tool.name} exposes identity args: {args}"


# ============================================================================
# 8. read-only surface
# ============================================================================


def test_seller_tools_are_read_only():
    shop = _create_shop("ro")
    names = {t.name for t in _tools(shop)}
    assert names == _SELLER_TOOL_NAMES


# ============================================================================
# 9. safe errors
# ============================================================================


def test_invalid_tool_args_return_safe_error():
    shop = _create_shop("err")
    assert _purchase_in(shop, quantity=10, total_amount=80).status_code == 200

    tools = {t.name: t for t in _tools(shop)}

    unknown = json.loads(tools["seller_stock"].invoke(
        {"product_uid": "no_such_product_xyz"}))
    assert unknown == []

    bad_date = tools["seller_summary"].invoke({"date_from": "2026-13-99"})
    assert "查询失败" in bad_date
    assert "psycopg2" not in bad_date
    assert "ProgrammingError" not in bad_date
    assert "password" not in bad_date.lower()
