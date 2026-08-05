"""
BE-02 TDD: Seller inventory transaction atomicity.

RED phase — all 10 BE-02 tests must FAIL before BE-02 implementation.
Test 11 (Three Kingdoms regression) should PASS independently.

Business identifiers only: product_uid, warehouse_code, location_path,
counterparty_name. No database numeric primary keys in assertions.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

_ALLOWED_BUSINESS_FIELDS = {
    "status", "operation_type", "product_uid", "product_name",
    "warehouse_code", "location_path", "quantity", "unit",
    "total_amount", "counterparty_name", "movement_uid",
    "quantity_delta", "new_quantity", "created_at",
}
_DB_ID_FIELDS = {
    "id", "resource_id", "warehouse_id",
    "organization_id", "person_id",
    "transaction_id", "resource_warehouse_id",
    "inventory_movement_id",
}


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_shop(tag: str, location_path: str = "A-01") -> dict:
    """Create a self-contained ecommerce shop (each call gets a unique suffix)."""
    s = uuid.uuid4().hex[:8]

    login = f"seller_{tag}_{s}"
    resp = client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": f"卖家{tag}_{s}",
    })
    assert resp.status_code == 201, resp.text

    ouid = f"be02_{tag}_{s}"
    resp = client.post("/spaces", headers=_auth_header(resp.json()["access_token"]), json={
        "name": f"BE02_{tag}_{s}", "org_type": "ecommerce", "ouid": ouid,
    })
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    puid = resp.json().get("person", {}).get("puid")

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
        "puid": puid,
        "token": token,
        "product_uid": product_uid,
        "warehouse_code": wh_code,
        "base_location": location_path,
    }


def _count_objects(shop: dict) -> dict:
    """Count transactions and movements for a shop's org."""
    tx_resp = client.get(
        "/transactions",
        headers=_auth_header(shop["token"]),
    )
    tx_count = len(tx_resp.json()) if tx_resp.status_code == 200 else 0

    mv_resp = client.get(
        "/seller/inventory-movements",
        headers=_auth_header(shop["token"]),
        params={"product_uid": shop["product_uid"]},
    )
    mv_count = len(mv_resp.json()) if mv_resp.status_code == 200 else 0

    return {"transactions": tx_count, "movements": mv_count}


# ============================================================================
# Tests 1-2: Purchase-in (buy-in / stock increase)
# ============================================================================

class TestPurchaseIn:
    """POST /seller/purchase-in"""

    def test_purchase_in_increases_stock(self):
        """GIVEN a shop WHEN purchase-in 20 units THEN new_quantity=20."""
        shop = _create_shop("a01")
        payload = {
            "product_uid": shop["product_uid"],
            "warehouse_code": shop["warehouse_code"],
            "location_path": shop["base_location"],
            "quantity": 20,
            "unit": "件",
            "total_amount": 160,
            "counterparty_name": "供应商A",
        }
        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop["token"]),
            json=payload,
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["status"] == "ok"
        assert body["operation_type"] == "purchase_in"
        assert body["product_uid"] == shop["product_uid"]
        assert body["warehouse_code"] == shop["warehouse_code"]
        assert body["location_path"] == shop["base_location"]
        assert body["quantity_delta"] == 20
        assert body["new_quantity"] == 20
        assert body["total_amount"] == 160
        assert body["counterparty_name"] == "供应商A"
        assert "movement_uid" in body
        assert body["movement_uid"].startswith("mv_")

        # Stock query also shows 20
        resp2 = client.get(
            "/seller/stock",
            headers=_auth_header(shop["token"]),
            params={"product_uid": shop["product_uid"]},
        )
        assert resp2.status_code == 200, resp2.text
        match = [s for s in resp2.json()
                 if s["location_path"] == shop["base_location"]]
        assert len(match) == 1
        assert match[0]["quantity"] == 20

    def test_purchase_in_records_transaction_and_movement(self):
        """Purchase-in creates 1 transaction AND 1 movement."""
        shop = _create_shop("a02")
        before = _count_objects(shop)

        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 30, "unit": "件",
                "total_amount": 240,
                "counterparty_name": "供应商B",
            },
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text}"
        )
        mv_uid = resp.json().get("movement_uid")

        after = _count_objects(shop)
        assert after["transactions"] == before["transactions"] + 1, (
            f"Expected 1 new transaction, before={before} after={after}"
        )
        assert after["movements"] == before["movements"] + 1, (
            f"Expected 1 new movement, before={before} after={after}"
        )

        # Movement detail matches
        resp2 = client.get(
            "/seller/inventory-movements",
            headers=_auth_header(shop["token"]),
            params={"product_uid": shop["product_uid"]},
        )
        assert resp2.status_code == 200, resp2.text
        match = [m for m in resp2.json() if m.get("movement_uid") == mv_uid]
        assert len(match) == 1
        mv = match[0]
        assert mv["operation_type"] == "purchase_in"
        assert mv["quantity_delta"] == 30
        assert mv["total_amount"] == 240
        assert mv["counterparty_name"] == "供应商B"


# ============================================================================
# Tests 3-4: Sales-out (sell / stock decrease)
# ============================================================================

class TestSalesOut:
    """POST /seller/sales-out"""

    def test_sales_out_decreases_stock(self):
        """GIVEN 50 units WHEN sales-out 3 THEN new_quantity=47."""
        shop = _create_shop("s01")

        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 50, "unit": "件",
                "total_amount": 400,
                "counterparty_name": "种子供应商",
            },
        )
        assert resp.status_code == 200, resp.text

        resp = client.post(
            "/seller/sales-out",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 3, "unit": "件",
                "total_amount": 45,
                "counterparty_name": "淘宝买家甲",
            },
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["status"] == "ok"
        assert body["operation_type"] == "sales_out"
        assert body["quantity_delta"] == -3
        assert body["new_quantity"] == 47
        assert "movement_uid" in body

        resp2 = client.get(
            "/seller/stock",
            headers=_auth_header(shop["token"]),
            params={"product_uid": shop["product_uid"]},
        )
        assert resp2.status_code == 200, resp2.text
        match = [s for s in resp2.json()
                 if s["location_path"] == shop["base_location"]]
        assert match[0]["quantity"] == 47

    def test_sales_out_rejects_insufficient_stock(self):
        """GIVEN 10 units WHEN sales-out 20 THEN 409, stock+tx+mv unchanged."""
        shop = _create_shop("s02")

        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 10, "unit": "件",
                "total_amount": 80,
                "counterparty_name": "种子供应商",
            },
        )
        assert resp.status_code == 200, resp.text

        before_stock = client.get(
            "/seller/stock",
            headers=_auth_header(shop["token"]),
            params={"product_uid": shop["product_uid"]},
        )
        assert before_stock.status_code == 200, before_stock.text
        before_qty = before_stock.json()[0]["quantity"]
        before_objects = _count_objects(shop)

        resp = client.post(
            "/seller/sales-out",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 20, "unit": "件",
                "total_amount": 300,
                "counterparty_name": "淘宝买家乙",
            },
        )
        assert resp.status_code == 409, (
            f"Expected 409, got {resp.status_code}: {resp.text}"
        )

        after_stock = client.get(
            "/seller/stock",
            headers=_auth_header(shop["token"]),
            params={"product_uid": shop["product_uid"]},
        )
        assert after_stock.status_code == 200, after_stock.text
        assert after_stock.json()[0]["quantity"] == before_qty

        after_objects = _count_objects(shop)
        assert after_objects == before_objects, (
            f"Transaction/movement count changed: {before_objects} -> {after_objects}"
        )


# ============================================================================
# Test 5: Cross-shop isolation
# ============================================================================

class TestCrossShopIsolation:
    """Shop B must not affect Shop A's inventory."""

    def test_other_shop_cannot_affect_shop_a_stock(self):
        """Shop B's JWT prevents access to shop A's product."""
        shop_a = _create_shop("cs_a")
        shop_b = _create_shop("cs_b", "B-01")

        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop_a["token"]),
            json={
                "product_uid": shop_a["product_uid"],
                "warehouse_code": shop_a["warehouse_code"],
                "location_path": shop_a["base_location"],
                "quantity": 30, "unit": "件",
                "total_amount": 240,
                "counterparty_name": "供应商A",
            },
        )
        assert resp.status_code == 200, resp.text

        # Shop B tries shop A's product_uid
        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop_b["token"]),
            json={
                "product_uid": shop_a["product_uid"],
                "warehouse_code": shop_b["warehouse_code"],
                "location_path": shop_b["base_location"],
                "quantity": 10, "unit": "件",
                "total_amount": 80,
                "counterparty_name": "跨店尝试",
            },
        )
        assert resp.status_code in (403, 404), (
            f"Expected 403/404, got {resp.status_code}: {resp.text}"
        )

        # Shop A stock unchanged
        check = client.get(
            "/seller/stock",
            headers=_auth_header(shop_a["token"]),
            params={"product_uid": shop_a["product_uid"]},
        )
        assert check.status_code == 200, check.text
        match = [s for s in check.json()
                 if s["location_path"] == shop_a["base_location"]]
        assert match[0]["quantity"] == 30


# ============================================================================
# Test 6: Failed sales-out creates no artifacts
# ============================================================================

class TestFailedSalesOutNoArtifacts:
    """Failed outbound must roll back completely — no tx, no movement."""

    def test_failed_sales_out_creates_no_transaction_or_movement(self):
        """WHEN sales-out insufficient THEN 409 AND tx+mv count unchanged."""
        shop = _create_shop("f01")

        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 10, "unit": "件",
                "total_amount": 80,
                "counterparty_name": "种子供应商",
            },
        )
        assert resp.status_code == 200, resp.text

        before = _count_objects(shop)

        resp = client.post(
            "/seller/sales-out",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 99, "unit": "件",
                "total_amount": 999,
                "counterparty_name": "不可能买家",
            },
        )
        assert resp.status_code == 409, (
            f"Expected 409, got {resp.status_code}: {resp.text}"
        )

        after = _count_objects(shop)
        assert after == before, (
            f"Transaction/movement count changed: {before} -> {after}"
        )


# ============================================================================
# Test 7: Inventory movement traceability without DB IDs
# ============================================================================

class TestInventoryMovementTraceable:
    """GET /seller/inventory-movements returns business fields, no DB PKs."""

    def test_inventory_movement_is_traceable_without_db_ids(self):
        """Purchase-in + sales-out rows visible, no numeric PKs."""
        shop = _create_shop("t01")

        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 50, "unit": "件",
                "total_amount": 400,
                "counterparty_name": "批发商",
            },
        )
        assert resp.status_code == 200, resp.text
        in_mv_uid = resp.json()["movement_uid"]

        resp = client.post(
            "/seller/sales-out",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 10, "unit": "件",
                "total_amount": 150,
                "counterparty_name": "零售买家",
            },
        )
        assert resp.status_code == 200, resp.text
        out_mv_uid = resp.json()["movement_uid"]

        resp2 = client.get(
            "/seller/inventory-movements",
            headers=_auth_header(shop["token"]),
            params={"product_uid": shop["product_uid"]},
        )
        assert resp2.status_code == 200, resp2.text
        movements = resp2.json()
        assert len(movements) >= 2

        in_mv = [m for m in movements if m.get("movement_uid") == in_mv_uid][0]
        assert in_mv["operation_type"] == "purchase_in"
        assert in_mv["quantity_delta"] == 50
        assert in_mv["new_quantity"] == 50
        assert in_mv["total_amount"] == 400
        assert in_mv["counterparty_name"] == "批发商"

        out_mv = [m for m in movements if m.get("movement_uid") == out_mv_uid][0]
        assert out_mv["operation_type"] == "sales_out"
        assert out_mv["quantity_delta"] == -10
        assert out_mv["new_quantity"] == 40
        assert out_mv["total_amount"] == 150
        assert out_mv["counterparty_name"] == "零售买家"

        for mv in movements:
            for pk_field in _DB_ID_FIELDS:
                assert pk_field not in mv, (
                    f"Movement response leaks DB PK '{pk_field}'"
                )


# ============================================================================
# Test 8: No DB PK leakage in any seller API response AND
#          requests with DB PK fields are rejected
# ============================================================================

class TestNoDbIdLeakage:
    """Seller API: response has no DB PKs, request rejects DB PK fields."""

    def _check_no_db_ids(self, data, context: str):
        if isinstance(data, dict):
            for key in data:
                if key in _DB_ID_FIELDS:
                    pytest.fail(f"{context}: response contains DB PK field '{key}'")
                self._check_no_db_ids(data[key], f"{context}.{key}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._check_no_db_ids(item, f"{context}[{i}]")

    def test_seller_api_response_does_not_leak_db_ids(self):
        """Purchase-in, sales-out, stock, movements — all free of DB PKs."""
        shop = _create_shop("l01")

        resp = client.post(
            "/seller/purchase-in",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 15, "unit": "件",
                "total_amount": 120,
                "counterparty_name": "供应商",
            },
        )
        assert resp.status_code == 200, resp.text
        self._check_no_db_ids(resp.json(), "purchase_in")

        resp = client.post(
            "/seller/sales-out",
            headers=_auth_header(shop["token"]),
            json={
                "product_uid": shop["product_uid"],
                "warehouse_code": shop["warehouse_code"],
                "location_path": shop["base_location"],
                "quantity": 3, "unit": "件",
                "total_amount": 45,
                "counterparty_name": "买家",
            },
        )
        assert resp.status_code == 200, resp.text
        self._check_no_db_ids(resp.json(), "sales_out")

        resp = client.get(
            "/seller/stock",
            headers=_auth_header(shop["token"]),
            params={"product_uid": shop["product_uid"]},
        )
        assert resp.status_code == 200, resp.text
        self._check_no_db_ids(resp.json(), "stock")

        resp = client.get(
            "/seller/inventory-movements",
            headers=_auth_header(shop["token"]),
            params={"product_uid": shop["product_uid"]},
        )
        assert resp.status_code == 200, resp.text
        self._check_no_db_ids(resp.json(), "movements")

    def test_seller_api_rejects_request_with_db_id_fields(self):
        """POST to seller endpoints with resource_id/warehouse_id etc → 400/422."""
        shop = _create_shop("l02")
        base_payload = {
            "product_uid": shop["product_uid"],
            "warehouse_code": shop["warehouse_code"],
            "location_path": shop["base_location"],
            "quantity": 5, "unit": "件",
            "total_amount": 40,
            "counterparty_name": "测试拒绝DBID",
        }

        db_id_fields = ["resource_id", "warehouse_id",
                        "organization_id", "person_id"]

        for db_field in db_id_fields:
            payload = dict(base_payload)
            payload[db_field] = 1
            for endpoint in ("/seller/purchase-in", "/seller/sales-out"):
                resp = client.post(
                    endpoint,
                    headers=_auth_header(shop["token"]),
                    json=payload,
                )
                assert resp.status_code in (400, 422), (
                    f"{endpoint} with {db_field}: expected 400/422, "
                    f"got {resp.status_code}: {resp.text}"
                )

        # Verify no side effects — stock, tx, mv unchanged
        after = _count_objects(shop)
        assert after["transactions"] == 0, (
            f"Rejected requests created spurious transactions: {after}"
        )
        assert after["movements"] == 0, (
            f"Rejected requests created spurious movements: {after}"
        )

        stock_resp = client.get(
            "/seller/stock",
            headers=_auth_header(shop["token"]),
            params={"product_uid": shop["product_uid"]},
        )
        assert stock_resp.status_code == 200, stock_resp.text
        assert len(stock_resp.json()) == 0, (
            "Rejected requests created spurious stock rows"
        )


# ============================================================================
# Test 9: Transaction rollback on failure — DB-level proof
# ============================================================================

class TestRollbackOnFailure:
    """When inventory_movement INSERT fails, stock + transaction + movement
    all roll back atomically.  Uses a BEFORE INSERT trigger to inject failure
    at the latest possible stage — after stock UPDATE and transaction INSERT.
    RED phase: execute_purchase_in() missing → ImportError (correct)."""

    def test_purchase_in_rolls_back_when_movement_insert_fails(self):
        """GIVEN valid product/warehouse WHEN movement insert fails (trigger)
        THEN stock, transaction, movement all unchanged.
        RED phase: ImportError because execute_purchase_in() does not exist.
        GREEN phase: trigger fires mid-transaction, everything rolls back."""
        shop = _create_shop("r01")

        from src.db.database import (
            execute_purchase_in, query_organization_by_ouid,
            query_person_by_puid, _fetch, get_db_connection,
        )

        org_id = query_organization_by_ouid(shop["ouid"])[0]["id"]
        person_id = query_person_by_puid(shop["puid"])[0]["id"]

        # Resolve resource + warehouse to DB IDs for pre-state capture
        resources = _fetch(
            "SELECT id FROM resource WHERE organization_id = %s AND name = %s",
            (org_id, shop["product_uid"]),
        )
        resource_id = resources[0]["id"]

        pre_rw = _fetch(
            "SELECT id, quantity FROM resource_warehouse "
            "WHERE resource_id = %s AND location_path = %s",
            (resource_id, shop["base_location"]),
        )
        pre_qty = float(pre_rw[0]["quantity"]) if pre_rw else None
        pre_tx = len(_fetch(
            "SELECT id FROM transaction WHERE organization_id = %s", (org_id,),
        ))
        pre_mv = 0
        try:
            pre_mv = len(_fetch(
                "SELECT id FROM inventory_movement WHERE organization_id = %s",
                (org_id,),
            ))
        except Exception:
            pass

        # Install a trigger that rejects INSERT into inventory_movement
        conn = get_db_connection()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("""
            CREATE OR REPLACE FUNCTION reject_movement_for_test()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'injected rollback test failure';
            END;
            $$ LANGUAGE plpgsql
        """)
        cur.execute("""
            DROP TRIGGER IF EXISTS trg_reject_movement ON inventory_movement
        """)
        cur.execute("""
            CREATE TRIGGER trg_reject_movement
            BEFORE INSERT ON inventory_movement
            FOR EACH ROW EXECUTE FUNCTION reject_movement_for_test()
        """)
        conn.close()

        try:
            with pytest.raises(Exception, match="injected rollback test failure"):
                execute_purchase_in(
                    organization_id=org_id,
                    operator_person_id=person_id,
                    product_uid=shop["product_uid"],
                    warehouse_code=shop["warehouse_code"],
                    location_path=shop["base_location"],
                    quantity=10, unit="件",
                    total_amount=100,
                    counterparty_name="rollback_test",
                )

            # Assert all three unchanged
            post_rw = _fetch(
                "SELECT id, quantity FROM resource_warehouse "
                "WHERE resource_id = %s AND location_path = %s",
                (resource_id, shop["base_location"]),
            )

            if pre_qty is None:
                assert len(post_rw) == 0, (
                    "Stock row was created despite rollback"
                )
            else:
                post_qty = float(post_rw[0]["quantity"])
                assert abs(post_qty - pre_qty) < 0.001, (
                    f"Stock leaked: pre={pre_qty} post={post_qty}"
                )

            post_tx = len(_fetch(
                "SELECT id FROM transaction WHERE organization_id = %s",
                (org_id,),
            ))
            assert post_tx == pre_tx, (
                f"Transaction leaked: pre={pre_tx} post={post_tx}"
            )

            post_mv = 0
            try:
                post_mv = len(_fetch(
                    "SELECT id FROM inventory_movement WHERE organization_id = %s",
                    (org_id,),
                ))
                assert post_mv == pre_mv, (
                    f"Movement leaked: pre={pre_mv} post={post_mv}"
                )
            except Exception:
                pass
        finally:
            conn2 = get_db_connection()
            conn2.autocommit = True
            c2 = conn2.cursor()
            c2.execute(
                "DROP TRIGGER IF EXISTS trg_reject_movement ON inventory_movement"
            )
            c2.execute("DROP FUNCTION IF EXISTS reject_movement_for_test()")
            conn2.close()


# ============================================================================
# Test 10: Three Kingdoms HTTP regression
# ============================================================================

class TestThreeKingdomsRegression:
    """Three Kingdoms campaign data must remain unaffected."""

    def test_three_kingdoms_http_regression(self):
        """Public ouid context still works for shu."""
        resp = client.get("/organizations/shu/members")
        assert resp.status_code == 200, resp.text

        resp = client.get("/resource?ouid=shu")
        assert resp.status_code == 200, resp.text
        resources = resp.json()
        assert len(resources) >= 1

        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
