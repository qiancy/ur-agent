"""
BE-09 TDD: Seller Products API.

RED phase — these tests target `/seller/products` which is not yet implemented.
Black-box via HTTP TestClient; unique puid/ouid per run for DB isolation.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

_SUFFIX = uuid.uuid4().hex[:8]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def shop():
    s = _SUFFIX
    data = {}
    ouid = f"be09_shop_{s}"
    resp = client.post("/organizations", json={
        "name": f"BE09店铺_{s}", "org_type": "ecommerce", "ouid": ouid,
    })
    assert resp.status_code == 201, resp.text
    data["ouid"] = ouid

    login = f"seller_{s}@{ouid}"
    resp = client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": f"店主_{s}",
    })
    assert resp.status_code == 201, resp.text

    resp = client.post("/auth/seller-login", json={
        "login": login, "password": "pass123",
    })
    assert resp.status_code == 200, resp.text
    data["token"] = resp.json()["access_token"]
    return data


def _products(token: str):
    return client.get("/seller/products", headers=_auth_header(token))


def test_products_empty_list(shop):
    resp = _products(shop["token"])
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_create_product_returns_list_item(shop):
    resp = client.post("/seller/products", headers=_auth_header(shop["token"]),
                       json={"product_uid": "SKU-A01", "unit": "个", "description": "水杯"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["product_uid"] == "SKU-A01"
    assert body["unit"] == "个"
    assert body["status"] == "active"
    assert body["stock_total"] == 0
    assert body["stock_location_count"] == 0
    assert body["description"] == "水杯"
    assert "name" not in body


def test_products_list_after_create(shop):
    resp = _products(shop["token"])
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert any(x["product_uid"] == "SKU-A01" for x in items)


def test_create_duplicate_409(shop):
    resp = client.post("/seller/products", headers=_auth_header(shop["token"]),
                       json={"product_uid": "SKU-A01", "unit": "个"})
    assert resp.status_code == 409, resp.text


def test_create_missing_unit_422(shop):
    resp = client.post("/seller/products", headers=_auth_header(shop["token"]),
                       json={"product_uid": "SKU-B01"})
    assert resp.status_code == 422, resp.text


def test_create_extra_field_forbidden(shop):
    resp = client.post("/seller/products", headers=_auth_header(shop["token"]),
                       json={"product_uid": "SKU-C01", "unit": "个", "name": "X"})
    assert resp.status_code == 422, resp.text


def test_patch_inactive(shop):
    resp = client.patch("/seller/products/SKU-A01",
                        headers=_auth_header(shop["token"]),
                        json={"status": "inactive"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["product_uid"] == "SKU-A01"
    assert body["status"] == "inactive"
    assert "name" not in body


def test_patch_unknown_404(shop):
    resp = client.patch("/seller/products/NOPE",
                        headers=_auth_header(shop["token"]),
                        json={"status": "inactive"})
    assert resp.status_code == 404, resp.text


def test_products_isolated_between_shops():
    s = uuid.uuid4().hex[:8]
    ouid = f"be09_shop_b_{s}"
    assert client.post("/organizations", json={
        "name": f"BE09店铺B_{s}", "org_type": "ecommerce", "ouid": ouid,
    }).status_code == 201
    login = f"seller_b_{s}@{ouid}"
    assert client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": f"店主B_{s}",
    }).status_code == 201
    resp = client.post("/auth/seller-login", json={"login": login, "password": "pass123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    r2 = _products(token)
    assert r2.status_code == 200, r2.text
    assert all(x["product_uid"] != "SKU-A01" for x in r2.json())


def test_products_reject_identity_query_params(shop):
    resp = client.get("/seller/products?ouid=x", headers=_auth_header(shop["token"]))
    assert resp.status_code == 400, resp.text
    resp = client.get("/seller/products?organization_id=1", headers=_auth_header(shop["token"]))
    assert resp.status_code == 400, resp.text


def test_products_requires_ecommerce():
    s = _SUFFIX
    ouid = f"be09_org_{s}"
    resp = client.post("/organizations", json={
        "name": f"BE09非电商_{s}", "org_type": "family", "ouid": ouid,
    })
    assert resp.status_code == 201, resp.text
    login = f"fam_{s}@{ouid}"
    assert client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": f"家人_{s}",
    }).status_code == 201
    resp = client.post("/auth/seller-login", json={"login": login, "password": "pass123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    resp = client.get("/seller/products", headers=_auth_header(token))
    assert resp.status_code == 403, resp.text


def test_products_no_db_ids_in_response(shop):
    resp = _products(shop["token"])
    assert resp.status_code == 200
    text = resp.text
    assert '"id"' not in text
    assert 'organization_id' not in text
    assert 'person_id' not in text
