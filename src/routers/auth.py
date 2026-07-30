"""
Authentication endpoints: register and login.
"""
from fastapi import APIRouter, HTTPException

from src.models.schemas import RegisterRequest, LoginRequest
from src.db.database import (
    create_person, add_membership,
    query_person_by_puid, query_organization_by_ouid, query_membership,
    create_account, query_account_by_login, query_accounts_by_person_id,
)
from src.auth.auth import (
    parse_login_name, validate_puid, validate_ouid,
    hash_password, verify_password,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_token(person: dict, org: dict, account: dict, membership: dict) -> str:
    token_data = {
        "puid": person["puid"],
        "person_name": person["name"],
        "ouid": org["ouid"],
        "organization_name": org["name"],
        "organization_type": org["type"],
        "system_role": account.get("system_role", "user"),
        "role": membership["role"]
    }
    return create_access_token(token_data)


def _authenticate_login(body: LoginRequest):
    parsed = parse_login_name(body.login)
    if not parsed:
        raise HTTPException(400, "Invalid login format. Must be {puid}@{ouid} or {puid}@{ouid}.{suffix}")

    puid, ouid = parsed

    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid credentials")
    person = persons[0]

    accounts = query_account_by_login(body.login)
    if not accounts:
        accounts = query_accounts_by_person_id(person["id"])
    if not accounts:
        raise HTTPException(401, "Invalid credentials")
    account = accounts[0]

    if account["status"] != "active":
        raise HTTPException(403, "Account is not active")

    orgs = query_organization_by_ouid(ouid)
    if not orgs:
        raise HTTPException(401, "Invalid credentials")
    org = orgs[0]

    memberships = query_membership(person["id"], org["id"])
    if not memberships:
        raise HTTPException(401, "No membership in this organization")
    membership = memberships[0]

    if not verify_password(body.password, account["password"], account["salt"]):
        raise HTTPException(401, "Invalid password")

    return person, org, account, membership


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    """Register new user and add to organization."""
    # 1. Parse and validate login format
    parsed = parse_login_name(body.login)
    if not parsed:
        raise HTTPException(400, "Invalid login format. Must be {puid}@{ouid} or {puid}@{ouid}.{suffix}")

    puid, ouid = parsed

    # 2. Validate puid and ouid format
    if not validate_puid(puid):
        raise HTTPException(400, "Invalid puid format. Only letters, numbers, underscores, hyphens allowed.")
    if not validate_ouid(ouid):
        raise HTTPException(400, "Invalid ouid format. Only letters, numbers, underscores, hyphens allowed.")

    # 3. Check if organization exists
    orgs = query_organization_by_ouid(ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    org = orgs[0]

    # 4. Check if person exists
    persons = query_person_by_puid(puid)

    if persons:
        person = persons[0]
    else:
        # Create new person
        person = create_person(
            name=body.name,
            puid=puid,
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

    # 7. Return result (no database numeric IDs in public API)
    return {
        "person": {
            "puid": person["puid"],
            "name": person["name"]
        },
        "organization": {
            "ouid": org["ouid"],
            "name": org["name"],
            "type": org["type"]
        },
        "account": {
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
    person, org, account, membership = _authenticate_login(body)
    access_token = _build_token(person, org, account, membership)

    # 8. Return token and context (no database numeric IDs in public API)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "person": {
            "puid": person["puid"],
            "name": person["name"]
        },
        "organization": {
            "ouid": org["ouid"],
            "name": org["name"],
            "type": org["type"]
        },
        "account": {
            "login": account["login"],
            "status": account["status"],
            "system_role": account.get("system_role", "user")
        },
        "membership": {
            "role": membership["role"]
        }
    }


@router.post("/seller-login")
async def seller_login(body: LoginRequest):
    """Seller login response with no database numeric IDs."""
    person, org, account, membership = _authenticate_login(body)
    access_token = _build_token(person, org, account, membership)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "person": {
            "puid": person["puid"],
            "name": person["name"]
        },
        "organization": {
            "ouid": org["ouid"],
            "name": org["name"],
            "type": org["type"]
        },
        "membership": {
            "role": membership["role"]
        },
        "system_role": account.get("system_role", "user"),
    }
