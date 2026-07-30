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
