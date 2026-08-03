"""
BE-10 TDD: Spaces observation API (`/spaces/current/*`).

RED phase — endpoints not yet implemented. Strict JWT only; no ouid/puid query params.
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
def family_ctx():
    s = _SUFFIX
    data = {}
    ouid = f"be10_family_{s}"
    resp = client.post("/organizations", json={
        "name": f"BE10家庭_{s}", "org_type": "family", "ouid": ouid, "funds": 5000,
    })
    assert resp.status_code == 201, resp.text
    data["ouid"] = ouid

    login = f"fam_{s}"
    resp = client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": f"家长_{s}",
        "initial_ouid": ouid,
    })
    assert resp.status_code == 201, resp.text

    resp = client.post("/auth/seller-login", json={"login": login, "password": "pass123"})
    assert resp.status_code == 200, resp.text
    data["token"] = resp.json()["access_token"]
    return data


def test_overview_shape(family_ctx):
    resp = client.get("/spaces/current/overview", headers=_auth_header(family_ctx["token"]))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["space"]["ouid"] == family_ctx["ouid"]
    assert body["space"]["type"] == "family"
    assert body["space"]["role"] in ("owner", "member")
    assert set(body["counts"]) == {"resources", "persons", "transactions", "recent_events"}
    assert "funds" in body
    assert "id" not in body["space"]
    assert "organization_id" not in body["space"]


def test_resources_grouped(family_ctx):
    resp = client.get("/spaces/current/resources", headers=_auth_header(family_ctx["token"]))
    assert resp.status_code == 200, resp.text
    grouped = resp.json()["grouped"]
    assert set(grouped) == {"physical", "knowledge", "financial", "human"}
    text = resp.text
    assert '"id"' not in text
    assert 'person_id' not in text
    assert 'embedding' not in text


def test_resources_physical_locations(family_ctx):
    s = _SUFFIX
    # seed a physical resource with stock via warehouse + resource_warehouse
    login = f"fam2_{s}"
    assert client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": f"家长2_{s}",
        "initial_ouid": family_ctx["ouid"],
    }).status_code == 201
    resp = client.post("/auth/seller-login", json={"login": login, "password": "pass123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    org = client.get("/spaces/current/overview", headers=_auth_header(token)).json()["space"]
    # create resource via /resource (needs bearer + org context)
    resp = client.post("/resource", headers=_auth_header(token),
                       json={"name": f"教材_{s}", "resource_type": "physical", "unit": "本", "amount": 3})
    assert resp.status_code in (200, 201), resp.text


def test_persons_shape(family_ctx):
    resp = client.get("/spaces/current/persons", headers=_auth_header(family_ctx["token"]))
    assert resp.status_code == 200, resp.text
    arr = resp.json()
    assert isinstance(arr, list)
    assert any("puid" in x and "role" in x for x in arr)


def test_transactions_shape(family_ctx):
    resp = client.get("/spaces/current/transactions", headers=_auth_header(family_ctx["token"]))
    assert resp.status_code == 200, resp.text
    arr = resp.json()
    assert isinstance(arr, list)
    if arr:
        item = arr[0]
        assert {"transaction_uid", "from_party_name", "to_party_name",
                "amount", "category", "description", "created_at"} <= set(item)
        assert "id" not in item
        assert "organization_id" not in item


def test_timeline_empty_or_events(family_ctx):
    resp = client.get("/spaces/current/timeline", headers=_auth_header(family_ctx["token"]))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "events" in body
    for ev in body["events"]:
        assert "seq" in ev and "title" in ev


def test_timeline_reject_ouid_query_param(family_ctx):
    resp = client.get(f"/spaces/current/timeline?ouid=x", headers=_auth_header(family_ctx["token"]))
    assert resp.status_code in (400, 422), resp.text


def test_spaces_requires_jwt(family_ctx):
    for path in ("/spaces/current/overview", "/spaces/current/resources",
                 "/spaces/current/persons", "/spaces/current/transactions",
                 "/spaces/current/timeline"):
        resp = client.get(path)
        assert resp.status_code == 401, (path, resp.status_code)
