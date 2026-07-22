"""
Authentication endpoints: register and login.
"""
from fastapi import APIRouter, HTTPException

from src.models.schemas import RegisterRequest, LoginRequest
from src.db.database import (
    create_person, add_membership,
    query_person_by_pid, query_organization_by_oid, query_membership,
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
        # Person exists
        person = persons[0]
        if person.get("password"):
            # Password already set, verify it
            if not verify_password(body.password, person["password"], person["salt"]):
                raise HTTPException(409, "Password mismatch for existing user")
        else:
            # Set password for existing person
            from src.db.database import _execute
            password_hash, salt = hash_password(body.password)
            _execute(
                "UPDATE person SET password = %s, salt = %s WHERE id = %s",
                (password_hash, salt, person["id"])
            )
            person["password"] = password_hash
            person["salt"] = salt
    else:
        # Create new person
        password_hash, salt = hash_password(body.password)
        person = create_person(
            name=body.name,
            pid=person_pid,
            password=password_hash,
            salt=salt
        )

    # 5. Check if membership exists
    memberships = query_membership(person["id"], org["id"])

    if memberships:
        membership = memberships[0]
    else:
        # Create membership
        membership = add_membership(person["id"], org["id"], body.role)

    # 6. Return result
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

    # 2. Check if person exists
    persons = query_person_by_pid(person_pid)
    if not persons:
        raise HTTPException(401, "Invalid credentials")
    person = persons[0]

    # 3. Check if organization exists
    orgs = query_organization_by_oid(org_oid)
    if not orgs:
        raise HTTPException(401, "Invalid credentials")
    org = orgs[0]

    # 4. Check membership
    memberships = query_membership(person["id"], org["id"])
    if not memberships:
        raise HTTPException(401, "No membership in this organization")
    membership = memberships[0]

    # 5. Verify password
    if not person.get("password"):
        raise HTTPException(401, "Password not set for this user")

    if not verify_password(body.password, person["password"], person["salt"]):
        raise HTTPException(401, "Invalid password")

    # 6. Create JWT token
    token_data = {
        "pid": person["id"],
        "person_pid": person["pid"],
        "person_name": person["name"],
        "oid": org["id"],
        "org_oid": org["oid"],
        "org_name": org["name"],
        "org_type": org["type"],
        "role": membership["role"]
    }
    access_token = create_access_token(token_data)

    # 7. Return token and context
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
        "membership": {
            "role": membership["role"]
        }
    }
