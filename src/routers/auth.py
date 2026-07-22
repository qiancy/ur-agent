"""
Authentication endpoints: register and login.
"""
from fastapi import APIRouter, HTTPException

from src.models.schemas import RegisterRequest, LoginRequest
from src.db.database import (
    create_person, add_membership,
    query_person_by_pid, query_organization_by_oid, query_membership,
    create_account, query_account_by_login, query_accounts_by_person_id,
)
from src.auth.auth import (
    parse_login_name, validate_pid, validate_oid,
    hash_password, verify_password,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    """Register new user and add to organization."""
    # 1. Parse and validate login format
    parsed = parse_login_name(body.login)
    if not parsed:
        raise HTTPException(400, "Invalid login format. Must be {pid}@{oid} or {pid}@{oid}.{suffix}")

    pid, oid = parsed

    # 2. Validate pid and oid format
    if not validate_pid(pid):
        raise HTTPException(400, "Invalid pid format. Only letters, numbers, underscores, hyphens allowed.")
    if not validate_oid(oid):
        raise HTTPException(400, "Invalid oid format. Only letters, numbers, underscores, hyphens allowed.")

    # 3. Check if organization exists
    orgs = query_organization_by_oid(oid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    org = orgs[0]

    # 4. Check if person exists
    persons = query_person_by_pid(pid)

    if persons:
        person = persons[0]
    else:
        # Create new person
        person = create_person(
            name=body.name,
            pid=pid,
        )

    # 5. Check if account exists
    accounts = query_account_by_login(body.login)

    if accounts:
        account = accounts[0]
        # Account exists, verify it belongs to same person
        if account["person_id"] != person["id"]:
            raise HTTPException(409, "Login already taken by another user")
        # Verify password
        if not verify_password(body.password, account["password"], account["salt"]):
            raise HTTPException(409, "Password mismatch for existing user")
    else:
        # Create new account
        hashed_password, salt = hash_password(body.password)
        account = create_account(
            person_id=person["id"],
            login=body.login,
            password=hashed_password,
            salt=salt,
            system_role="user",
        )

    # 6. Check if membership exists
    memberships = query_membership(person["id"], org["id"])

    if memberships:
        membership = memberships[0]
    else:
        # Public registration cannot grant system or organization privileged roles.
        requested_role = (body.role or "member").strip() or "member"
        if requested_role.lower() in {"super", "admin", "owner"}:
            requested_role = "member"
        membership = add_membership(person["id"], org["id"], requested_role)

    # 7. Return result
    return {
        "person": {
            "id": person["id"],
            "pid": person["pid"],
            "name": person["name"]
        },
        "organization": {
            "id": org["id"],
            "oid": org["oid"],
            "name": org["name"],
            "type": org["type"]
        },
        "account": {
            "id": account["id"],
            "login": account["login"],
            "status": account["status"],
            "system_role": account.get("system_role", "user")
        },
        "membership": {
            "role": membership["role"]
        }
    }


@router.post("/login")
async def login(body: LoginRequest):
    """Login user and return JWT token."""
    # 1. Parse login format
    parsed = parse_login_name(body.login)
    if not parsed:
        raise HTTPException(400, "Invalid login format. Must be {pid}@{oid} or {pid}@{oid}.{suffix}")

    pid, oid = parsed

    # 2. Find person and account. The login suffix is presentation only; pid is the
    # stable business identity, so caocao@wei.cn and caocao@wei.com resolve to the same pid/oid.
    persons = query_person_by_pid(pid)
    if not persons:
        raise HTTPException(401, "Invalid credentials")
    person = persons[0]

    accounts = query_account_by_login(body.login)
    if not accounts:
        accounts = query_accounts_by_person_id(person["id"])
    if not accounts:
        raise HTTPException(401, "Invalid credentials")
    account = accounts[0]

    # 3. Check account status
    if account["status"] != "active":
        raise HTTPException(403, "Account is not active")

    # 4. Check if organization exists
    orgs = query_organization_by_oid(oid)
    if not orgs:
        raise HTTPException(401, "Invalid credentials")
    org = orgs[0]

    # 5. Check membership
    memberships = query_membership(person["id"], org["id"])
    if not memberships:
        raise HTTPException(401, "No membership in this organization")
    membership = memberships[0]

    # 6. Verify password
    if not verify_password(body.password, account["password"], account["salt"]):
        raise HTTPException(401, "Invalid password")

    # 7. Create JWT token — only business fields (pid, oid), no numeric DB IDs
    token_data = {
        "pid": person["pid"],
        "person_name": person["name"],
        "oid": org["oid"],
        "organization_name": org["name"],
        "organization_type": org["type"],
        "system_role": account.get("system_role", "user"),
        "role": membership["role"]
    }
    access_token = create_access_token(token_data)

    # 8. Return token and context
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "person": {
            "id": person["id"],
            "pid": person["pid"],
            "name": person["name"]
        },
        "organization": {
            "id": org["id"],
            "oid": org["oid"],
            "name": org["name"],
            "type": org["type"]
        },
        "account": {
            "id": account["id"],
            "login": account["login"],
            "status": account["status"],
            "system_role": account.get("system_role", "user")
        },
        "membership": {
            "role": membership["role"]
        }
    }
