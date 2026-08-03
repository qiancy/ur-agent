"""
BE-03 TDD: Seller summary & query loop.

Business identifiers only: product_uid, warehouse_code, location_path,
counterparty_name, movement_uid. The BE-03 business endpoints never accept
or return database numeric primary keys, and assertions verify that.

Test setup may create a `total` stock row via seller purchase-in with
`location_path="total"`. That is setup-only and does not introduce a DB-ID
request pattern into BE-03 business endpoints.

Date filters are API-only (no direct DB time edits):
today/tomorrow/yesterday are computed in Asia/Shanghai.
"""
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)

_DB_ID_FIELDS = {
    "id", "resource_id", "warehouse_id", "resource_warehouse_id",
    "organization_id", "person_id", "transaction_id",
    "inventory_movement_id", "movement_id",
}


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _today():
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


def _dstr(d) -> str:
    return d.isoformat()


def _assert_no_db_ids(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in _DB_ID_FIELDS, f"leaked DB id field: {k}"
            _assert_no_db_ids(v)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_db_ids(item)


def _create_resource(shop: dict, name: str, resource_type: str,
                     unit: str = None, content: str = None) -> str:
    """Create a resource for setup. Returns the business resource UID."""
    body = {"name": name, "resource_type": resource_type}
    if unit is not None:
        body["unit"] = unit
    if content is not None:
        body["content"] = content
    resp = client.post(
        "/resource",
        headers=_auth_header(shop["token"]),
        json=body,
    )
    assert resp.status_code == 201, resp.text
    return name


def _create_product(shop: dict, name: str, unit: str = None) -> str:
    """Create a physical product for setup. Returns the business product UID."""
    return _create_resource(shop, name, "physical", unit=unit)


def _create_shop(tag: str, location_path: str = "A-01") -> dict:
    """Create a self-contained ecommerce shop (each call gets a unique suffix)."""
    s = uuid.uuid4().hex[:8]

    ouid = f"be03_{tag}_{s}"
    resp = client.post("/organizations", json={
        "name": f"BE03_{tag}_{s}", "org_type": "ecommerce", "ouid": ouid,
    })
    assert resp.status_code in (200, 201), resp.text

    login = f"seller_{tag}_{s}"
    resp = client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": f"卖家{tag}_{s}",
        "initial_ouid": ouid,
    })
    assert resp.status_code == 201, resp.text

    resp = client.post("/auth/seller-login", json={
        "login": login, "password": "pass123",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    product_uid = f"prod_{tag}_{s}"
    _create_product({"token": token}, product_uid)

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
        "base_location": location_path,
    }


def _purchase_in(shop: dict, quantity: float, total_amount: float = None,
                 product_uid: str = None, location_path: str = None,
                 warehouse_code: str = None) -> object:
    if total_amount is None:
        total_amount = quantity * 8
    return client.post(
        "/seller/purchase-in",
        headers=_auth_header(shop["token"]),
        json={
            "product_uid": product_uid or shop["product_uid"],
            "warehouse_code": warehouse_code or shop["warehouse_code"],
            "location_path": location_path or shop["base_location"],
            "quantity": quantity,
            "unit": "件",
            "total_amount": total_amount,
            "counterparty_name": "BE03供应商",
        },
    )


def _sales_out(shop: dict, quantity: float, total_amount: float = None,
               product_uid: str = None, location_path: str = None,
               warehouse_code: str = None) -> object:
    if total_amount is None:
        total_amount = quantity * 15
    return client.post(
        "/seller/sales-out",
        headers=_auth_header(shop["token"]),
        json={
            "product_uid": product_uid or shop["product_uid"],
            "warehouse_code": warehouse_code or shop["warehouse_code"],
            "location_path": location_path or shop["base_location"],
            "quantity": quantity,
            "unit": "件",
            "total_amount": total_amount,
            "counterparty_name": "BE03买家",
        },
    )


def _summary(shop: dict, **params) -> dict:
    resp = client.get("/seller/summary", headers=_auth_header(shop["token"]), params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _product_summary(shop: dict, **params) -> dict:
    resp = client.get("/seller/product-summary", headers=_auth_header(shop["token"]), params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _movements(shop: dict, **params) -> list:
    resp = client.get("/seller/inventory-movements", headers=_auth_header(shop["token"]), params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _add_total_row(shop: dict, quantity: float = 999.0) -> object:
    """Create a 'total' summary row through seller purchase-in only."""
    return _purchase_in(shop, quantity=quantity, location_path="total")


# ============================================================================


def test_summary_requires_jwt():
    resp = client.get("/seller/summary")
    assert resp.status_code in (401, 403), resp.text


def test_summary_counts_purchase_and_sales():
    shop = _create_shop("cnt")
    resp = _purchase_in(shop, quantity=10, total_amount=80)
    assert resp.status_code == 200, resp.text
    resp = _sales_out(shop, quantity=3, total_amount=45)
    assert resp.status_code == 200, resp.text

    data = _summary(shop)
    assert data["status"] == "ok"
    assert data["purchase_amount"] == 80.0
    assert data["sales_amount"] == 45.0
    assert data["net_cash_flow"] == -35.0
    assert data["purchase_count"] == 1
    assert data["sales_count"] == 1
    assert data["movement_count"] == 2
    assert data["product_count"] == 1
    assert data["stock_location_count"] == 1
    assert data["current_stock_quantity"] == 7.0
    assert data["estimated_inventory_value"] == 56.0
    assert data["valuation_method"] == "weighted_average_purchase_cost"
    assert data["date_from"] is None
    assert data["date_to"] is None


def test_summary_isolated_by_shop():
    a = _create_shop("isoA")
    b = _create_shop("isoB")
    assert _purchase_in(a, quantity=10, total_amount=80).status_code == 200
    assert _purchase_in(b, quantity=5, total_amount=40).status_code == 200

    sa = _summary(a)
    sb = _summary(b)
    assert sa["purchase_amount"] == 80.0
    assert sa["purchase_count"] == 1
    assert sa["product_count"] == 1
    assert sb["purchase_amount"] == 40.0
    assert sb["purchase_count"] == 1
    assert sb["product_count"] == 1


def test_summary_date_range_filters_movements():
    shop = _create_shop("dr")
    assert _purchase_in(shop, quantity=10, total_amount=80).status_code == 200

    today = _today()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    s_today = _summary(shop, date_from=_dstr(today), date_to=_dstr(today))
    assert s_today["purchase_amount"] == 80.0
    assert s_today["movement_count"] == 1
    assert s_today["date_from"] == _dstr(today)
    assert s_today["date_to"] == _dstr(today)

    s_future = _summary(shop, date_from=_dstr(tomorrow), date_to=_dstr(tomorrow))
    assert s_future["purchase_amount"] == 0.0
    assert s_future["movement_count"] == 0

    s_past = _summary(shop, date_from=_dstr(yesterday), date_to=_dstr(yesterday))
    assert s_past["purchase_amount"] == 0.0

    assert s_future["current_stock_quantity"] == 10.0
    assert s_past["current_stock_quantity"] == 10.0


def test_summary_has_no_db_ids():
    shop = _create_shop("id5")
    assert _purchase_in(shop, quantity=3, total_amount=24).status_code == 200
    _assert_no_db_ids(_summary(shop))


def test_inventory_movements_requires_jwt():
    resp = client.get("/seller/inventory-movements")
    assert resp.status_code in (401, 403), resp.text


def test_product_summary_requires_jwt():
    resp = client.get("/seller/product-summary")
    assert resp.status_code in (401, 403), resp.text


def test_inventory_movements_isolated_by_shop():
    a = _create_shop("mv8a")
    b = _create_shop("mv8b")
    assert _purchase_in(a, quantity=4, total_amount=32).status_code == 200
    assert _purchase_in(b, quantity=9, total_amount=72).status_code == 200

    rows = _movements(a)
    assert len(rows) == 1
    assert rows[0]["product_uid"] == a["product_uid"]
    assert rows[0]["quantity_delta"] == 4.0


def test_inventory_movements_filter_by_type_and_date():
    shop = _create_shop("ft")
    assert _purchase_in(shop, quantity=10, total_amount=80).status_code == 200
    assert _sales_out(shop, quantity=3, total_amount=45).status_code == 200

    sales_rows = _movements(shop, operation_type="sales_out")
    assert len(sales_rows) == 1
    assert sales_rows[0]["operation_type"] == "sales_out"
    purchase_rows = _movements(shop, operation_type="purchase_in")
    assert len(purchase_rows) == 1
    assert purchase_rows[0]["operation_type"] == "purchase_in"

    today = _today()
    tomorrow = today + timedelta(days=1)
    rows_today = _movements(shop, date_from=_dstr(today), date_to=_dstr(today))
    assert len(rows_today) == 2
    rows_future = _movements(shop, date_from=_dstr(tomorrow), date_to=_dstr(tomorrow))
    assert rows_future == []


def test_inventory_movements_limit_offset_keeps_list_response():
    shop = _create_shop("lo")
    for _ in range(5):
        assert _purchase_in(shop, quantity=1, total_amount=8).status_code == 200

    all_rows = _movements(shop)
    assert isinstance(all_rows, list)
    assert len(all_rows) == 5

    page = _movements(shop, limit=2)
    assert isinstance(page, list)
    assert len(page) == 2

    page2 = _movements(shop, limit=2, offset=2)
    assert isinstance(page2, list)
    assert len(page2) == 2
    assert page2[0]["movement_uid"] != page[0]["movement_uid"]

    off_only = _movements(shop, offset=3)
    assert isinstance(off_only, list)
    assert len(off_only) == 5


def test_product_summary_returns_per_product_metrics():
    shop = _create_shop("pm")
    assert _purchase_in(shop, quantity=3, total_amount=10).status_code == 200
    assert _sales_out(shop, quantity=1, total_amount=15).status_code == 200

    body = _product_summary(shop)
    assert body["status"] == "ok"
    assert len(body["items"]) == 1
    it = body["items"][0]
    assert it["product_uid"] == shop["product_uid"]
    assert it["unit"] == "件"
    assert it["current_quantity"] == 2.0
    assert it["purchase_quantity"] == 3.0
    assert it["sales_quantity"] == 1.0
    assert it["purchase_amount"] == 10.0
    assert it["sales_amount"] == 15.0
    assert it["movement_count"] == 2
    assert it["estimated_inventory_value"] == 6.67


def test_product_summary_isolated_by_shop():
    a = _create_shop("iso12a")
    b = _create_shop("iso12b")
    shared = f"shared_prod_{uuid.uuid4().hex[:8]}"
    _create_product(a, shared)
    _create_product(b, shared)
    assert _purchase_in(a, product_uid=shared, quantity=5, total_amount=40).status_code == 200
    assert _purchase_in(b, product_uid=shared, quantity=2, total_amount=16).status_code == 200

    pa = _product_summary(a, product_uid=shared)
    pb = _product_summary(b, product_uid=shared)
    assert len(pa["items"]) == 1
    assert pa["items"][0]["current_quantity"] == 5.0
    assert pa["items"][0]["purchase_amount"] == 40.0
    assert len(pb["items"]) == 1
    assert pb["items"][0]["current_quantity"] == 2.0
    assert pb["items"][0]["purchase_amount"] == 16.0


def test_product_summary_has_no_db_ids():
    shop = _create_shop("id13")
    assert _purchase_in(shop, quantity=3, total_amount=24).status_code == 200
    _assert_no_db_ids(_product_summary(shop))


def test_product_summary_current_quantity_ignores_date_range():
    shop = _create_shop("cqr")
    assert _purchase_in(shop, quantity=10, total_amount=80).status_code == 200
    tomorrow = _today() + timedelta(days=1)

    body = _product_summary(shop, date_from=_dstr(tomorrow), date_to=_dstr(tomorrow))
    assert body["status"] == "ok"
    it = body["items"][0]
    assert it["current_quantity"] == 10.0
    assert it["purchase_amount"] == 0.0
    assert it["sales_amount"] == 0.0
    assert it["movement_count"] == 0


def test_quantities_are_positive_in_summary_outputs():
    shop = _create_shop("pos")
    assert _purchase_in(shop, quantity=10, total_amount=80).status_code == 200
    assert _sales_out(shop, quantity=3, total_amount=45).status_code == 200

    s = _summary(shop)
    assert s["top_products_by_sales"][0]["sales_quantity"] == 3.0
    assert s["top_products_by_sales"][0]["sales_quantity"] > 0

    ps = _product_summary(shop)
    it = ps["items"][0]
    assert it["purchase_quantity"] == 10.0
    assert it["sales_quantity"] == 3.0
    assert it["purchase_quantity"] >= 0
    assert it["sales_quantity"] >= 0


def test_low_stock_items_use_threshold():
    shop = _create_shop("low")
    assert _purchase_in(shop, quantity=3, total_amount=24).status_code == 200
    b_uid = f"prod_b_{uuid.uuid4().hex[:8]}"
    _create_product(shop, b_uid, unit="个")
    resp = _add_total_row(shop, quantity=999)
    assert resp.status_code == 200, resp.text

    s0 = _summary(shop, low_stock_threshold=0)
    uids0 = [x["product_uid"] for x in s0["low_stock_items"]]
    assert b_uid in uids0
    assert shop["product_uid"] not in uids0
    assert s0["current_stock_quantity"] == 3.0
    assert s0["stock_location_count"] == 1

    s5 = _summary(shop, low_stock_threshold=5)
    uids5 = [x["product_uid"] for x in s5["low_stock_items"]]
    assert shop["product_uid"] in uids5
    assert b_uid in uids5
    item_b = next(x for x in s5["low_stock_items"] if x["product_uid"] == b_uid)
    assert item_b["quantity"] == 0.0
    assert item_b["unit"] == "个"


def test_top_products_by_sales_order_and_limit():
    shop = _create_shop("top")
    x = uuid.uuid4().hex[:8]
    p1 = f"prod_top_a_{x}"
    p2 = f"prod_top_b_{x}"
    p3 = f"prod_top_c_{x}"
    for p in (p1, p2, p3):
        _create_product(shop, p)
    # sales: p1=100, p2=300, p3=100 (tie p1 vs p3 -> p1 first by product_uid ASC)
    assert _purchase_in(shop, product_uid=p1, quantity=10, total_amount=80).status_code == 200
    assert _purchase_in(shop, product_uid=p2, quantity=20, total_amount=160).status_code == 200
    assert _purchase_in(shop, product_uid=p3, quantity=10, total_amount=80).status_code == 200
    assert _sales_out(shop, product_uid=p1, quantity=4, total_amount=100).status_code == 200
    assert _sales_out(shop, product_uid=p2, quantity=12, total_amount=300).status_code == 200
    assert _sales_out(shop, product_uid=p3, quantity=4, total_amount=100).status_code == 200

    s2 = _summary(shop, top_n=2)
    assert [t["product_uid"] for t in s2["top_products_by_sales"]] == [p2, p1]
    s_all = _summary(shop, top_n=20)
    assert [t["product_uid"] for t in s_all["top_products_by_sales"]] == [p2, p1, p3]


def test_seller_summary_counts_only_physical_products():
    shop = _create_shop("rtype")
    x = uuid.uuid4().hex[:8]
    knowledge_uid = f"knowledge_{x}"
    finance_uid = f"finance_{x}"
    _create_resource(shop, knowledge_uid, "knowledge", content="非库存资料")
    _create_resource(shop, finance_uid, "financial")

    s = _summary(shop, low_stock_threshold=0)
    assert s["product_count"] == 1
    low_uids = [x["product_uid"] for x in s["low_stock_items"]]
    assert shop["product_uid"] in low_uids
    assert knowledge_uid not in low_uids
    assert finance_uid not in low_uids

    body = _product_summary(shop)
    assert [x["product_uid"] for x in body["items"]] == [shop["product_uid"]]
    assert _product_summary(shop, product_uid=knowledge_uid)["items"] == []

    resp = _purchase_in(shop, product_uid=knowledge_uid, quantity=1, total_amount=1)
    assert resp.status_code == 404


def test_seller_query_endpoints_reject_invalid_date_range():
    shop = _create_shop("drx")
    for path in ("/seller/summary", "/seller/product-summary", "/seller/inventory-movements"):
        resp = client.get(
            path, headers=_auth_header(shop["token"]),
            params={"date_from": "2026-07-01", "date_to": "2026-06-30"},
        )
        assert resp.status_code == 422, (path, resp.status_code, resp.text)


def test_summary_rejects_invalid_threshold_and_top_n():
    shop = _create_shop("inv")
    for params in ({"low_stock_threshold": "-1"}, {"top_n": "0"}, {"top_n": "21"}):
        resp = client.get("/seller/summary", headers=_auth_header(shop["token"]), params=params)
        assert resp.status_code == 422, (params, resp.status_code, resp.text)


def test_inventory_movements_rejects_invalid_filters():
    shop = _create_shop("mvf")
    for params in ({"operation_type": "invalid"},
                   {"limit": "0"}, {"limit": "201"}, {"offset": "-1"},
                   {"date_from": "2026/07/31"}, {"date_to": "31-07-2026"}):
        resp = client.get(
            "/seller/inventory-movements",
            headers=_auth_header(shop["token"]),
            params=params,
        )
        assert resp.status_code == 422, (params, resp.status_code, resp.text)


def test_summary_empty_shop_all_zero():
    shop = _create_shop("empty")
    data = _summary(shop)
    assert data["status"] == "ok"
    assert data["purchase_amount"] == 0.0
    assert data["sales_amount"] == 0.0
    assert data["net_cash_flow"] == 0.0
    assert data["purchase_count"] == 0
    assert data["sales_count"] == 0
    assert data["current_stock_quantity"] == 0.0
    assert data["top_products_by_sales"] == []
    assert len(data["low_stock_items"]) == 1
    assert data["low_stock_items"][0]["product_uid"] == shop["product_uid"]
    assert data["low_stock_items"][0]["quantity"] == 0.0
    body = _product_summary(shop)
    assert body["status"] == "ok"
    assert len(body["items"]) == 1
    it = body["items"][0]
    assert it["product_uid"] == shop["product_uid"]
    assert it["current_quantity"] == 0.0
    assert it["purchase_quantity"] == 0.0
    assert it["sales_quantity"] == 0.0
    assert it["purchase_amount"] == 0.0
    assert it["sales_amount"] == 0.0
    assert it["movement_count"] == 0


def test_unknown_product_uid_returns_empty_query_result():
    shop = _create_shop("unk")
    unknown = f"no_such_prod_{uuid.uuid4().hex[:8]}"
    rows = _movements(shop, product_uid=unknown)
    assert rows == []
    body = _product_summary(shop, product_uid=unknown)
    assert body["status"] == "ok"
    assert body["items"] == []


def test_seller_query_endpoints_reject_identity_and_db_id_params():
    shop = _create_shop("idp")
    forbidden = [
        "id",
        "puid", "ouid",
        "organization_id", "person_id", "resource_id",
        "warehouse_id", "transaction_id",
        "resource_warehouse_id", "inventory_movement_id", "movement_id",
    ]
    paths = [
        "/seller/stock",
        "/seller/inventory-movements",
        "/seller/summary",
        "/seller/product-summary",
    ]
    for path in paths:
        for key in forbidden:
            resp = client.get(
                path, headers=_auth_header(shop["token"]), params={key: "1"},
            )
            assert resp.status_code in (400, 422), (
                path, key, resp.status_code, resp.text
            )
