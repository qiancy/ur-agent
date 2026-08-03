# AUTH-03/ORG-01 开发计划：默认个人空间与组织治理 MVP

> 日期：2026-08-03
> 角色：PM / 产品负责人
> 状态：下达开发团队，生产参赛前必须完成
> 前置：AUTH-02（单账号多空间认证与注册）已验收通过
> 关联文档：`AUTH-02_单账号多空间认证与注册开发计划.md`、`uc001_用户认证用例.md`、`CR-01_多业务空间参赛版开发规格书.md`

**Goal:** 注册即拥有默认 personal 空间，删除"凭 initial_ouid 直接加入任意组织"的能力；组织加入/退出全部走治理流程（invite、join request、exit、kick、owner 转让、最后 owner 保护），并补齐用户注册测试文档。

**Architecture:** 后端 FastAPI + PostgreSQL。新增 `space_invite` / `space_join_request` 两张治理表与对应 DB 函数；`/auth/register` 改为原子创建 person+account+personal 空间(owner)；`POST /spaces` 建组织自动 owner；`/spaces/*` 提供治理端点；`POST /organizations/members` 收口为 owner/admin 治理端点。前端 `LoginView` 登录走 `/auth/login`、删 noSpace 占位与 initialOuid 输入。黑盒 TDD（TestClient）先行，最后全量回归 + 前端构建。

**Tech Stack:** FastAPI、psycopg2、Pydantic v2、Vue 3 + Vite + TS、Vitest、pytest + TestClient。

**开发者须知：** 所有 API 只暴露 `puid` / `ouid` / `invite_uid` / `request_uid` 业务字段，JWT 与响应不得含 DB 数字 ID。`initial_ouid` 从注册契约中彻底移除（`extra=forbid` 使其 422）。测试黑盒原则不变：不改 `src/`，只改 `agents/tdd/` 测试与 `web/src` 前端。

---

## 产品规则（PM 定稿）

1. 注册自动创建 personal 空间：`ouid={puid}_personal`、`type=personal`、`name={name}的个人空间`、membership `role=owner`；注册必定返回 personal 空间 JWT。
2. personal 空间是默认空间；**不能退出、不能被踢、MVP 不开放邀请他人加入**。
3. `POST /spaces` 用户建组织（family/ecommerce/campaign/starship/company），创建者自动 owner。
4. 加入组织只走 **invite**（owner/admin 建 invite → 受邀人接受）或 **join request**（用户提交 → owner/admin 审批）。
5. member 可退出普通组织；**owner 不能直接退出最后 owner**（先转让或解散）。
6. owner/admin 可移除 member/viewer，但**不能移除最后 owner**；personal 空间成员不可移除。

## 开发红线（不可违反）

- 注册必定返回 personal 空间 JWT（不再有 `requires_organization=true` 分支）。
- 删除 `initial_ouid` 直接建 membership 能力（schema 移除字段，传入即 422）。
- 加入组织只走 invite / join request；`POST /organizations/members` 收口为 owner/admin 治理端点，且不能加 personal 空间成员。
- 组织治理 API 只暴露 `puid` / `ouid` / `invite_uid` / `request_uid`，无 DB 数字 ID。
- 补测试：默认 personal、公开注册不能加入任意组织、邀请加入、申请审批、退出、踢出、最后 owner 保护、owner 转让。
- **用户注册测试必须写入测试文档。**

---

## 文件结构（新建/修改）

| 文件 | 动作 | 职责 |
| :--- | :--- | :--- |
| `src/db/database.py` | 改 | 新增 2 表 + 原子注册 + 治理 DB 函数；`list_person_organizations` 排序 personal 优先 |
| `src/models/schemas.py` | 改 | `RegisterRequest` 移除 `initial_ouid`；新增 Space/Invite/JoinRequest/Leave/Kick/Transfer schema |
| `src/routers/auth.py` | 改 | `register` 原子创建 personal 空间并返回其 JWT |
| `src/routers/spaces.py` | 改 | 新增 `POST /spaces` 与治理端点 |
| `src/routers/organization.py` | 改 | `POST /organizations/members` 收口为 owner/admin |
| `agents/tdd/test_auth_api.py` | 改 | 重写契约 + 治理流程测试 |
| `agents/tdd/test_*.py`（9 个） | 改 | 移除 `initial_ouid` 依赖，改用注册→建组织/邀请流程 |
| `agents/tdd/回归测试计划.md` | 改 | 新增用户注册测试章节 |
| `agents/tdd/测试执行指南.md` | 改 | 新增用户注册测试执行说明 |
| `web/src/api/auth.ts` | 改 | `RegisterParams` 移除 `initialOuid` |
| `web/src/api/seller.ts` | 改 | 保留（`sellerLogin` 后端 alias 保留） |
| `web/src/views/LoginView.vue` | 改 | 登录用 `loginAccount`；删 initialOuid 输入与 noSpace 态 |
| `web/src/api/auth.test.ts` | 改 | 更新 registerAccount 契约测试 |
| `web/src/views/LoginView.test.ts` | 改 | 登录 mock 换 `loginAccount`；删 no-space/initialOuid 用例 |
| `_pm/进度跟踪.md` | 改 | 标记 AUTH-03 进度 |

**不动**：`src/app.py`、`src/routers/deps.py`、`src/auth/auth.py`、`scripts/setup_fire_newye_campaign.py` 的公开创建路径（其加成员调用不再执行——见 Task 7 说明）、`agents/tdd/test_three_kingdoms_http.py`（4 个既有失败非本次回归，成员创建改由 seed 数据提供）。

---

## Task 1: DB 治理表 + 原子注册 + 治理函数（`src/db/database.py`）

**Files:**
- Modify: `src/db/database.py`（SCHEMA_SQL 区 :57、CRUD 区 :304、organization 区 :336）

- [ ] **Step 1: 在 SCHEMA_SQL 中追加两张治理表**

在 `src/db/database.py` 的 `SCHEMA_SQL` 末尾（`membership` 表定义之后，`resource` 之前）插入：

```sql
-- Space Invite: 组织邀请 (owner/admin 创建, 受邀人接受)
CREATE TABLE IF NOT EXISTS space_invite (
    id              SERIAL PRIMARY KEY,
    invite_uid      VARCHAR(100) UNIQUE NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    invitee_puid    VARCHAR(100) NOT NULL,
    role            VARCHAR(100) NOT NULL DEFAULT 'member',
    status          VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_by_puid VARCHAR(100) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Space Join Request: 加入申请 (用户提交, owner/admin 审批)
CREATE TABLE IF NOT EXISTS space_join_request (
    id              SERIAL PRIMARY KEY,
    request_uid     VARCHAR(100) UNIQUE NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    requester_puid  VARCHAR(100) NOT NULL,
    status          VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

注意 `init_database` 的 DROP 段（:255）会先 DROP 全部表再建——`space_invite`/`space_join_request` 无需额外 DROP（`DROP TABLE IF EXISTS` 未列出它们，但全库重建后不存在旧表残留风险；为幂等，DROP 段末尾可加两条 `DROP TABLE IF EXISTS space_join_request CASCADE; DROP TABLE IF EXISTS space_invite CASCADE;` 保持 clean-drop 一致性）。

- [ ] **Step 2: 新增原子注册函数**

在 CRUD helpers 区（`:334` 后）新增：

```python
def register_personal_space(puid: str, name: str, login: str,
                            password_hash: str, salt: str):
    """Atomically create person + account + personal org + owner membership.

    Returns (person, account, org, membership). Any failure rolls back.
    personal space: ouid={puid}_personal, type=personal, name={name}的个人空间.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO person (puid, name) VALUES (%s, %s) RETURNING *",
            (puid, name))
        person = dict(cur.fetchone())
        cur.execute(
            "INSERT INTO account (person_id, login, password, salt, system_role)"
            " VALUES (%s, %s, %s, %s, 'user') RETURNING *",
            (person["id"], login, password_hash, salt))
        account = dict(cur.fetchone())
        org_ouid = f"{puid}_personal"
        cur.execute(
            "INSERT INTO organization (ouid, name, type, description)"
            " VALUES (%s, %s, 'personal', '个人空间') RETURNING *",
            (org_ouid, f"{name}的个人空间"))
        org = dict(cur.fetchone())
        cur.execute(
            "INSERT INTO membership (person_id, organization_id, role)"
            " VALUES (%s, %s, 'owner') RETURNING *",
            (person["id"], org["id"]))
        membership = dict(cur.fetchone())
        conn.commit()
        return person, account, org, membership
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

- [ ] **Step 3: 新增治理 DB 函数**

在 membership 区（`:500` 后）新增：

```python
def create_org_invite(organization_id: int, invitee_puid: str,
                      role: str, created_by_puid: str) -> Dict[str, Any]:
    import secrets as _secrets
    invite_uid = f"inv_{_secrets.token_hex(4)}"
    sql = """
        INSERT INTO space_invite
            (invite_uid, organization_id, invitee_puid, role, created_by_puid, status)
        VALUES (%s, %s, %s, %s, %s, 'pending')
        RETURNING *
    """
    return dict(_execute(sql, (invite_uid, organization_id, invitee_puid,
                               role, created_by_puid), fetch_returning=True)[0])


def query_invite_by_uid(invite_uid: str) -> List[Dict]:
    return _fetch("SELECT * FROM space_invite WHERE invite_uid = %s", (invite_uid,))


def accept_invite(invite_uid: str, person_id: int) -> Optional[Dict[str, Any]]:
    """Atomically add membership and mark invite accepted. Returns membership or None."""
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM space_invite WHERE invite_uid = %s FOR UPDATE",
                    (invite_uid,))
        invite = cur.fetchone()
        if not invite or invite["status"] != "pending":
            return None
        cur.execute(
            "INSERT INTO membership (person_id, organization_id, role)"
            " VALUES (%s, %s, %s) ON CONFLICT (person_id, organization_id) DO NOTHING"
            " RETURNING *",
            (person_id, invite["organization_id"], invite["role"]))
        membership = cur.fetchone()
        cur.execute("UPDATE space_invite SET status = 'accepted' WHERE invite_uid = %s",
                    (invite_uid,))
        conn.commit()
        return dict(membership) if membership else None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_join_request(organization_id: int, requester_puid: str) -> Dict[str, Any]:
    import secrets as _secrets
    request_uid = f"req_{_secrets.token_hex(4)}"
    sql = """
        INSERT INTO space_join_request
            (request_uid, organization_id, requester_puid, status)
        VALUES (%s, %s, %s, 'pending')
        RETURNING *
    """
    return dict(_execute(sql, (request_uid, organization_id, requester_puid),
                         fetch_returning=True)[0])


def query_join_request_by_uid(request_uid: str) -> List[Dict]:
    return _fetch("SELECT * FROM space_join_request WHERE request_uid = %s",
                  (request_uid,))


def approve_join_request(request_uid: str, person_id: int,
                         role: str = "member") -> Optional[Dict[str, Any]]:
    """Atomically add membership and mark request approved. Returns membership or None."""
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM space_join_request WHERE request_uid = %s FOR UPDATE",
                    (request_uid,))
        req = cur.fetchone()
        if not req or req["status"] != "pending":
            return None
        cur.execute(
            "INSERT INTO membership (person_id, organization_id, role)"
            " VALUES (%s, %s, %s) ON CONFLICT (person_id, organization_id) DO NOTHING"
            " RETURNING *",
            (person_id, req["organization_id"], role))
        membership = cur.fetchone()
        cur.execute("UPDATE space_join_request SET status = 'approved' WHERE request_uid = %s",
                    (request_uid,))
        conn.commit()
        return dict(membership) if membership else None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def remove_membership(person_id: int, organization_id: int) -> int:
    return _execute("DELETE FROM membership WHERE person_id = %s AND organization_id = %s",
                    (person_id, organization_id))


def count_org_owners(organization_id: int) -> int:
    rows = _fetch(
        "SELECT COUNT(*) AS n FROM membership WHERE organization_id = %s AND role = 'owner'",
        (organization_id,))
    return int(rows[0]["n"])


def transfer_ownership(organization_id: int, new_owner_person_id: int) -> None:
    """Transfer: old owner -> admin, new member -> owner (single transaction)."""
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "UPDATE membership SET role = 'admin' WHERE organization_id = %s AND role = 'owner'",
            (organization_id,))
        cur.execute(
            "UPDATE membership SET role = 'owner' WHERE organization_id = %s AND person_id = %s",
            (organization_id, new_owner_person_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

- [ ] **Step 4: `list_person_organizations` 排序 personal 优先**

修改 `list_person_organizations`（:500）的 ORDER BY：

```python
        ORDER BY CASE WHEN o.type = 'personal' THEN 0 ELSE 1 END, o.ouid
```

这样 `_resolve_default_org` 取 `organizations[0]` 即默认落到 personal 空间。

- [ ] **Step 5: 验证无语法错误**

Run: `python -c "import src.db.database"` → Expected: 无异常（需 `PYTHONPATH=.`）。

---

## Task 2: Schema 更新（`src/models/schemas.py`）

**Files:**
- Modify: `src/models/schemas.py`（Auth 区 :139、Organization 区 :12）

- [ ] **Step 1: `RegisterRequest` 移除 `initial_ouid`**

替换 :139-145：

```python
class RegisterRequest(BaseModel):
    login: str  # account login credential; not parsed as puid/ouid
    password: str
    name: str
    puid: Optional[str] = None  # business person id; defaults to login when safe
    model_config = {"extra": "forbid"}
```

`extra=forbid` 保证传 `initial_ouid` 返回 422（红线：删除 initial_ouid 直接加入能力）。

- [ ] **Step 2: 新增治理 schema**

在 Auth 区之后新增：

```python
# ── Space governance (AUTH-03/ORG-01) ───────────────────────────────────────

class SpaceCreate(BaseModel):
    name: str
    org_type: str
    ouid: Optional[str] = None
    description: Optional[str] = None
    model_config = {"extra": "forbid"}


class InviteCreate(BaseModel):
    invitee_puid: str
    role: Optional[str] = "member"
    model_config = {"extra": "forbid"}


class AcceptInviteRequest(BaseModel):
    invite_uid: str
    model_config = {"extra": "forbid"}


class JoinRequestCreate(BaseModel):
    message: Optional[str] = None
    model_config = {"extra": "forbid"}


class ApproveJoinRequestRequest(BaseModel):
    request_uid: str
    model_config = {"extra": "forbid"}


class LeaveSpaceRequest(BaseModel):
    ouid: str
    model_config = {"extra": "forbid"}


class KickMemberRequest(BaseModel):
    ouid: str
    member_puid: str
    model_config = {"extra": "forbid"}


class TransferOwnerRequest(BaseModel):
    ouid: str
    new_owner_puid: str
    model_config = {"extra": "forbid"}
```

- [ ] **Step 3: 验证**

Run: `python -c "import src.models.schemas"` → Expected: 无异常。

---

## Task 3: `/auth/register` 原子创建 personal 空间（`src/routers/auth.py`）

**Files:**
- Modify: `src/routers/auth.py`（:108 `_resolve_default_org`、:123 `register`、:178 `_requires_org_dto`）

- [ ] **Step 1: 重写 `register`**

替换 :123-178 的 `register` 函数：

```python
@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    """Create account + person + personal space atomically.

    Registration always yields a personal space (owner) and its JWT.
    Public registration never grants privileged roles (system_role stays 'user').
    initial_ouid is gone: joining another org only via invite / join request.
    """
    if not body.login.strip():
        raise HTTPException(422, "login is required")

    if body.puid is not None and body.puid.strip():
        puid = body.puid.strip()
        if not validate_puid(puid):
            raise HTTPException(422, "Invalid puid. Only letters, numbers, underscores, hyphens allowed.")
    else:
        puid = derive_puid_from_login(body.login)
        if puid is None:
            raise HTTPException(
                422, "A safe puid is required when login cannot be used as puid "
                     "(only letters, numbers, underscores, hyphens).")

    persons = query_person_by_puid(puid)
    if persons and any(a["login"] != body.login for a in _accounts_of(persons[0]["id"])):
        raise HTTPException(409, "puid already registered by another user")
    if query_account_by_login(body.login):
        raise HTTPException(409, "Login already taken")
    if persons:
        raise HTTPException(409, "puid already registered")

    from src.auth.auth import hash_password
    hashed_password, salt = hash_password(body.password)

    from src.db.database import register_personal_space
    person, account, org, membership = register_personal_space(
        puid=puid, name=body.name, login=body.login,
        password_hash=hashed_password, salt=salt)

    return _context_dto(person, org, account, membership)
```

- [ ] **Step 2: 保留 `_requires_org_dto` 供 login 兜底，但 register 不再使用**

`login`（:186）与 `seller_login` 对无 membership 的旧账号仍走 `_requires_org_dto`——保留该函数与分支，不改动（AUTH-02 后新账号必有 personal 空间，老账号若确实无 membership 仍返回 requires_organization=true，前端已兼容）。

- [ ] **Step 3: 验证**

Run: `python -c "import src.routers.auth"` → Expected: 无异常。

---

## Task 4: 空间治理端点（`src/routers/spaces.py`）

**Files:**
- Modify: `src/routers/spaces.py`（:14 router、:59 末尾）

- [ ] **Step 1: 新增依赖导入与 helper**

在文件头部 import 区补充：

```python
from src.routers.deps import (
    require_strict_org_context, require_authenticated, get_current_user,
)
from src.db.database import (
    get_space_overview, get_space_resources, get_space_persons,
    get_space_transactions, get_space_timeline,
    query_organization_by_ouid, query_person_by_puid, query_membership,
    create_organization, add_membership, create_org_invite,
    query_invite_by_uid, accept_invite, create_join_request,
    query_join_request_by_uid, approve_join_request,
    remove_membership, count_org_owners, transfer_ownership,
)
from src.models.schemas import (
    SpaceCreate, InviteCreate, AcceptInviteRequest, JoinRequestCreate,
    ApproveJoinRequestRequest, LeaveSpaceRequest, KickMemberRequest,
    TransferOwnerRequest,
)
```

新增私有 helper（放在 `_reject_identity_params` 之后）：

```python
_VALID_ORG_TYPES = {"family", "ecommerce", "campaign", "starship", "company"}

# Governance responses carry only business fields (puid/ouid/uid), never DB ids.
_GOV_FORBIDDEN = {"id", "organization_id", "membership_id"}


def _gov_dto(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if k not in _GOV_FORBIDDEN}


def _get_person_org(puid: str, ouid: str):
    from src.db.database import query_person_by_puid, query_organization_by_ouid, query_membership
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(404, "Person not found")
    orgs = query_organization_by_ouid(ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    memberships = query_membership(persons[0]["id"], orgs[0]["id"])
    return persons[0], orgs[0], (memberships[0] if memberships else None)
```

- [ ] **Step 2: `POST /spaces` 建组织（创建者自动 owner）**

在 router 下新增：

```python
@router.post("", status_code=201)
async def create_space(body: SpaceCreate, request: Request):
    """Create an organization; caller becomes its owner. JWT required."""
    payload = require_authenticated(request)
    if body.org_type not in _VALID_ORG_TYPES:
        raise HTTPException(422, f"org_type must be one of {sorted(_VALID_ORG_TYPES)}")
    if body.org_type == "personal":
        raise HTTPException(422, "personal spaces are auto-created at registration")
    puid = payload.get("puid")
    if not puid:
        raise HTTPException(401, "JWT must include puid")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    person = persons[0]
    org = create_organization(body.name, body.org_type, body.description,
                              ouid=body.ouid)
    membership = add_membership(person["id"], org["id"], "owner")
    from src.routers.auth import _context_dto
    account = _fetch_account_for_person(person["id"], payload)[0]
    return _context_dto(person, org, account, membership)
```

在文件内新增小 helper（放在 `_get_person_org` 后）：

```python
def _fetch_account_for_person(person_id: int, payload: dict):
    from src.db.database import _fetch
    accounts = _fetch("SELECT * FROM account WHERE person_id = %s ORDER BY id",
                      (person_id,))
    return accounts or [{
        "system_role": payload.get("system_role", "user"),
        "login": payload.get("puid"), "status": "active",
    }]
```

> 说明：`create_space` 返回 `_context_dto`，其 `access_token` 已指向新组织（owner），创建者无需再 switch。

- [ ] **Step 3: invite 创建与接受**

```python
@router.post("/{ouid}/invites", status_code=201)
async def create_invite(ouid: str, body: InviteCreate, request: Request):
    """owner/admin of the org creates an invite. JWT must be in that org context."""
    ctx = require_strict_org_context(request)
    if ctx.get("ouid") != ouid:
        raise HTTPException(403, "Invite must be created from the target org context")
    if ctx.get("role") not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can create invites")
    orgs = query_organization_by_ouid(ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    if orgs[0]["type"] == "personal":
        raise HTTPException(422, "Personal spaces do not accept invites (MVP)")
    invite = create_org_invite(orgs[0]["id"], body.invitee_puid, body.role or "member",
                               ctx["puid"])
    return _gov_dto({
        "invite_uid": invite["invite_uid"],
        "ouid": ouid,
        "invitee_puid": body.invitee_puid,
        "role": invite["role"],
        "status": invite["status"],
    })


@router.post("/invites/accept")
async def accept_org_invite(body: AcceptInviteRequest, request: Request):
    """Invitee accepts an invite (JWT person must match invitee_puid)."""
    payload = require_authenticated(request)
    puid = payload.get("puid")
    if not puid:
        raise HTTPException(401, "JWT must include puid")
    invites = query_invite_by_uid(body.invite_uid)
    if not invites:
        raise HTTPException(404, "Invite not found")
    invite = invites[0]
    if invite["invitee_puid"] != puid:
        raise HTTPException(403, "Invite belongs to another person")
    if invite["status"] != "pending":
        raise HTTPException(409, "Invite already used")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    membership = accept_invite(body.invite_uid, persons[0]["id"])
    if not membership:
        raise HTTPException(409, "Invite already used or already a member")
    return _gov_dto({
        "ouid": _org_ouid_by_id(invite["organization_id"]),
        "puid": puid,
        "role": membership["role"],
        "status": "accepted",
    })
```

新增 helper（放在 `_fallback_account` 后）：

```python
def _org_ouid_by_id(organization_id: int) -> str:
    from src.db.database import _fetch
    rows = _fetch("SELECT ouid FROM organization WHERE id = %s", (organization_id,))
    if not rows:
        raise HTTPException(404, "Organization not found")
    return rows[0]["ouid"]
```

- [ ] **Step 4: join request 提交与审批**

```python
@router.post("/{ouid}/join-requests", status_code=201)
async def create_join_request(ouid: str, body: JoinRequestCreate, request: Request):
    """Any authenticated user may request to join an org (not the personal type)."""
    payload = require_authenticated(request)
    puid = payload.get("puid")
    if not puid:
        raise HTTPException(401, "JWT must include puid")
    orgs = query_organization_by_ouid(ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    if orgs[0]["type"] == "personal":
        raise HTTPException(422, "Personal spaces are not joinable (MVP)")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    if query_membership(persons[0]["id"], orgs[0]["id"]):
        raise HTTPException(409, "Already a member")
    req = create_join_request(orgs[0]["id"], puid)
    return _gov_dto({
        "request_uid": req["request_uid"],
        "ouid": ouid,
        "requester_puid": puid,
        "status": req["status"],
    })


@router.post("/join-requests/approve")
async def approve_join_request(body: ApproveJoinRequestRequest, request: Request):
    """owner/admin of the target org approves a join request."""
    reqs = query_join_request_by_uid(body.request_uid)
    if not reqs:
        raise HTTPException(404, "Join request not found")
    req = reqs[0]
    if req["status"] != "pending":
        raise HTTPException(409, "Join request already processed")
    orgs = query_organization_by_id(req["organization_id"])
    if not orgs:
        raise HTTPException(404, "Organization not found")
    # caller must be owner/admin of that org (any space context allowed for lookup)
    payload = require_authenticated(request)
    puid = payload.get("puid")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    memberships = query_membership(persons[0]["id"], req["organization_id"])
    if not memberships or memberships[0]["role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can approve join requests")
    requester = query_person_by_puid(req["requester_puid"])
    if not requester:
        raise HTTPException(404, "Requester person not found")
    membership = approve_join_request(body.request_uid, requester[0]["id"])
    if not membership:
        raise HTTPException(409, "Join request already processed or already a member")
    return _gov_dto({
        "request_uid": req["request_uid"],
        "ouid": orgs[0]["ouid"],
        "puid": req["requester_puid"],
        "role": membership["role"],
        "status": "approved",
    })
```

新增 helper（放在 `query_organization_by_ouid_ensure` 后）：

```python
def query_organization_by_id(organization_id: int):
    from src.db.database import _fetch
    return _fetch("SELECT * FROM organization WHERE id = %s", (organization_id,))
```

- [ ] **Step 5: 退出 / 踢出 / 转让（最后 owner 保护）**

```python
@router.post("/leave")
async def leave_space(body: LeaveSpaceRequest, request: Request):
    """Member leaves an org. Personal space cannot be left; last owner cannot leave."""
    payload = require_authenticated(request)
    puid = payload.get("puid")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    person, org, membership = _get_person_org(puid, body.ouid)
    if not membership:
        raise HTTPException(403, "No membership in this organization")
    if org["type"] == "personal":
        raise HTTPException(422, "Personal space cannot be left")
    if membership["role"] == "owner" and count_org_owners(org["id"]) <= 1:
        raise HTTPException(409, "Last owner cannot leave; transfer ownership first")
    remove_membership(person["id"], org["id"])
    return {"ouid": body.ouid, "puid": puid, "status": "left"}


@router.post("/kick")
async def kick_member(body: KickMemberRequest, request: Request):
    """owner/admin removes a member/viewer; last owner and personal members protected."""
    ctx = require_strict_org_context(request)
    if ctx.get("ouid") != body.ouid:
        raise HTTPException(403, "Kick must be issued from the target org context")
    if ctx.get("role") not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can remove members")
    orgs = query_organization_by_ouid(body.ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    if orgs[0]["type"] == "personal":
        raise HTTPException(422, "Members of a personal space cannot be removed")
    target, _, target_membership = _get_person_org(body.member_puid, body.ouid)
    if not target_membership:
        raise HTTPException(404, "Member not found in this organization")
    if target_membership["role"] == "owner":
        if count_org_owners(orgs[0]["id"]) <= 1:
            raise HTTPException(409, "Cannot remove the last owner")
        raise HTTPException(403, "Owner can only be removed via ownership transfer")
    if target["puid"] == ctx["puid"]:
        raise HTTPException(422, "Use /spaces/leave to leave by yourself")
    remove_membership(target["id"], orgs[0]["id"])
    return {"ouid": body.ouid, "puid": body.member_puid, "status": "removed"}


@router.post("/transfer")
async def transfer_owner(body: TransferOwnerRequest, request: Request):
    """Owner transfers ownership to another member (old owner becomes admin)."""
    ctx = require_strict_org_context(request)
    if ctx.get("ouid") != body.ouid:
        raise HTTPException(403, "Transfer must be issued from the target org context")
    if ctx.get("role") != "owner":
        raise HTTPException(403, "Only the owner can transfer ownership")
    if body.new_owner_puid == ctx["puid"]:
        raise HTTPException(422, "Already the owner")
    orgs = query_organization_by_ouid(body.ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    target, _, target_membership = _get_person_org(body.new_owner_puid, body.ouid)
    if not target_membership:
        raise HTTPException(404, "New owner must be an existing member")
    transfer_ownership(orgs[0]["id"], target["id"])
    return {"ouid": body.ouid, "new_owner_puid": body.new_owner_puid, "status": "transferred"}
```

- [ ] **Step 6: 验证**

Run: `python -c "import src.routers.spaces"` → Expected: 无异常。

---

## Task 5: 收口 `POST /organizations/members`（`src/routers/organization.py`）

**Files:**
- Modify: `src/routers/organization.py`（:36 `add_org_member`）

- [ ] **Step 1: 重写 `add_org_member` 为 owner/admin 治理端点**

替换 :36-44：

```python
@router.post("/organizations/members", status_code=201)
async def add_org_member(body: MembershipAdd, request: Request):
    """Governed member add: caller must be owner/admin of the org (JWT context).

    Only member/viewer roles can be assigned; personal space members cannot be added.
    """
    from src.routers.deps import require_strict_org_context
    ctx = require_strict_org_context(request)
    if ctx.get("ouid") != body.ouid:
        raise HTTPException(403, "Must add members from the target org context")
    if ctx.get("role") not in ("owner", "admin"):
        raise HTTPException(403, "Only owner or admin can add members")
    if body.role not in ("member", "viewer"):
        raise HTTPException(422, "role must be 'member' or 'viewer'")
    orgs = query_organization_by_ouid(body.ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    if orgs[0]["type"] == "personal":
        raise HTTPException(422, "Cannot add members to a personal space")
    persons = query_person_by_puid(body.puid)
    if not persons:
        raise HTTPException(404, "Person not found")
    return add_membership(persons[0]["id"], orgs[0]["id"], body.role)
```

> 兼容说明：AUTH-02 测试辅助 `_add_membership(puid, ouid, role)` 将改为在测试内先注册一个 owner（建 org）再用 owner JWT 调此端点——见 Task 7。

- [ ] **Step 2: 验证**

Run: `python -c "import src.routers.organization"` → Expected: 无异常。

---

## Task 6: 后端契约测试重写（`agents/tdd/test_auth_api.py`）

**Files:**
- Modify: `agents/tdd/test_auth_api.py`（全文件重写契约，保留黑盒 + uuid 隔离）

- [ ] **Step 1: 重写测试文件**

替换 helper 区（:43-76）与全部用例。新 helper：

```python
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
```

保留 `_assert_no_db_ids` 与 `_AUTH_FORBIDDEN_FIELDS`。治理响应中的 `invite_uid`/`request_uid` 是业务字段（允许出现），`_assert_no_db_ids` 只拒绝 `id`/`*_id`，因此原实现即可覆盖，无需新增集合。

- [ ] **Step 2: 核心契约用例**

```python
# 1. 注册自动创建 personal 空间并返回其 JWT
def test_register_creates_personal_space():
    u = _uid()
    login = f"reg_{u}"
    resp = _register(login, name="张三", puid=login)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["organization"]["ouid"] == f"{login}_personal"
    assert data["organization"]["type"] == "personal"
    assert data["membership"]["role"] == "owner"
    assert data["requires_organization"] is False
    assert data["access_token"]
    assert any(o["ouid"] == f"{login}_personal" for o in data["organizations"])
    _assert_no_db_ids(data)


# 2. 登录默认空间即 personal
def test_login_default_is_personal_space():
    u = _uid()
    login = f"dflt_{u}"
    _register_token(login, puid=login)
    resp = _login(login)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["organization"]["ouid"] == f"{login}_personal"
    assert data["organization"]["type"] == "personal"


# 3. initial_ouid 已从契约移除：传入返回 422
def test_register_rejects_initial_ouid():
    u = _uid()
    ouid = _make_org()
    resp = client.post("/auth/register", json={
        "login": f"rej_{u}", "password": "pass123", "name": "新人",
        "initial_ouid": ouid,
    })
    assert resp.status_code == 422, resp.text


# 4. 注册后仍不能凭 ouid 加入任意组织（invite/join request 之外无入口）
def test_registration_cannot_join_arbitrary_org():
    u = _uid()
    ouid = _make_org("company")
    login = f"outsider_{u}"
    _register_token(login, puid=login)
    # 直接 switch 到未加入组织 → 403
    token = _login(login).json()["access_token"]
    resp = client.post("/auth/switch-organization", headers=_auth(token),
                       json={"ouid": ouid})
    assert resp.status_code == 403, resp.text
```

- [ ] **Step 3: 治理流程用例（invite / join request / exit / kick / transfer / last-owner）**

```python
# invite 加入
def test_invite_join_flow():
    u = _uid()
    owner = f"owner_{u}"
    member = f"mem_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"团队{u}", "company", ouid=f"co_{u}")
    ouid = space["organization"]["ouid"]
    member_token = _register_token(member, puid=member)

    inv = client.post(f"/spaces/{ouid}/invites", headers=_auth(owner_token),
                      json={"invitee_puid": member, "role": "member"})
    assert inv.status_code == 201, inv.text
    invite_uid = inv.json()["invite_uid"]
    assert "id" not in inv.text and "organization_id" not in inv.text

    acc = client.post("/spaces/invites/accept", headers=_auth(member_token),
                      json={"invite_uid": invite_uid})
    assert acc.status_code == 200, acc.text
    assert acc.json()["status"] == "accepted"
    # 受邀人可切换进该组织
    sw = client.post("/auth/switch-organization", headers=_auth(member_token),
                     json={"ouid": ouid})
    assert sw.status_code == 200, sw.text


# join request + 审批
def test_join_request_approve_flow():
    u = _uid()
    owner = f"jo_{u}"
    requester = f"jr_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"项目{u}", "company", ouid=f"pj_{u}")
    ouid = space["organization"]["ouid"]
    req_token = _register_token(requester, puid=requester)

    req = client.post(f"/spaces/{ouid}/join-requests", headers=_auth(req_token), json={})
    assert req.status_code == 201, req.text
    request_uid = req.json()["request_uid"]

    appr = client.post("/spaces/join-requests/approve", headers=_auth(owner_token),
                       json={"request_uid": request_uid})
    assert appr.status_code == 200, appr.text
    assert appr.json()["status"] == "approved"
    sw = client.post("/auth/switch-organization", headers=_auth(req_token),
                     json={"ouid": ouid})
    assert sw.status_code == 200, sw.text


# 退出
def test_leave_space():
    u = _uid()
    owner = f"lv_{u}"
    member = f"lm_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"组织{u}", "company", ouid=f"lv_org_{u}")
    ouid = space["organization"]["ouid"]
    member_token = _register_token(member, puid=member)
    _add_membership(owner_token, member, ouid)

    resp = client.post("/spaces/leave", headers=_auth(member_token), json={"ouid": ouid})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "left"
    sw = client.post("/auth/switch-organization", headers=_auth(member_token),
                     json={"ouid": ouid})
    assert sw.status_code == 403, sw.text


# personal 空间不可退出
def test_cannot_leave_personal_space():
    u = _uid()
    login = f"pl_{u}"
    token = _register_token(login, puid=login)
    resp = client.post("/spaces/leave", headers=_auth(token),
                       json={"ouid": f"{login}_personal"})
    assert resp.status_code == 422, resp.text


# 最后 owner 不可退出（需先转让）
def test_last_owner_cannot_leave():
    u = _uid()
    owner = f"ol_{u}"
    member = f"olm_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"组{u}", "company", ouid=f"lo_{u}")
    ouid = space["organization"]["ouid"]
    member_token = _register_token(member, puid=member)
    _add_membership(owner_token, member, ouid)

    resp = client.post("/spaces/leave", headers=_auth(owner_token), json={"ouid": ouid})
    assert resp.status_code == 409, resp.text


# 踢出：不能踢最后 owner；owner 只能经转让移除
def test_kick_protections():
    u = _uid()
    owner = f"kk_{u}"
    member = f"km_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"队{u}", "company", ouid=f"kk_org_{u}")
    ouid = space["organization"]["ouid"]
    member_token = _register_token(member, puid=member)
    _add_membership(owner_token, member, ouid)

    # 踢普通 member 成功
    kick = client.post("/spaces/kick", headers=_auth(owner_token),
                       json={"ouid": ouid, "member_puid": member})
    assert kick.status_code == 200, kick.text
    sw = client.post("/auth/switch-organization", headers=_auth(member_token),
                     json={"ouid": ouid})
    assert sw.status_code == 403, sw.text

    # 踢最后 owner 被拒
    kick2 = client.post("/spaces/kick", headers=_auth(owner_token),
                        json={"ouid": ouid, "member_puid": owner})
    assert kick2.status_code == 409, kick2.text


# owner 转让后原 owner 变 admin，不能退出最后 owner 限制随之转移
def test_ownership_transfer():
    u = _uid()
    owner = f"ot_{u}"
    member = f"otm_{u}"
    owner_token = _register_token(owner, puid=owner)
    space = _create_space(owner_token, f"会{u}", "company", ouid=f"ot_org_{u}")
    ouid = space["organization"]["ouid"]
    member_token = _register_token(member, puid=member)
    _add_membership(owner_token, member, ouid)

    tr = client.post("/spaces/transfer", headers=_auth(owner_token),
                     json={"ouid": ouid, "new_owner_puid": member})
    assert tr.status_code == 200, tr.text
    assert tr.json()["new_owner_puid"] == member

    # 原 owner 现在可退出（不再是 owner，也不再是最后 owner 问题）
    leave = client.post("/spaces/leave", headers=_auth(owner_token), json={"ouid": ouid})
    assert leave.status_code == 200, leave.text
    # 新 owner 不能退出最后 owner
    resp = client.post("/spaces/leave", headers=_auth(member_token), json={"ouid": ouid})
    assert resp.status_code == 409, resp.text


# POST /spaces 建组织后创建者即 owner 且无需再 switch
def test_create_space_makes_owner():
    u = _uid()
    login = f"cs_{u}"
    token = _register_token(login, puid=login)
    data = _create_space(token, f"工作室{u}", "ecommerce", ouid=f"ws_{u}")
    assert data["organization"]["type"] == "ecommerce"
    assert data["membership"]["role"] == "owner"
    _assert_no_db_ids(data)
```

- [ ] **Step 4: 迁移原 7/8 号用例（认证响应无 DB id、switch 拒绝 DB id 字段）**

保留 `test_auth_responses_have_no_db_ids` 与 `test_switch_organization_rejects_db_id_fields`，将其中 `_register(..., initial_ouid=ouid)` 改为 `_register_token(...)` + `_add_membership(owner_token, login, ouid)` 的等价流程（用 `_make_org` + `_create_space` 组合）。`test_seller_login_shares_single_account_auth` 改为：注册 → 建 ecommerce 空间 → seller-login 返回该空间 JWT。

- [ ] **Step 5: 运行**

Run: `PYTHONPATH=. python -m pytest agents/tdd/test_auth_api.py -q`
Expected: 全部通过（含新增治理用例）。

---

## Task 7: 旧测试文件迁移（9 个文件）

**Files:**
- Modify: `agents/tdd/test_be02_acceptance.py`、`test_seller_ai_tools.py`、`test_seller_chat_api.py`、`test_seller_chat_live_llm.py`、`test_seller_inventory_api.py`、`test_seller_inventory_transaction_api.py`、`test_seller_products_api.py`、`test_seller_summary_api.py`、`test_spaces_api.py`

**迁移模式（逐文件套用）：**

旧模式：`POST /organizations` 建 org + `register(initial_ouid=ouid)` 让用户直接加入。

新模式（每个文件里的 fixture/helper 统一改为）：

```python
def _make_shop(login, org_type="ecommerce", name=None):
    """注册 → 建组织成为 owner → 返回 (ouid, token)."""
    s = uuid.uuid4().hex[:8]
    reg = client.post("/auth/register", json={
        "login": login, "password": "pass123", "name": name or login})
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]
    ouid = f"shop_{s}"
    resp = client.post("/spaces", headers={"Authorization": f"Bearer {token}"},
                       json={"name": f"店铺_{s}", "org_type": org_type, "ouid": ouid})
    assert resp.status_code == 201, resp.text
    return ouid, resp.json()["access_token"]
```

- 需要**两个成员在同一 org** 的场景（如权限隔离）：owner 用 `/spaces/{ouid}/invites` 或 `POST /organizations/members`（owner JWT）加第二个账号。
- `test_seller_products_api.py` 有多 shop 场景：为每个 shop 各注册一个 owner。
- `test_spaces_api.py` 的 `family_ctx`：改为注册 → `_create_space` family 组织 → 返回 `(ouid, token)`；其 `test_resources_physical_locations` 中第二个用户改为 owner 邀请/添加进 family。
- `test_seller_chat_live_llm.py`：若需真实 LLM 才跑，保持注册→建 org 结构，其余不变。

每个文件具体改动以该文件现有 `_register`/fixture 为准，统一替换 `"initial_ouid": ouid` 为"先注册拿 personal token → 建/加入组织"。

- [ ] **Step 1: 逐文件迁移 + 本地运行**

Run: `PYTHONPATH=. python -m pytest agents/tdd/test_be02_acceptance.py agents/tdd/test_seller_ai_tools.py agents/tdd/test_seller_chat_api.py agents/tdd/test_seller_inventory_api.py agents/tdd/test_seller_inventory_transaction_api.py agents/tdd/test_seller_products_api.py agents/tdd/test_seller_summary_api.py agents/tdd/test_spaces_api.py -q`
Expected: 全部通过。

- [ ] **Step 2: 火烧新野种子脚本不再走公开加成员**

`setup_fire_newye_campaign.py` 的 `add_membership` 改为直接 DB INSERT（脚本已具备 `_get_db_connection`），或在脚本顶部注册一个 campaign 组织的 owner，用 owner JWT 调 `POST /organizations/members`。优先 DB 直插（与 `create_person` 的 DB 直插策略一致）。

- [ ] **Step 3: 文档说明历史脚本**

在 `agents/tdd/回归测试计划.md` 注明：`test_three_kingdoms_http.py` 成员创建依赖 `setup_fire_newye_campaign.py` seed 数据，不再调用 `POST /organizations/members`（该端点已收口）；其 4 个既有失败（固定名 `测试物资` 撞唯一约束）为非本次回归，单独跟踪。

---

## Task 8: 前端改造（`web/src`）

**Files:**
- Modify: `web/src/api/auth.ts`、`web/src/views/LoginView.vue`、`web/src/api/auth.test.ts`、`web/src/views/LoginView.test.ts`

- [ ] **Step 1: `auth.ts` 移除 `initialOuid`**

替换 `RegisterParams`（:10-16）与 `registerAccount`（:18-34）：

```ts
export interface RegisterParams {
  login: string
  password: string
  name: string
  puid?: string
}

export async function registerAccount(
  params: RegisterParams,
): Promise<SellerLoginResult> {
  const body: Record<string, string> = {
    login: params.login,
    password: params.password,
    name: params.name,
  }
  if (params.puid) body.puid = params.puid
  const result = await request<SellerLoginResult>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  if (result.access_token) setToken(result.access_token)
  return result
}
```

- [ ] **Step 2: `LoginView.vue` 登录改用 `loginAccount` + 删 noSpace/initialOuid**

替换脚本区（:1-53）：

```ts
<script setup lang="ts">
import { ref } from 'vue'
import { loginAccount, registerAccount } from '../api/auth'
import type { SellerLoginResult } from '../api/seller'

const emit = defineEmits<{
  (e: 'authenticated', result: SellerLoginResult): void
}>()

const mode = ref<'login' | 'register'>('login')
const login = ref('')
const password = ref('')
const name = ref('')
const puid = ref('')
const error = ref('')
const loading = ref(false)

function switchMode(next: 'login' | 'register') {
  mode.value = next
  error.value = ''
}

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') {
      const result = await loginAccount(login.value.trim(), password.value)
      emit('authenticated', result)
    } else {
      const result = await registerAccount({
        login: login.value.trim(),
        password: password.value,
        name: name.value.trim(),
        puid: puid.value.trim() || undefined,
      })
      emit('authenticated', result)
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>
```

模板区：删除 `initialOuid` 字段与 `noSpace` 段落（:95-103、:106），注册成功后直接 `emit`。

- [ ] **Step 3: `auth.test.ts` 更新**

- `registerAccount` 用例：删除 `initialOuid` 传参与 `initial_ouid` 断言；`requires_organization:true` 分支用例改断言 personal 空间结果（或直接删除——注册必有 personal）。
- `loginAccount` 用例不变。

- [ ] **Step 4: `LoginView.test.ts` 更新**

- mock 改为：`vi.mock('../api/auth', () => ({ loginAccount, registerAccount }))`（`loginAccount` 用 `loginMock`，`registerAccount` 用 `registerMock`）。
- 登录用例：`expect(loginMock).toHaveBeenCalledWith('zhansan', 'pass123')` 不变。
- 注册用例：删除 initialOuid 输入与 `initialOuid: 'shop_demo'` 断言；删除 no-space 用例；`registerMock` 返回带 personal 空间的 RESULT。

- [ ] **Step 5: 前端全量验证**

Run: `cd web && npm test`
Expected: 全部通过。
Run: `cd web && npm run build`
Expected: 构建成功（vue-tsc 无类型错误）。

---

## Task 9: 测试文档（用户注册测试）

**Files:**
- Modify: `agents/tdd/回归测试计划.md`、`agents/tdd/测试执行指南.md`

- [ ] **Step 1: `回归测试计划.md` 新增「用户注册测试」章节**

内容包括：

- 用例：注册成功创建 personal 空间（owner）、默认空间即 personal、登录返回 personal JWT、`initial_ouid` 传入即 422、注册后不能凭 ouid 加入任意组织、invite 加入、join request 审批、退出（含 personal 禁止 / 最后 owner 禁止）、踢出（含最后 owner 保护）、owner 转让。
- 归属文件：`agents/tdd/test_auth_api.py`（含 `test_register_creates_personal_space`、`test_login_default_is_personal_space`、`test_register_rejects_initial_ouid`、`test_invite_join_flow`、`test_join_request_approve_flow`、`test_leave_space`、`test_cannot_leave_personal_space`、`test_last_owner_cannot_leave`、`test_kick_protections`、`test_ownership_transfer`）。
- 说明：这是"用户注册"的正式回归项，注册必须产生 personal 空间与可用 JWT。

- [ ] **Step 2: `测试执行指南.md` 同步**

增加「注册测试」执行步骤：启动后端 → `pytest agents/tdd/test_auth_api.py -q` → 断言注册/治理用例全绿；说明 DB 隔离（uuid）。

---

## Task 10: 进度跟踪 + 全量验收

**Files:**
- Modify: `_pm/进度跟踪.md`

- [ ] **Step 1: 更新进度**

AUTH-03/ORG-01 标记 ✅，日期 8/3。

- [ ] **Step 2: 全量验收命令**

```bash
PYTHONPATH=. python -m pytest agents/tdd/test_auth_api.py agents/tdd/test_be02_acceptance.py agents/tdd/test_seller_ai_tools.py agents/tdd/test_seller_chat_api.py agents/tdd/test_seller_inventory_api.py agents/tdd/test_seller_inventory_transaction_api.py agents/tdd/test_seller_products_api.py agents/tdd/test_seller_summary_api.py agents/tdd/test_spaces_api.py -q
```

Expected: 全部通过（`test_seller_chat_live_llm.py` 如需真实 LLM 可跳过）。

```bash
cd web && npm test && npm run build
```

Expected: 全部通过 + 构建成功。

- [ ] **Step 3: 红线自检**

- `git diff --check` 无空白错误。
- `rg -n "initial_ouid" src/` → 无命中（schema/router 全清）。
- `rg -n "requires_organization" src/routers/auth.py` → 仅 `login` 兜底分支与 `_requires_org_dto`（register 不再返回 true）。
- 安全扫描：认证/治理响应与 JWT 无 DB 数字 ID。

---

## Self-Review（执行前自查）

- 规格覆盖：PM 6 条产品规则 → Task 1（personal 空间/原子注册）、Task 4（建空间/invite/join/exit/kick/transfer）、Task 5（收口 members）；红线 → Task 2/3/6；前端 P1 → Task 8；测试文档 → Task 9。✅
- 无占位符：每个 Step 均含可执行代码或明确命令。✅
- 类型一致：`register_personal_space` / `create_org_invite` / `accept_invite` / `approve_join_request` / `remove_membership` / `count_org_owners` / `transfer_ownership` 签名在 Task 1 定义、Task 4 引用一致；`_context_dto` 在 Task 3/4 复用。✅
