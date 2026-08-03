"""
Authentication endpoints: register, login, organization switch.

AUTH-02 model: account.login is the single login credential. A user logs in
once and switches between organizations through membership + JWT re-issue.
login is NEVER parsed as puid/ouid context.
"""
from fastapi import APIRouter, HTTPException, Request

from src.models.schemas import RegisterRequest, LoginRequest, SwitchOrganizationRequest
from src.db.database import (
    query_person_by_puid, query_organization_by_ouid, query_membership,
    query_account_by_login, list_person_organizations,
)
from src.auth.auth import (
    validate_puid, derive_puid_from_login,
    verify_password,
    create_access_token,
)
from src.routers.deps import require_authenticated

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


def _orgs_dto(person: dict) -> list:
    """Business-facing organization list for a person (no DB ids)."""
    return [
        {"ouid": r["ouid"], "name": r["name"], "type": r["type"], "role": r["role"]}
        for r in list_person_organizations(person["id"])
    ]


def _context_dto(person: dict, org: dict, account: dict, membership: dict) -> dict:
    return {
        "access_token": _build_token(person, org, account, membership),
        "token_type": "bearer",
        "person": {"puid": person["puid"], "name": person["name"]},
        "organization": {"ouid": org["ouid"], "name": org["name"], "type": org["type"]},
        "account": {
            "login": account["login"],
            "status": account["status"],
            "system_role": account.get("system_role", "user"),
        },
        "membership": {"role": membership["role"]},
        "organizations": _orgs_dto(person),
        "requires_organization": False,
    }


def _requires_org_dto(person: dict, account: dict) -> dict:
    return {
        "access_token": None,
        "token_type": None,
        "person": {"puid": person["puid"], "name": person["name"]},
        "account": {
            "login": account["login"],
            "status": account["status"],
            "system_role": account.get("system_role", "user"),
        },
        "organizations": [],
        "requires_organization": True,
    }


def _load_person_for_account(account: dict) -> dict:
    """Load person by account.person_id (business fields only)."""
    from src.db.database import _fetch
    rows = _fetch("SELECT * FROM person WHERE id = %s", (account["person_id"],))
    if not rows:
        raise HTTPException(401, "Invalid account binding")
    return rows[0]


def _authenticate_account(login: str, password: str):
    """Authenticate by account.login only; login is never parsed as ouid.

    Returns (account, person) or raises.
    """
    accounts = query_account_by_login(login)
    if not accounts:
        raise HTTPException(401, "Invalid credentials")
    account = accounts[0]

    if account["status"] != "active":
        raise HTTPException(403, "Account is not active")

    if not verify_password(password, account["password"], account["salt"]):
        raise HTTPException(401, "Invalid password")

    person = _load_person_for_account(account)
    return account, person


def _resolve_default_org(person: dict, organizations: list):
    """Pick the default organization from a stable server-side order.

    Returns (org, membership) for the first active membership.
    """
    orgs = query_organization_by_ouid(organizations[0]["ouid"])
    if not orgs:
        raise HTTPException(401, "Invalid organization in membership")
    org = orgs[0]
    memberships = query_membership(person["id"], org["id"])
    if not memberships:
        raise HTTPException(401, "Invalid membership")
    return org, memberships[0]


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    """Create account + person + personal space atomically.

    Registration always yields a personal space (owner) and its JWT.
    Public registration never grants privileged roles (system_role stays 'user').
    Joining another org now happens only via invite / join request, never at
    registration (no initial-org membership on register).
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


def _accounts_of(person_id: int) -> list:
    from src.db.database import _fetch
    return _fetch("SELECT * FROM account WHERE person_id = %s", (person_id,))


@router.post("/login")
async def login(body: LoginRequest):
    """Login by account.login; returns default space + switchable organizations."""
    account, person = _authenticate_account(body.login, body.password)
    organizations = _orgs_dto(person)
    if not organizations:
        return _requires_org_dto(person, account)
    org, membership = _resolve_default_org(person, organizations)
    return _context_dto(person, org, account, membership)


@router.post("/seller-login")
async def seller_login(body: LoginRequest):
    """Alias of /auth/login sharing the same single-account authentication."""
    return await login(body)


@router.get("/me/organizations")
async def my_organizations(request: Request):
    """List the current user's organizations (business fields only)."""
    if request.query_params.get("puid") is not None or request.query_params.get("ouid") is not None:
        raise HTTPException(
            400, "puid/ouid query parameters are not accepted here")
    payload = require_authenticated(request)
    puid = payload.get("puid")
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    return _orgs_dto(persons[0])


@router.post("/switch-organization")
async def switch_organization(body: SwitchOrganizationRequest, request: Request):
    """Re-issue a JWT scoped to a target organization the user belongs to."""
    payload = require_authenticated(request)
    puid = payload.get("puid")
    if not puid:
        raise HTTPException(401, "JWT must include puid")

    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    person = persons[0]

    orgs = query_organization_by_ouid(body.ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    org = orgs[0]

    memberships = query_membership(person["id"], org["id"])
    if not memberships:
        raise HTTPException(403, "No membership in this organization")
    membership = memberships[0]

    from src.db.database import _fetch
    accounts = _fetch("SELECT * FROM account WHERE person_id = %s ORDER BY id",
                      (person["id"],))
    account = accounts[0] if accounts else {
        "system_role": payload.get("system_role", "user"),
        "login": payload.get("puid"), "status": "active",
    }
    return _context_dto(person, org, account, membership)
