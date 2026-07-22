"""
Authentication endpoints: register and login.
"""
from fastapi import APIRouter, HTTPException

from src.models.schemas import RegisterRequest, LoginRequest
from src.db.database import (
    create_person, add_membership,
    query_person_by_pid, query_organization_by_oid, query_membership,
    create_account, query_account_by_login,
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
        raise HTTPException(400, "Invalid login format. Must be {pid}@{oid}.cn")

    person_pid, org_oid = parsed

    # 2. Validate pid and oid format
    if not validate_pid(person_pid):
        raise HTTPException(400, "Invalid pid format. Only letters, numbers, underscores, hyphens allowed.")
    if not validate_oid(org_oid):
        raise HTTPException(400, "Invalid oid format. Only letters, numbers, underscores, hyphens allowed.")

    # 3. Check if organization exists
    orgs = query_organization_by_oid(org_oid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    org = orgs[0]

    # 4. Check if person exists
    persons = query_person_by_pid(person_pid)

    if persons:
        person = persons[0]
    else:
        # Create new person
        person = create_person(
            name=body.name,
            pid=person_pid,
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
        password_hash, salt = hash_password(body.password)
        account = create_account(
            person_id=person["id"],
            login=body.login,
            password=password_hash,
            salt=salt,
        )

    # 6. Check if membership exists
    memberships = query_membership(person["id"], org["id"])

    if memberships:
        membership = memberships[0]
    else:
        # Create membership
        membership = add_membership(person["id"], org["id"], body.role)

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
            "status": account["status"]
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
        raise HTTPException(400, "Invalid login format. Must be {pid}@{oid}.cn")

    person_pid, org_oid = parsed

    # 2. Check if account exists
    accounts = query_account_by_login(body.login)
    if not accounts:
        raise HTTPException(401, "Invalid credentials")
    account = accounts[0]

    # 3. Check account status
    if account["status"] != "active":
        raise HTTPException(403, "Account is not active")

    # 4. Get person via account.person_id
    from src.db.database import _fetch
    persons = _fetch("SELECT * FROM person WHERE id = %s", (account["person_id"],))
    if not persons:
        raise HTTPException(401, "Invalid credentials")
    person = persons[0]

    # 5. Verify person_pid matches
    if person["pid"] != person_pid:
        raise HTTPException(401, "Invalid credentials")

    # 6. Check if organization exists
    orgs = query_organization_by_oid(org_oid)
    if not orgs:
        raise HTTPException(401, "Invalid credentials")
    org = orgs[0]

    # 7. Check membership
    memberships = query_membership(person["id"], org["id"])
    if not memberships:
        raise HTTPException(401, "No membership in this organization")
    membership = memberships[0]

    # 8. Verify password
    if not verify_password(body.password, account["password"], account["salt"]):
        raise HTTPException(401, "Invalid password")

    # 9. Create JWT token
    token_data = {
        "pid": person["id"],
        "person_pid": person["pid"],
        "person_name": person["name"],
        "oid": org["id"],
        "org_oid": org["oid"],
        "org_name": org["name"],
        "org_type": org["type"],
        "account_id": account["id"],
        "role": membership["role"]
    }
    access_token = create_access_token(token_data)

    # 10. Return token and context
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
            "status": account["status"]
        },
        "membership": {
            "role": membership["role"]
        }
    }
