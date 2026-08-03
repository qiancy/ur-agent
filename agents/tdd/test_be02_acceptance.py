"""
BE-02 PM acceptance tests.

Covers the 5 PM Review findings:
  1. Concurrent sales-out must not oversell (row lock on resource_warehouse).
  2. Stock is separated by warehouse (same product + location, two warehouses).
  3. Negative quantity / amount rejected with 422 (Pydantic validation).
  4. Campaign import delete still works end-to-end (regression).
"""
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_shop(tag: str, location_path: str = "A-01") -> dict:
    """Create a self-contained ecommerce shop (each call gets a unique suffix)."""
    s = uuid.uuid4().hex[:8]

    ouid = f"be02acc_{tag}_{s}"
    resp = client.post("/organizations", json={
        "name": f"BE02ACC_{tag}_{s}", "org_type": "ecommerce", "ouid": ouid,
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
    resp = client.post(
        "/resource",
        headers=_auth_header(token),
        json={"name": product_uid, "resource_type": "physical"},
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
        "base_location": location_path,
    }


def _purchase_in(shop: dict, quantity: float, location_path: str = None,
                 warehouse_code: str = None) -> object:
    return client.post(
        "/seller/purchase-in",
        headers=_auth_header(shop["token"]),
        json={
            "product_uid": shop["product_uid"],
            "warehouse_code": warehouse_code or shop["warehouse_code"],
            "location_path": location_path or shop["base_location"],
            "quantity": quantity,
            "unit": "件",
            "total_amount": quantity * 8,
            "counterparty_name": "验收供应商",
        },
    )


def _sales_out(shop: dict, quantity: float, location_path: str = None,
               warehouse_code: str = None) -> object:
    return client.post(
        "/seller/sales-out",
        headers=_auth_header(shop["token"]),
        json={
            "product_uid": shop["product_uid"],
            "warehouse_code": warehouse_code or shop["warehouse_code"],
            "location_path": location_path or shop["base_location"],
            "quantity": quantity,
            "unit": "件",
            "total_amount": quantity * 15,
            "counterparty_name": "验收买家",
        },
    )


def _stock(shop: dict) -> list:
    resp = client.get(
        "/seller/stock",
        headers=_auth_header(shop["token"]),
        params={"product_uid": shop["product_uid"]},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _movement_count(shop: dict) -> int:
    resp = client.get(
        "/seller/inventory-movements",
        headers=_auth_header(shop["token"]),
        params={"product_uid": shop["product_uid"]},
    )
    assert resp.status_code == 200, resp.text
    return len(resp.json())


def _first_resource_id(shop: dict) -> int:
    resp = client.get("/resource", headers=_auth_header(shop["token"]))
    assert resp.status_code == 200, resp.text
    return resp.json()[0]["id"]


def _transaction_count(shop: dict) -> int:
    resp = client.get(
        "/transactions",
        headers=_auth_header(shop["token"]),
    )
    assert resp.status_code == 200, resp.text
    return len(resp.json())


# ============================================================================
# 1. Concurrent sales-out must not oversell
# ============================================================================

class TestConcurrentSalesOut:
    """Two simultaneous sales-out of 6 from stock 10 → one 200, one 409."""

    def test_concurrent_sales_out_does_not_oversell(self):
        shop = _create_shop("conc")
        resp = _purchase_in(shop, 10)
        assert resp.status_code == 200, resp.text

        barrier = threading.Barrier(2)
        results = []

        def sell():
            barrier.wait()
            results.append(_sales_out(shop, 6))

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(sell) for _ in range(2)]
            for f in futures:
                f.result()

        statuses = sorted(r.status_code for r in results)
        assert statuses == [200, 409], (
            f"Expected one success + one 409, got {statuses}"
        )

        stock = _stock(shop)
        match = [s for s in stock if s["location_path"] == shop["base_location"]]
        assert len(match) == 1
        assert match[0]["quantity"] == 4, (
            f"Oversell detected: expected final stock 4, got {match[0]['quantity']}"
        )

        assert _transaction_count(shop) == 2, "Concurrent oversell created extra transactions"
        assert _movement_count(shop) == 2, "Concurrent oversell created extra movements"


# ============================================================================
# 2. Stock separated by warehouse (same product + location)
# ============================================================================

class TestWarehouseDimension:
    """Same product_uid + location_path in two warehouses stays independent."""

    def test_same_location_different_warehouse_are_separate_stock_rows(self):
        shop = _create_shop("wdim")

        wh2_code = f"wh2_{uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/warehouse",
            headers=_auth_header(shop["token"]),
            json={"name": "第二仓库", "code": wh2_code},
        )
        assert resp.status_code == 201, resp.text

        resp = _purchase_in(shop, 10)  # wh1 @ A-01
        assert resp.status_code == 200, resp.text
        resp = _purchase_in(shop, 20, warehouse_code=wh2_code)  # wh2 @ A-01
        assert resp.status_code == 200, resp.text

        stock = _stock(shop)
        loc_rows = [s for s in stock if s["location_path"] == shop["base_location"]]
        assert len(loc_rows) == 2, (
            f"Expected 2 stock rows for same location, got {loc_rows}"
        )
        by_code = {s["warehouse_code"]: s["quantity"] for s in loc_rows}
        assert by_code.get(shop["warehouse_code"]) == 10
        assert by_code.get(wh2_code) == 20

        # Sales-out from wh2 only affects wh2
        resp = _sales_out(shop, 5, warehouse_code=wh2_code)
        assert resp.status_code == 200, resp.text

        stock = _stock(shop)
        loc_rows = [s for s in stock if s["location_path"] == shop["base_location"]]
        by_code = {s["warehouse_code"]: s["quantity"] for s in loc_rows}
        assert by_code[shop["warehouse_code"]] == 10, "wh1 stock changed"
        assert by_code[wh2_code] == 15, "wh2 stock not decremented"


# ============================================================================
# 3. Negative quantity / amount rejected with 422
# ============================================================================

class TestNegativeValidation:
    """quantity <= 0 or total_amount < 0 must be rejected by Pydantic (422)."""

    def test_purchase_in_rejects_negative_quantity(self):
        shop = _create_shop("negq_pi")
        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": -5, "unit": "件",
                "total_amount": 40,
                "counterparty_name": "负数量",
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for negative quantity, got {resp.status_code}: {resp.text}"
        )

        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 0, "unit": "件",
                "total_amount": 0,
                "counterparty_name": "零数量",
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for zero quantity, got {resp.status_code}: {resp.text}"
        )

    def test_purchase_in_rejects_negative_amount(self):
        shop = _create_shop("nega_pi")
        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 5, "unit": "件",
                "total_amount": -1,
                "counterparty_name": "负金额",
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for negative amount, got {resp.status_code}: {resp.text}"
        )

    def test_sales_out_rejects_negative_quantity(self):
        shop = _create_shop("negq_so")
        resp = client.post(
            "/seller/sales-out",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": -3, "unit": "件",
                "total_amount": 45,
                "counterparty_name": "负数量",
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for negative quantity, got {resp.status_code}: {resp.text}"
        )

    def test_sales_out_rejects_negative_amount(self):
        shop = _create_shop("nega_so")
        resp = client.post(
            "/seller/sales-out",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 3, "unit": "件",
                "total_amount": -1,
                "counterparty_name": "负金额",
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for negative amount, got {resp.status_code}: {resp.text}"
        )


# ============================================================================
# 3b. Public /resource-warehouse ownership (PM P0-1)
# ============================================================================

class TestResourceWarehouseOwnership:
    """Public API takes warehouse_code only; DB IDs and cross-org codes rejected."""

    def test_warehouse_id_field_is_rejected(self):
        shop = _create_shop("own_id")
        resp = client.post(
            "/resource-warehouse",
            headers=_auth_header(shop["token"]),
            json={"resource_id": _first_resource_id(shop), "warehouse_id": 1,
                  "location_path": "X-1", "quantity": 5, "unit": "件"},
        )
        assert resp.status_code == 422, (
            f"Expected 422 for warehouse_id field, got {resp.status_code}: {resp.text}"
        )

    def test_other_org_warehouse_code_is_rejected(self):
        shop_a = _create_shop("own_a")
        shop_b = _create_shop("own_b")
        rid_a = _first_resource_id(shop_a)

        resp = client.post(
            "/resource-warehouse",
            headers=_auth_header(shop_a["token"]),
            json={"resource_id": rid_a, "warehouse_code": shop_b["warehouse_code"],
                  "location_path": "X-1", "quantity": 5, "unit": "件"},
        )
        assert resp.status_code == 404, (
            f"Expected 404 for cross-org warehouse_code, "
            f"got {resp.status_code}: {resp.text}"
        )

        # No stock row was created
        resp = client.get(
            "/resource-warehouse",
            params={"resource_id": rid_a},
            headers=_auth_header(shop_a["token"]),
        )
        assert resp.status_code == 200, resp.text
        assert all(rw["location_path"] != "X-1" for rw in resp.json()), (
            "Cross-org warehouse_code created a spurious stock row"
        )

    def test_own_warehouse_code_resolves_inside_org(self):
        shop = _create_shop("own_ok")
        rid = _first_resource_id(shop)
        resp = client.post(
            "/resource-warehouse",
            headers=_auth_header(shop["token"]),
            json={"resource_id": rid, "warehouse_code": shop["warehouse_code"],
                  "location_path": "S-1", "quantity": 7, "unit": "件"},
        )
        assert resp.status_code == 201, (
            f"Expected 201 for own warehouse_code, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["location_path"] == "S-1"
        assert "warehouse_id" in body
        assert body["quantity"] == 7


# ============================================================================
# 4. Campaign import delete regression
# ============================================================================class TestCampaignImportDelete:
    """DELETE /campaigns/imports/{campaign_code} removes all imported org data."""

    def _super_token(self) -> str:
        resp = client.post("/auth/login", json={
            "login": "super@system.cn", "password": "demo123",
        })
        assert resp.status_code == 200, resp.text
        return resp.json()["access_token"]

    def test_delete_campaign_import_cleans_everything(self):
        token = self._super_token()
        headers = _auth_header(token)

        resp = client.post(
            "/campaigns/import",
            headers=headers,
            json={"campaign_code": "fire_xinye"},
        )
        assert resp.status_code in (200, 201), resp.text
        body = resp.json()
        campaign_import = body.get("campaign_import")
        campaign_code = campaign_import.get("campaign_code") or body.get("campaign_code")
        assert campaign_code, f"Import response has no campaign_code: {body}"
        assert "id" not in campaign_import, (
            f"Campaign import response must not expose DB id: {campaign_import}"
        )
        for org in body.get("organizations", []):
            assert "id" not in org, f"Import response org must not expose DB id: {org}"
        for person in body.get("persons", []):
            assert "id" not in person, f"Import response person must not expose DB id: {person}"

        # Data exists before delete
        resp = client.get("/organizations", params={"ouid": "fire_xinye_shu"})
        assert resp.status_code == 200, resp.text
        assert any(o["ouid"] == "fire_xinye_shu" for o in resp.json()), (
            "fire_xinye_shu org missing after import"
        )

        resp = client.delete(f"/campaigns/imports/{campaign_code}", headers=headers)
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text}"
        )
        del_body = resp.json()
        assert del_body.get("deleted") is True
        assert del_body.get("campaign_import", {}).get("status") == "deleted"
        assert "id" not in del_body.get("campaign_import", {}), (
            f"Campaign delete response must not expose DB id: {del_body.get('campaign_import')}"
        )

        # Imported orgs/resources/warehouses are gone
        resp = client.get("/organizations", params={"ouid": "fire_xinye_shu"})
        assert resp.status_code == 200, resp.text
        assert all(o["ouid"] != "fire_xinye_shu" for o in resp.json()), (
            "fire_xinye_shu org still exists after delete"
        )
