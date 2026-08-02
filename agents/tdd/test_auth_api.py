"""
Test authentication API endpoints.

Tests:
- test_register_success
- test_register_invalid_login_format
- test_register_unknown_org
- test_login_success
- test_login_wrong_password
- test_login_wrong_org_membership
- test_login_unknown_org
"""
import sys
import os
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

BASE_URL = "http://localhost:8000"


def test_register_success():
    """Test successful registration."""
    print("\n" + "=" * 60)
    print("TEST: Register success")
    print("=" * 60)
    
    # First, ensure organization exists
    try:
        resp = requests.get(f"{BASE_URL}/organizations", timeout=5)
        orgs = resp.json()
        if not orgs:
            print("  ✗ No organizations found")
            return False
        org_ouid = orgs[0].get("ouid")
        if not org_ouid:
            print("  ✗ Organization has no ouid field")
            return False
    except Exception as e:
        print(f"  ✗ Failed to get organizations: {e}")
        return False
    
    # Register new user
    login = f"testuser@{org_ouid}.cn"
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "login": login,
                "password": "test123",
                "name": "测试用户",
                "role": "member"
            },
            timeout=10
        )
        if resp.status_code == 201:
            data = resp.json()
            if data.get("person", {}).get("puid") == "testuser":
                print(f"  ✓ Registration successful: {data}")
                return True
            else:
                print(f"  ✗ Invalid response: {data}")
                return False
        else:
            print(f"  ✗ Registration failed: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"  ✗ Registration error: {e}")
        return False


def test_register_invalid_login_format():
    """Test registration with invalid login format."""
    print("\n" + "=" * 60)
    print("TEST: Register invalid login format")
    print("=" * 60)
    
    invalid_logins = [
        "invalid",           # No @
        "user@org",          # No .cn
        "user@org.com",      # Wrong TLD
        "user.name@org.cn",  # Invalid puid (contains dot)
    ]
    
    for login in invalid_logins:
        try:
            resp = requests.post(
                f"{BASE_URL}/auth/register",
                json={
                    "login": login,
                    "password": "test123",
                    "name": "测试用户",
                    "role": "member"
                },
                timeout=10
            )
            if resp.status_code == 400:
                print(f"  ✓ Correctly rejected: {login}")
            else:
                print(f"  ✗ Should have rejected: {login}, got {resp.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ Error testing {login}: {e}")
            return False
    
    print("  ✓ All invalid formats rejected")
    return True


def test_register_unknown_org():
    """Test registration with unknown organization."""
    print("\n" + "=" * 60)
    print("TEST: Register unknown org")
    print("=" * 60)
    
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "login": "user@nonexistent.cn",
                "password": "test123",
                "name": "测试用户",
                "role": "member"
            },
            timeout=10
        )
        if resp.status_code == 404:
            print("  ✓ Correctly rejected unknown org")
            return True
        else:
            print(f"  ✗ Should have returned 404, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_login_success():
    """Test successful login."""
    print("\n" + "=" * 60)
    print("TEST: Login success")
    print("=" * 60)
    
    # First, register a user
    try:
        resp = requests.get(f"{BASE_URL}/organizations", timeout=5)
        orgs = resp.json()
        if not orgs:
            print("  ✗ No organizations found")
            return False
        org_ouid = orgs[0].get("ouid")
        if not org_ouid:
            print("  ✗ Organization has no ouid field")
            return False
    except Exception as e:
        print(f"  ✗ Failed to get organizations: {e}")
        return False
    
    login = f"testuser@{org_ouid}.cn"
    
    # Register
    requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "login": login,
            "password": "test123",
            "name": "测试用户",
            "role": "member"
        },
        timeout=10
    )
    
    # Login
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "login": login,
                "password": "test123"
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("access_token") and data.get("organization", {}).get("ouid") == org_ouid:
                print(f"  ✓ Login successful")
                return True
            else:
                print(f"  ✗ Invalid response: {data}")
                return False
        else:
            print(f"  ✗ Login failed: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"  ✗ Login error: {e}")
        return False


def test_login_wrong_password():
    """Test login with wrong password."""
    print("\n" + "=" * 60)
    print("TEST: Login wrong password")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{BASE_URL}/organizations", timeout=5)
        orgs = resp.json()
        if not orgs:
            print("  ✗ No organizations found")
            return False
        org_ouid = orgs[0].get("ouid")
    except:
        print("  ✗ Cannot get orgs")
        return False
    
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "login": f"testuser@{org_ouid}.cn",
                "password": "wrongpassword"
            },
            timeout=10
        )
        if resp.status_code == 401:
            print("  ✓ Correctly rejected wrong password")
            return True
        else:
            print(f"  ✗ Should have returned 401, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_login_wrong_org_membership():
    """Test login when user is not a member of the organization."""
    import time
    print("\n" + "=" * 60)
    print("TEST: Login wrong org membership")
    print("=" * 60)
    
    # Create a new organization with unique ouid
    unique_suffix = str(int(time.time()))[-6:]
    test_ouid = f"torg{unique_suffix}"
    
    try:
        resp = requests.post(
            f"{BASE_URL}/organizations",
            json={
                "name": "测试组织",
                "org_type": "company",
                "ouid": test_ouid
            },
            timeout=10
        )
        if resp.status_code != 201:
            print(f"  ✗ Failed to create org: {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error creating org: {e}")
        return False
    
    # Register user in the new org
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "login": f"member@{test_ouid}.cn",
                "password": "test123",
                "name": "组织成员",
                "role": "member"
            },
            timeout=10
        )
        if resp.status_code != 201:
            print(f"  ✗ Failed to register user: {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error registering user: {e}")
        return False
    
    # Try to login to a different org
    try:
        resp = requests.get(f"{BASE_URL}/organizations", timeout=5)
        orgs = resp.json()
        other_org = [o for o in orgs if o.get("ouid") != test_ouid]
        if not other_org:
            print("  ✗ No other orgs to test")
            return False
        other_ouid = other_org[0].get("ouid")
    except:
        print("  ✗ Cannot get orgs")
        return False
    
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "login": f"member@{other_ouid}.cn",
                "password": "test123"
            },
            timeout=10
        )
        if resp.status_code == 401:
            print("  ✓ Correctly rejected wrong org membership")
            return True
        else:
            print(f"  ✗ Should have returned 401, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_login_unknown_org():
    """Test login with unknown organization."""
    print("\n" + "=" * 60)
    print("TEST: Login unknown org")
    print("=" * 60)
    
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "login": "user@nonexistent.cn",
                "password": "test123"
            },
            timeout=10
        )
        if resp.status_code == 401:
            print("  ✓ Correctly rejected unknown org")
            return True
        else:
            print(f"  ✗ Should have returned 401, got {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("AUTHENTICATION API TESTS")
    print("=" * 60)
    
    # Check if server is running
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code != 200:
            print("ERROR: Server not responding!")
            return 1
    except requests.RequestException as e:
        print(f"ERROR: Cannot connect to server: {e}")
        return 1
    
    results = []
    results.append(("Register success", test_register_success()))
    results.append(("Register invalid format", test_register_invalid_login_format()))
    results.append(("Register unknown org", test_register_unknown_org()))
    results.append(("Login success", test_login_success()))
    results.append(("Login wrong password", test_login_wrong_password()))
    results.append(("Login wrong org membership", test_login_wrong_org_membership()))
    results.append(("Login unknown org", test_login_unknown_org()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, p in results if p)
    failed = len(results) - passed
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())


# ============================================================================
# FE-08 TDD (RED): GET /auth/me/organizations + POST /auth/switch-organization
# ============================================================================
import uuid

import pytest
from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)

_AUTH_FORBIDDEN_FIELDS = {
    "id", "pid", "oid", "person_id", "organization_id", "membership_id",
}


def _assert_no_db_ids(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in _AUTH_FORBIDDEN_FIELDS, f"leaked db id field: {k}"
            assert not k.endswith("_id"), f"leaked db id field: {k}"
            _assert_no_db_ids(v)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_db_ids(item)


def _make_org(org_type="company"):
    s = uuid.uuid4().hex[:8]
    ouid = f"fe08_{org_type}_{s}"
    resp = client.post("/organizations", json={
        "name": f"FE08_{org_type}_{s}", "org_type": org_type, "ouid": ouid,
    })
    assert resp.status_code in (200, 201), resp.text
    return ouid, resp.json()


def _register(puid, ouid, name=None, password="pass123"):
    login = f"{puid}@{ouid}"
    resp = client.post("/auth/register", json={
        "login": login, "password": password, "name": name or puid,
    })
    assert resp.status_code == 201, resp.text


def _login(puid, ouid, password="pass123"):
    resp = client.post("/auth/login", json={
        "login": f"{puid}@{ouid}", "password": password,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# 1. GET /auth/me/organizations without a JWT returns 401.
def test_me_organizations_requires_jwt():
    resp = client.get("/auth/me/organizations")
    assert resp.status_code == 401


# 2. A user only sees their own organizations.
# 3. Response has no DB numeric ids and no legacy pid/oid.
def test_me_organizations_lists_only_own_orgs_without_db_ids():
    u = uuid.uuid4().hex[:8]
    ouid_a, _ = _make_org("company")
    ouid_b, _ = _make_org("company")
    ouid_c, _ = _make_org("company")

    _register(f"alice_{u}", ouid_a)
    _register(f"alice_{u}", ouid_b)  # same person, second membership
    _register(f"bob_{u}", ouid_c)

    token_b = _login(f"alice_{u}", ouid_b)
    token_c = _login(f"bob_{u}", ouid_c)

    resp = client.get("/auth/me/organizations", headers=_auth(token_b))
    assert resp.status_code == 200, resp.text
    orgs = resp.json()
    ouids = {o["ouid"] for o in orgs}
    assert ouid_a in ouids
    assert ouid_b in ouids
    assert ouid_c not in ouids
    for o in orgs:
        assert set(o.keys()) == {"ouid", "name", "type", "role"}
    _assert_no_db_ids(orgs)

    resp = client.get("/auth/me/organizations", headers=_auth(token_c))
    assert resp.status_code == 200
    orgs_c = resp.json()
    assert [o["ouid"] for o in orgs_c] == [ouid_c]


# GET /auth/me/organizations rejects puid/ouid query parameters.
def test_me_organizations_rejects_puid_ouid_query_params():
    u = uuid.uuid4().hex[:8]
    ouid, _ = _make_org("company")
    _register(f"carol_{u}", ouid)
    token = _login(f"carol_{u}", ouid)
    for param in ("puid", "ouid"):
        resp = client.get(
            f"/auth/me/organizations?{param}=whatever",
            headers=_auth(token),
        )
        assert resp.status_code == 400, resp.text


# 4. Switch to a member organization issues a new token + target context.
def test_switch_organization_success_issues_new_token():
    u = uuid.uuid4().hex[:8]
    ouid_a, _ = _make_org("company")
    ouid_b, _ = _make_org("ecommerce")
    _register(f"dave_{u}", ouid_a)
    _register(f"dave_{u}", ouid_b)

    token_a = _login(f"dave_{u}", ouid_a)

    resp = client.post(
        "/auth/switch-organization",
        headers=_auth(token_a),
        json={"ouid": ouid_b},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"]
    assert data["organization"]["ouid"] == ouid_b
    assert data["organization"]["type"] == "ecommerce"
    assert data["person"]["puid"] == f"dave_{u}"
    assert data["membership"]["role"]
    _assert_no_db_ids(data)

    # The new token keeps the same person but re-scopes to the target org.
    resp = client.get(
        "/auth/me/organizations",
        headers=_auth(data["access_token"]),
    )
    assert resp.status_code == 200
    ouids = {o["ouid"] for o in resp.json()}
    assert ouid_a in ouids and ouid_b in ouids


# 5. Switch to a non-member organization returns 403.
def test_switch_organization_non_member_403():
    u = uuid.uuid4().hex[:8]
    ouid_a, _ = _make_org("company")
    ouid_b, _ = _make_org("company")
    _register(f"frank_{u}", ouid_b)  # frank is only in ouid_b

    token_b = _login(f"frank_{u}", ouid_b)
    resp = client.post(
        "/auth/switch-organization",
        headers=_auth(token_b),
        json={"ouid": ouid_a},
    )
    assert resp.status_code == 403, resp.text


def test_switch_organization_unknown_org_404():
    u = uuid.uuid4().hex[:8]
    ouid, _ = _make_org("company")
    _register(f"grace_{u}", ouid)
    token = _login(f"grace_{u}", ouid)
    resp = client.post(
        "/auth/switch-organization",
        headers=_auth(token),
        json={"ouid": "no_such_org"},
    )
    assert resp.status_code == 404, resp.text


def test_switch_organization_requires_jwt():
    resp = client.post("/auth/switch-organization", json={"ouid": "x"})
    assert resp.status_code == 401


# 6. Request body with DB-id / legacy fields is rejected (422).
@pytest.mark.parametrize("forbidden", [
    "id", "pid", "oid", "person_id", "organization_id", "membership_id",
])
def test_switch_organization_rejects_db_id_fields(forbidden):
    u = uuid.uuid4().hex[:8]
    ouid, _ = _make_org("company")
    _register(f"heidi_{u}", ouid)
    token = _login(f"heidi_{u}", ouid)
    resp = client.post(
        "/auth/switch-organization",
        headers=_auth(token),
        json={"ouid": ouid, forbidden: "x"},
    )
    assert resp.status_code == 422, resp.text
