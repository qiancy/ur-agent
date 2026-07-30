"""
BE-01 TDD: Permission isolation for ecommerce organizations.

RED phase — all ecommerce auth tests must FAIL before BE-01 implementation.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


# ============================================================================
# Helper
# ============================================================================

_SUFFIX = uuid.uuid4().hex[:8]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Fixture: create two ecommerce shops with resources + stock
# ============================================================================

@pytest.fixture(scope="module")
def shops():
    s = _SUFFIX
    data = {}

    # ── 店铺A ──
    shop_a_ouid = f"be01_shop_a_{s}"
    resp = client.post("/organizations", json={
        "name": f"BE01店铺A_{s}",
        "org_type": "ecommerce",
        "ouid": shop_a_ouid,
    })
    assert resp.status_code in (200, 201), resp.text
    data["shop_a_ouid"] = shop_a_ouid

    login_a = f"seller_a_{s}@{shop_a_ouid}"
    resp = client.post("/auth/register", json={
        "login": login_a, "password": "pass123", "name": f"小A_{s}",
    })
    assert resp.status_code == 201, resp.text

    resp = client.post("/auth/seller-login", json={
        "login": login_a, "password": "pass123",
    })
    assert resp.status_code == 200
    data["token_a"] = resp.json()["access_token"]

    resp = client.post(
        "/resource",
        headers=_auth_header(data["token_a"]),
        json={"name": f"商品A_{s}", "resource_type": "physical"},
    )
    assert resp.status_code == 201, resp.text
    data["resource_a"] = resp.json()

    resp = client.post(
        f"/resource-warehouse?ouid={shop_a_ouid}",
        headers=_auth_header(data["token_a"]),
        json={"resource_id": data["resource_a"]["id"], "location_path": "A-1",
              "quantity": 100, "unit": "件"},
    )
    assert resp.status_code == 201, resp.text

    # ── 店铺B ──
    shop_b_ouid = f"be01_shop_b_{s}"
    resp = client.post("/organizations", json={
        "name": f"BE01店铺B_{s}",
        "org_type": "ecommerce",
        "ouid": shop_b_ouid,
    })
    assert resp.status_code in (200, 201), resp.text
    data["shop_b_ouid"] = shop_b_ouid

    login_b = f"seller_b_{s}@{shop_b_ouid}"
    resp = client.post("/auth/register", json={
        "login": login_b, "password": "pass123", "name": f"小B_{s}",
    })
    assert resp.status_code == 201, resp.text

    resp = client.post("/auth/seller-login", json={
        "login": login_b, "password": "pass123",
    })
    assert resp.status_code == 200
    data["token_b"] = resp.json()["access_token"]

    resp = client.post(
        "/resource",
        headers=_auth_header(data["token_b"]),
        json={"name": f"商品B_{s}", "resource_type": "physical"},
    )
    assert resp.status_code == 201, resp.text
    data["resource_b"] = resp.json()

    resp = client.post(
        f"/resource-warehouse?ouid={shop_b_ouid}",
        headers=_auth_header(data["token_b"]),
        json={"resource_id": data["resource_b"]["id"], "location_path": "B-1",
              "quantity": 50, "unit": "件"},
    )
    assert resp.status_code == 201, resp.text

    return data


# ============================================================================
# Tests 1-3: Anonymous access to ecommerce warehouse
# ============================================================================

class TestAnonymousEcommerceRejected:
    """Anonymous requests to ecommerce warehouse endpoints must return 401/403."""

    def test_anonymous_cannot_read_ecommerce_stock(self, shops):
        uid = shops["shop_a_ouid"]
        rid = shops["resource_a"]["id"]
        resp = client.get(f"/resource-warehouse?ouid={uid}&resource_id={rid}")
        assert resp.status_code in (401, 403), (
            f"Expected 401/403, got {resp.status_code}: {resp.text}"
        )

    def test_anonymous_cannot_read_ecommerce_total(self, shops):
        uid = shops["shop_a_ouid"]
        rid = shops["resource_a"]["id"]
        resp = client.get(f"/resource-warehouse/total?ouid={uid}&resource_id={rid}")
        assert resp.status_code in (401, 403), (
            f"Expected 401/403, got {resp.status_code}: {resp.text}"
        )

    def test_anonymous_cannot_write_ecommerce_stock(self, shops):
        uid = shops["shop_a_ouid"]
        rid = shops["resource_a"]["id"]
        resp = client.post(
            f"/resource-warehouse?ouid={uid}",
            json={"resource_id": rid, "location_path": "X-9", "quantity": 1, "unit": "件"},
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403, got {resp.status_code}: {resp.text}"
        )


# ============================================================================
# Tests 4-6: Cross-org access with wrong JWT
# ============================================================================

class TestCrossOrgRejected:
    """Shop B token must be rejected (403) when accessing shop A's inventory."""

    def test_other_shop_cannot_read_stock(self, shops):
        rid = shops["resource_a"]["id"]
        resp = client.get(
            f"/resource-warehouse?resource_id={rid}",
            headers=_auth_header(shops["token_b"]),
        )
        assert resp.status_code == 403, (
            f"Expected 403, got {resp.status_code}: {resp.text}"
        )
        body = resp.text.lower()
        assert "quantity" not in body, "Response must not leak inventory data"

    def test_other_shop_cannot_read_total(self, shops):
        rid = shops["resource_a"]["id"]
        resp = client.get(
            f"/resource-warehouse/total?resource_id={rid}",
            headers=_auth_header(shops["token_b"]),
        )
        assert resp.status_code == 403, (
            f"Expected 403, got {resp.status_code}: {resp.text}"
        )
        body = resp.text.lower()
        assert "quantity" not in body, "Response must not leak inventory data"

    def test_other_shop_cannot_write_stock(self, shops):
        rid = shops["resource_a"]["id"]
        resp = client.post(
            f"/resource-warehouse",
            headers=_auth_header(shops["token_b"]),
            json={"resource_id": rid, "location_path": "X-9", "quantity": 1, "unit": "件"},
        )
        assert resp.status_code == 403, (
            f"Expected 403, got {resp.status_code}: {resp.text}"
        )


# ============================================================================
# Tests 7-8: Three Kingdoms public ouid context
# ============================================================================

class TestThreeKingdomsPublicOuidContext:
    """Non-ecommerce orgs must remain unaffected."""

    @pytest.fixture(scope="class")
    def shu_resource(self):
        resp = client.get("/resource?ouid=shu")
        assert resp.status_code == 200, resp.text
        resources = resp.json()
        assert len(resources) > 0, "No resources found for shu"
        return resources[0]

    def test_public_ouid_context_still_works(self, shu_resource):
        rid = shu_resource["id"]
        resp = client.get(f"/resource-warehouse?ouid=shu&resource_id={rid}")
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text}"
        )

    def test_non_ecommerce_jwt_still_works(self):
        s = _SUFFIX
        org_ouid = f"be01_test_org_{s}"
        resp = client.post("/organizations", json={
            "name": f"BE01测试组织_{s}",
            "org_type": "company",
            "ouid": org_ouid,
        })
        assert resp.status_code in (200, 201), resp.text

        login = f"test_user_{s}@{org_ouid}"
        resp = client.post("/auth/register", json={
            "login": login, "password": "pass123", "name": f"测试用户_{s}",
        })
        assert resp.status_code == 201, resp.text

        resp = client.post("/auth/login", json={
            "login": login, "password": "pass123",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        resp = client.post(
            "/resource",
            headers=_auth_header(token),
            json={"name": f"测试资源_{s}", "resource_type": "physical"},
        )
        assert resp.status_code == 201, resp.text
        my_rid = resp.json()["id"]

        resp = client.post(
            f"/resource-warehouse?ouid={org_ouid}",
            headers=_auth_header(token),
            json={"resource_id": my_rid, "location_path": "R1",
                  "quantity": 10, "unit": "个"},
        )
        assert resp.status_code == 201, resp.text

        resp = client.get(
            f"/resource-warehouse?resource_id={my_rid}",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}: {resp.text}"
        )
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["quantity"] == 10
