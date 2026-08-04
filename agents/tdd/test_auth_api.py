"""
AUTH-03 TDD: 默认个人空间与组织治理。

契约要点：
- 注册自动创建 personal 空间（owner），必定返回 personal 空间 JWT。
- initial_ouid 已从契约移除：传入返回 422；注册后不能凭 ouid 加入任意组织。
- 加入组织只走 invite（owner/admin 建 → 受邀人接受）或 join request（提交 → 审批）。
- member 可退出普通组织；personal 不可退出；最后 owner 不可退出/被踢。
- owner/admin 可移除 member/viewer，不能移除最后 owner；owner 转让后原 owner 变 admin。
- 治理响应与 JWT 不得含 DB 数字 ID（invite_uid/request_uid 是业务字段，允许）。

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
    ouid = f"auth03_{org_type}_{s}"
    resp = client.post("/organizations", json={
        "name": f"AUTH03_{org_type}_{s}", "org_type": org_type, "ouid": ouid,
    })
    assert resp.status_code in (200, 201), resp.text
    return ouid


def _register(login, password="pass123", name=None, puid=None):
    body = {"login": login, "password": password, "name": name or login}
    if puid is not None:
        body["puid"] = puid
    return client.post("/auth/register", json=body)


def _register_token(login, password="pass123", name=None, puid=None) -> str:
    resp = _register(login, password=password, name=name, puid=puid)
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    assert token, resp.text
    return token


def _create_space(token, name, org_type, ouid=None) -> dict:
    body = {"name": name, "org_type": org_type}
    if ouid:
        body["ouid"] = ouid
    resp = client.post("/spaces", headers=_auth(token), json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _add_membership(owner_token, puid, ouid, role="member"):
    resp = client.post("/organizations/members", headers=_auth(owner_token),
                       json={"puid": puid, "ouid": ouid, "role": role})
    assert resp.status_code == 201, resp.text


def _login(login, password="pass123"):
    return client.post("/auth/login", json={"login": login, "password": password})


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. 注册自动创建 personal 空间并返回其 JWT
# ============================================================================
def test_register_creates_personal_space():
    u = _uid()
    login = f"reg_{u}"
    resp = _register(login, name="张三", puid=login)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["person"]["puid"] == login
    assert data["person"]["name"] == "张三"
    assert data["account"]["login"] == login
    assert data["account"]["system_role"] == "user"
    assert data["organization"]["ouid"] == f"{login}_personal"
    assert data["organization"]["type"] == "personal"
    assert data["membership"]["role"] == "owner"
    assert data["requires_organization"] is False
    assert data["access_token"]
    assert any(o["ouid"] == f"{login}_personal" for o in data["organizations"])
    _assert_no_db_ids(data)


# ============================================================================
# 2. 登录默认空间即 personal
# ============================================================================
def test_login_default_is_personal_space():
    u = _uid()
    login = f"dflt_{u}"
    _register_token(login, puid=login)
    resp = _login(login)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["organization"]["ouid"] == f"{login}_personal"
    assert data["organization"]["type"] == "personal"
    assert data["requires_organization"] is False
    assert data["access_token"]
    _assert_no_db_ids(data)


# ============================================================================
# 3. initial_ouid 已从契约移除：传入返回 422
# ============================================================================
def test_register_rejects_initial_ouid():
    u = _uid()
    ouid = _make_org()
    resp = client.post("/auth/register", json={
        "login": f"rej_{u}", "password": "pass123", "name": "新人",
        "initial_ouid": ouid,
    })
    assert resp.status_code == 422, resp.text


# ============================================================================
# 4. 注册后仍不能凭 ouid 加入任意组织（invite/join request 之外无入口）
# ============================================================================
def test_registration_cannot_join_arbitrary_org():
    u = _uid()
    ouid = _make_org("company")
    login = f"outsider_{u}"
    _register_token(login, puid=login)
    token = _login(login).json()["access_token"]
    resp = client.post("/auth/switch-organization", headers=_auth(token),
                       json={"ouid": ouid})
    assert resp.status_code == 403, resp.text


# ============================================================================
# 5. 非法 puid → 422；login 不能作为 puid 时要求显式 puid
# ============================================================================
@pytest.mark.parametrize("bad_puid", ["张三", "zhansan@shop", "zhang san"])
def test_register_rejects_invalid_puid(bad_puid):
    u = _uid()
    resp = _register(f"puidbad_{u}", puid=bad_puid)
    assert resp.status_code == 422, resp.text


def test_register_requires_explicit_puid_when_login_unsafe():
    u = _uid()
    resp = _register(f"email_{u}@example.com")
    assert resp.status_code == 422, resp.text


def test_register_rejects_empty_name():
    u = _uid()
    resp = _register(f"noname_{u}", name="   ")
    assert resp.status_code == 422, resp.text


# ============================================================================
# 6. 重复 login / puid → 409
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
# 7. 登录单账号返回 personal + 自建组织
# ============================================================================
def test_login_single_account_returns_spaces():
    u = _uid()
    login = f"multi_{u}"
    token = _register_token(login, puid=login)
    data_a = _create_space(token, f"店A_{u}", "ecommerce", ouid=f"a_{u}")
    data_b = _create_space(token, f"店B_{u}", "ecommerce", ouid=f"b_{u}")

    resp = _login(login)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"]
    assert data["requires_organization"] is False
    org_ouids = {o["ouid"] for o in data["organizations"]}
    assert f"{login}_personal" in org_ouids
    assert data_a["organization"]["ouid"] in org_ouids
    assert data_b["organization"]["ouid"] in org_ouids
    assert data["organization"]["ouid"] == f"{login}_personal"  # personal 默认
    _assert_no_db_ids(data)


# ============================================================================
# 8. 登录认证基础行为
# ============================================================================
def test_login_does_not_parse_ouid_from_login():
    u = _uid()
    login = f"zhansan_{u}"
    _register_token(login, puid=login)

    resp = _login(f"{login}@some_org")
    assert resp.status_code == 401, resp.text

    assert _login(login).status_code == 200


def test_login_wrong_password_401():
    u = _uid()
    login = f"wrongpw_{u}"
    _register_token(login, puid=login)
    assert _login(login, password="nope").status_code == 401


# ============================================================================
# 9. 切换组织
# ============================================================================
def test_switch_organization_requires_membership():
    u = _uid()
    ouid_b = _make_org("company")
    login = f"switch_{u}"
    _register_token(login, puid=login)
    # owner 建 space（ouid_a），login 被加入其中
    data = _create_space(_register_token(f"own_{u}", puid=f"own_{u}"),
                         f"组_{u}", "company", ouid=f"sw_a_{u}")
    ouid_a = data["organization"]["ouid"]
    _add_membership(data["access_token"], login, ouid_a)
    token = _login(login).json()["access_token"]

    resp = client.post("/auth/switch-organization",
                       headers=_auth(token), json={"ouid": ouid_b})
    assert resp.status_code == 403, resp.text


def test_switch_organization_unknown_org_404():
    u = _uid()
    login = f"sw4_{u}"
    token = _register_token(login, puid=login)
    resp = client.post("/auth/switch-organization",
                       headers=_auth(token), json={"ouid": "no_such_org"})
    assert resp.status_code == 404, resp.text


def test_switch_organization_success_issues_new_token():
    u = _uid()
    login = f"dave_{u}"
    token = _register_token(login, puid=login)
    data_a = _create_space(token, f"店A_{u}", "ecommerce", ouid=f"dva_{u}")
    ouid_a = data_a["organization"]["ouid"]
    token_a = data_a["access_token"]  # owner token in org A context

    resp = client.post("/auth/switch-organization",
                       headers=_auth(token_a), json={"ouid": ouid_a})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"]
    assert data["organization"]["ouid"] == ouid_a
    assert data["person"]["puid"] == login
    assert data["requires_organization"] is False
    _assert_no_db_ids(data)


def test_switch_organization_requires_jwt():
    resp = client.post("/auth/switch-organization", json={"ouid": "x"})
    assert resp.status_code == 401


# ============================================================================
# 10. 认证响应和 JWT 无 DB 数字 ID；请求拒绝 DB id 字段
# ============================================================================
def test_auth_responses_have_no_db_ids():
    u = _uid()
    login = f"clean_{u}"
    reg = _register(login, puid=login)
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
                     json={"ouid": f"{login}_personal"})
    assert sw.status_code == 200
    _assert_no_db_ids(sw.json())


@pytest.mark.parametrize("forbidden", [
    "id", "pid", "oid", "person_id", "organization_id", "membership_id",
])
def test_switch_organization_rejects_db_id_fields(forbidden):
    u = _uid()
    login = f"forbid_{u}"
    token = _register_token(login, puid=login)
    resp = client.post("/auth/switch-organization", headers=_auth(token),
                       json={"ouid": f"{login}_personal", forbidden: "x"})
    assert resp.status_code == 422, resp.text


# ============================================================================
# 11. 前端依赖：/auth/seller-login 与 /auth/login 同一认证契约
# ============================================================================
def test_seller_login_shares_single_account_auth():
    u = _uid()
    login = f"seller_{u}"
    token = _register_token(login, puid=login)
    data = _create_space(token, f"店铺_{u}", "ecommerce", ouid=f"shop_{u}")
    ouid = data["organization"]["ouid"]

    resp = client.post("/auth/seller-login", json={"login": login, "password": "pass123"})
    assert resp.status_code == 200, resp.text
    d = resp.json()
    assert d["requires_organization"] is False
    org_ouids = {o["ouid"] for o in d["organizations"]}
    assert ouid in org_ouids
    assert "organizations" in d
    _assert_no_db_ids(d)


# ============================================================================
# 12. 治理流程：invite 加入
# ============================================================================
def test_invite_join_flow():
    u = _uid()
    owner = f"owner_{u}"
    member = f"mem_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"团队{u}", "company", ouid=f"co_{u}")
    ouid = space["organization"]["ouid"]
    org_owner_token = space["access_token"]  # owner JWT in org context
    member_token = _register_token(member, puid=member)

    inv = client.post(f"/spaces/{ouid}/invites", headers=_auth(org_owner_token),
                      json={"invitee_puid": member, "role": "member"})
    assert inv.status_code == 201, inv.text
    invite_uid = inv.json()["invite_uid"]
    _assert_no_db_ids(inv.json())

    acc = client.post("/spaces/invites/accept", headers=_auth(member_token),
                      json={"invite_uid": invite_uid})
    assert acc.status_code == 200, acc.text
    assert acc.json()["status"] == "accepted"
    sw = client.post("/auth/switch-organization", headers=_auth(member_token),
                     json={"ouid": ouid})
    assert sw.status_code == 200, sw.text


def test_invite_not_accepted_by_other_person():
    u = _uid()
    owner = f"o2_{u}"
    member = f"m2_{u}"
    outsider = f"x2_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"组{u}", "company", ouid=f"co2_{u}")
    ouid = space["organization"]["ouid"]
    org_owner_token = space["access_token"]
    _register_token(member, puid=member)
    outsider_token = _register_token(outsider, puid=outsider)

    inv = client.post(f"/spaces/{ouid}/invites", headers=_auth(org_owner_token),
                      json={"invitee_puid": member})
    invite_uid = inv.json()["invite_uid"]

    acc = client.post("/spaces/invites/accept", headers=_auth(outsider_token),
                      json={"invite_uid": invite_uid})
    assert acc.status_code == 403, acc.text


# ============================================================================
# 13. 治理流程：join request + 审批
# ============================================================================
def test_join_request_approve_flow():
    u = _uid()
    owner = f"jo_{u}"
    requester = f"jr_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"项目{u}", "company", ouid=f"pj_{u}")
    ouid = space["organization"]["ouid"]
    org_owner_token = space["access_token"]
    req_token = _register_token(requester, puid=requester)

    req = client.post(f"/spaces/{ouid}/join-requests", headers=_auth(req_token), json={})
    assert req.status_code == 201, req.text
    request_uid = req.json()["request_uid"]

    appr = client.post("/spaces/join-requests/approve", headers=_auth(org_owner_token),
                       json={"request_uid": request_uid})
    assert appr.status_code == 200, appr.text
    assert appr.json()["status"] == "approved"
    sw = client.post("/auth/switch-organization", headers=_auth(req_token),
                     json={"ouid": ouid})
    assert sw.status_code == 200, sw.text


# ============================================================================
# 14. 退出
# ============================================================================
def test_leave_space():
    u = _uid()
    owner = f"lv_{u}"
    member = f"lm_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"组织{u}", "company", ouid=f"lv_org_{u}")
    ouid = space["organization"]["ouid"]
    org_owner_token = space["access_token"]
    member_token = _register_token(member, puid=member)
    _add_membership(org_owner_token, member, ouid)

    resp = client.post("/spaces/leave", headers=_auth(member_token), json={"ouid": ouid})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "left"
    sw = client.post("/auth/switch-organization", headers=_auth(member_token),
                     json={"ouid": ouid})
    assert sw.status_code == 403, sw.text


def test_cannot_leave_personal_space():
    u = _uid()
    login = f"pl_{u}"
    token = _register_token(login, puid=login)
    resp = client.post("/spaces/leave", headers=_auth(token),
                       json={"ouid": f"{login}_personal"})
    assert resp.status_code == 422, resp.text


def test_last_owner_cannot_leave():
    u = _uid()
    owner = f"ol_{u}"
    member = f"olm_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"组{u}", "company", ouid=f"lo_{u}")
    ouid = space["organization"]["ouid"]
    org_owner_token = space["access_token"]
    member_token = _register_token(member, puid=member)
    _add_membership(org_owner_token, member, ouid)

    resp = client.post("/spaces/leave", headers=_auth(org_owner_token), json={"ouid": ouid})
    assert resp.status_code == 409, resp.text


# ============================================================================
# 15. 踢出
# ============================================================================
def test_kick_protections():
    u = _uid()
    owner = f"kk_{u}"
    member = f"km_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"队{u}", "company", ouid=f"kk_org_{u}")
    ouid = space["organization"]["ouid"]
    org_owner_token = space["access_token"]
    member_token = _register_token(member, puid=member)
    _add_membership(org_owner_token, member, ouid)

    kick = client.post("/spaces/kick", headers=_auth(org_owner_token),
                       json={"ouid": ouid, "member_puid": member})
    assert kick.status_code == 200, kick.text
    sw = client.post("/auth/switch-organization", headers=_auth(member_token),
                     json={"ouid": ouid})
    assert sw.status_code == 403, sw.text

    kick2 = client.post("/spaces/kick", headers=_auth(org_owner_token),
                        json={"ouid": ouid, "member_puid": owner})
    assert kick2.status_code == 409, kick2.text


# ============================================================================
# 16. owner 转让
# ============================================================================
def test_ownership_transfer():
    u = _uid()
    owner = f"ot_{u}"
    member = f"otm_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"会{u}", "company", ouid=f"ot_org_{u}")
    ouid = space["organization"]["ouid"]
    org_owner_token = space["access_token"]
    member_token = _register_token(member, puid=member)
    _add_membership(org_owner_token, member, ouid)

    tr = client.post("/spaces/transfer", headers=_auth(org_owner_token),
                     json={"ouid": ouid, "new_owner_puid": member})
    assert tr.status_code == 200, tr.text
    assert tr.json()["new_owner_puid"] == member

    leave = client.post("/spaces/leave", headers=_auth(owner_token), json={"ouid": ouid})
    assert leave.status_code == 200, leave.text
    resp = client.post("/spaces/leave", headers=_auth(member_token), json={"ouid": ouid})
    assert resp.status_code == 409, resp.text


# ============================================================================
# 17. POST /spaces 建组织后创建者即 owner 且无需再 switch
# ============================================================================
def test_create_space_makes_owner():
    u = _uid()
    login = f"cs_{u}"
    token = _register_token(login, puid=login)
    data = _create_space(token, f"工作室{u}", "ecommerce", ouid=f"ws_{u}")
    assert data["organization"]["type"] == "ecommerce"
    assert data["membership"]["role"] == "owner"
    assert data["requires_organization"] is False
    assert data["access_token"]
    _assert_no_db_ids(data)


def test_create_space_rejects_personal_type():
    u = _uid()
    token = _register_token(f"csp_{u}", puid=f"csp_{u}")
    resp = client.post("/spaces", headers=_auth(token),
                       json={"name": f"私{u}", "org_type": "personal"})
    assert resp.status_code == 422, resp.text


def test_create_space_rejects_invalid_org_type():
    u = _uid()
    token = _register_token(f"cst_{u}", puid=f"cst_{u}")
    resp = client.post("/spaces", headers=_auth(token),
                       json={"name": f"X{u}", "org_type": "evil"})
    assert resp.status_code == 422, resp.text
