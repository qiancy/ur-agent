"""
AUTH-02 TDD: 单账号多空间认证与注册。

契约要点：
- account.login 是唯一登录凭据，不再解析为 puid/ouid 上下文。
- 注册创建 account + person；可选 initial_ouid 加入组织（role=member）。
- 登录按 account.login 认证，返回默认空间 JWT + 可切换 organizations。
- 无 membership 时返回 requires_organization=true，不签发组织上下文 JWT。
- 空间切换只走 /auth/switch-organization。
- 认证响应与 JWT 不得含 DB 数字 ID。

黑盒：HTTP TestClient，每次运行用 uuid 隔离。
"""
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


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _make_org(org_type="company") -> str:
    s = _uid()
    ouid = f"auth02_{org_type}_{s}"
    resp = client.post("/organizations", json={
        "name": f"AUTH02_{org_type}_{s}", "org_type": org_type, "ouid": ouid,
    })
    assert resp.status_code in (200, 201), resp.text
    return ouid


def _register(login, password="pass123", name=None, puid=None,
              initial_ouid=None):
    body = {"login": login, "password": password, "name": name or login}
    if puid is not None:
        body["puid"] = puid
    if initial_ouid is not None:
        body["initial_ouid"] = initial_ouid
    return client.post("/auth/register", json=body)


def _add_membership(puid: str, ouid: str, role="member"):
    resp = client.post("/organizations/members", json={
        "puid": puid, "ouid": ouid, "role": role,
    })
    assert resp.status_code == 201, resp.text


def _login(login, password="pass123"):
    return client.post("/auth/login", json={"login": login, "password": password})


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. 单账号注册成功（account + person）
# ============================================================================
def test_register_single_account_success():
    u = _uid()
    ouid = _make_org("ecommerce")
    resp = _register(f"zhansan_{u}", name="张三", puid=f"zhansan_{u}",
                     initial_ouid=ouid)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["person"]["puid"] == f"zhansan_{u}"
    assert data["person"]["name"] == "张三"
    assert data["account"]["login"] == f"zhansan_{u}"
    assert data["account"]["system_role"] == "user"
    assert data["organization"]["ouid"] == ouid
    assert data["membership"]["role"] == "member"
    assert data["requires_organization"] is False
    assert data["access_token"]
    _assert_no_db_ids(data)


# ============================================================================
# 2. 注册不带 initial_ouid → requires_organization=true
# ============================================================================
def test_register_without_space_requires_org():
    u = _uid()
    login = f"newuser_{u}"
    resp = _register(login, name="新用户", puid=login)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["requires_organization"] is True
    assert data["access_token"] is None
    assert data["organizations"] == []
    _assert_no_db_ids(data)

    # 登录同样返回 requires_organization=true
    resp = _login(login)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["requires_organization"] is True
    assert data["access_token"] is None
    assert data["organizations"] == []


# ============================================================================
# 3. 非法 puid → 422；login 不能作为 puid 时要求显式 puid
# ============================================================================
@pytest.mark.parametrize("bad_puid", ["张三", "zhansan@shop", "zhang san"])
def test_register_rejects_invalid_puid(bad_puid):
    u = _uid()
    resp = _register(f"puidbad_{u}", puid=bad_puid)
    assert resp.status_code == 422, resp.text


def test_register_requires_explicit_puid_when_login_unsafe():
    u = _uid()
    # login contains '@' -> not derivable as puid -> 422
    resp = _register(f"email_{u}@example.com")
    assert resp.status_code == 422, resp.text


# ============================================================================
# 4. 重复 login → 409
# ============================================================================
def test_register_rejects_duplicate_login():
    u = _uid()
    login = f"dup_{u}"
    assert _register(login, puid=login).status_code == 201
    resp = _register(login, puid=f"{login}_x")
    assert resp.status_code == 409, resp.text


def test_register_rejects_puid_taken_by_other_login():
    u = _uid()
    puid = f"shared_{u}"
    assert _register(f"a_{u}", puid=puid).status_code == 201
    resp = _register(f"b_{u}", puid=puid)
    assert resp.status_code == 409, resp.text


# ============================================================================
# 5. 登录单账号返回默认空间和 organizations
# ============================================================================
def test_login_single_account_returns_spaces():
    u = _uid()
    ouid_a = _make_org("ecommerce")
    ouid_b = _make_org("family")
    login = f"multi_{u}"
    assert _register(login, puid=login, initial_ouid=ouid_a).status_code == 201
    _add_membership(login, ouid_b)

    resp = _login(login)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"]
    assert data["requires_organization"] is False
    org_ouids = {o["ouid"] for o in data["organizations"]}
    assert ouid_a in org_ouids
    assert ouid_b in org_ouids
    assert data["organization"]["ouid"] == ouid_a  # stable default (first)
    _assert_no_db_ids(data)


# ============================================================================
# 6. 旧形式 zhansan@fire_xinye_shu 不会被解析成组织上下文
# ============================================================================
def test_login_does_not_parse_ouid_from_login():
    u = _uid()
    ouid = _make_org("ecommerce")
    login = f"zhansan_{u}"
    assert _register(login, puid=login, initial_ouid=ouid).status_code == 201

    # 旧格式 login@ouid 不被当作组织切换；按字面查 account → 401
    resp = _login(f"{login}@{ouid}")
    assert resp.status_code == 401, resp.text

    # 正确单账号登录不受影响
    assert _login(login).status_code == 200


def test_login_wrong_password_401():
    u = _uid()
    login = f"wrongpw_{u}"
    assert _register(login, puid=login, initial_ouid=_make_org()).status_code == 201
    assert _login(login, password="nope").status_code == 401


# ============================================================================
# 7. 切换非 membership 组织返回 403
# ============================================================================
def test_switch_organization_requires_membership():
    u = _uid()
    ouid_a = _make_org("company")
    ouid_b = _make_org("company")
    login = f"switch_{u}"
    assert _register(login, puid=login, initial_ouid=ouid_a).status_code == 201
    token = _login(login).json()["access_token"]

    resp = client.post("/auth/switch-organization",
                       headers=_auth(token), json={"ouid": ouid_b})
    assert resp.status_code == 403, resp.text


def test_switch_organization_unknown_org_404():
    u = _uid()
    login = f"sw4_{u}"
    assert _register(login, puid=login, initial_ouid=_make_org()).status_code == 201
    token = _login(login).json()["access_token"]
    resp = client.post("/auth/switch-organization",
                       headers=_auth(token), json={"ouid": "no_such_org"})
    assert resp.status_code == 404, resp.text


def test_switch_organization_success_issues_new_token():
    u = _uid()
    ouid_a = _make_org("ecommerce")
    ouid_b = _make_org("ecommerce")
    login = f"dave_{u}"
    assert _register(login, puid=login, initial_ouid=ouid_a).status_code == 201
    _add_membership(login, ouid_b)
    token_a = _login(login).json()["access_token"]

    resp = client.post("/auth/switch-organization",
                       headers=_auth(token_a), json={"ouid": ouid_b})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"]
    assert data["organization"]["ouid"] == ouid_b
    assert data["person"]["puid"] == login
    assert data["requires_organization"] is False
    _assert_no_db_ids(data)


def test_switch_organization_requires_jwt():
    resp = client.post("/auth/switch-organization", json={"ouid": "x"})
    assert resp.status_code == 401


# ============================================================================
# 8. 认证响应和 JWT 无 DB 数字 ID；请求拒绝 DB id 字段
# ============================================================================
def test_auth_responses_have_no_db_ids():
    u = _uid()
    ouid = _make_org("ecommerce")
    login = f"clean_{u}"
    reg = _register(login, puid=login, initial_ouid=ouid)
    assert reg.status_code == 201
    _assert_no_db_ids(reg.json())

    log = _login(login)
    assert log.status_code == 200
    _assert_no_db_ids(log.json())

    token = log.json()["access_token"]
    me = client.get("/auth/me/organizations", headers=_auth(token))
    assert me.status_code == 200
    _assert_no_db_ids(me.json())

    sw = client.post("/auth/switch-organization", headers=_auth(token),
                     json={"ouid": ouid})
    assert sw.status_code == 200
    _assert_no_db_ids(sw.json())


@pytest.mark.parametrize("forbidden", [
    "id", "pid", "oid", "person_id", "organization_id", "membership_id",
])
def test_switch_organization_rejects_db_id_fields(forbidden):
    u = _uid()
    login = f"forbid_{u}"
    ouid = _make_org()
    assert _register(login, puid=login, initial_ouid=ouid).status_code == 201
    token = _login(login).json()["access_token"]
    resp = client.post("/auth/switch-organization", headers=_auth(token),
                       json={"ouid": ouid, forbidden: "x"})
    assert resp.status_code == 422, resp.text


# ============================================================================
# 前端依赖：/auth/seller-login 与 /auth/login 同一认证契约
# ============================================================================
def test_seller_login_shares_single_account_auth():
    u = _uid()
    ouid = _make_org("ecommerce")
    login = f"seller_{u}"
    assert _register(login, puid=login, initial_ouid=ouid).status_code == 201
    resp = client.post("/auth/seller-login", json={"login": login, "password": "pass123"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["organization"]["ouid"] == ouid
    assert data["requires_organization"] is False
    assert "organizations" in data
    _assert_no_db_ids(data)
