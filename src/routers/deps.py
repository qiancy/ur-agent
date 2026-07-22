"""
Shared dependencies for routers.

API-facing identifiers: pid (person.pid), oid (organization.oid) — string business keys.
Internal: person_id (person.id), organization_id (organization.id) — numeric DB keys.

JWT payload uses: pid, oid, system_role, role (strings only)
"""
from typing import Optional, List
from fastapi import Request, HTTPException
from src.auth.auth import decode_access_token


def get_current_user(request: Request) -> Optional[dict]:
    """
    Extract and validate JWT from Authorization header.
    Returns token payload dict or None if no token / invalid token.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    payload = decode_access_token(token)
    return payload


def require_org_context(request: Request) -> dict:
    """
    Require valid JWT or oid query param and return org context.
    Returns:
      - pid: str (person.pid — business identifier)
      - oid: str (organization.oid — business identifier)
      - person_id: int (person.id — internal numeric)
      - organization_id: int (organization.id — internal numeric)
      - role: str
    Falls back to query param 'oid' if no JWT present (backward compat).
    """
    from src.db.database import (
        query_organization_by_oid, query_person_by_pid, query_membership, _fetch
    )

    payload = get_current_user(request)

    if payload:
        org_oid = payload.get("oid")
        pid = payload.get("pid")

        orgs = query_organization_by_oid(org_oid)
        if not orgs:
            raise HTTPException(401, "Invalid organization in token")
        org = orgs[0]

        persons = query_person_by_pid(pid)
        if not persons:
            raise HTTPException(401, "Invalid person in token")
        person = persons[0]

        memberships = query_membership(person["id"], org["id"])
        if not memberships:
            raise HTTPException(403, "No membership in this organization")

        return {
            "pid": person["pid"],
            "oid": org["oid"],
            "person_id": person["id"],
            "organization_id": org["id"],
            "system_role": payload.get("system_role", "user"),
            "role": payload.get("role"),
        }

    # Fallback: oid query param (no auth, backward compat)
    oid_param = request.query_params.get("oid")
    if oid_param is not None:
        # Try numeric id first (backward compat with old tests)
        try:
            numeric_id = int(oid_param)
            rows = _fetch("SELECT * FROM organization WHERE id = %s", (numeric_id,))
            if rows:
                org = rows[0]
                return {
                    "pid": None,
                    "oid": org["oid"],
                    "person_id": None,
                    "organization_id": org["id"],
                    "system_role": "user",
                    "role": None,
                }
        except (ValueError, TypeError):
            pass

        # Try string oid lookup
        orgs = query_organization_by_oid(oid_param)
        if orgs:
            org = orgs[0]
            return {
                "pid": None,
                "oid": org["oid"],
                "person_id": None,
                "organization_id": org["id"],
                "system_role": "user",
                "role": None,
            }

        raise HTTPException(404, "Organization not found")

    raise HTTPException(401, "Authentication required. Provide Bearer token or oid query parameter.")



def require_authenticated(request: Request) -> dict:
    payload = get_current_user(request)
    if not payload:
        raise HTTPException(401, "Authentication required")
    return payload


def require_system_super(request: Request) -> dict:
    payload = require_authenticated(request)
    if payload.get("system_role") != "super":
        raise HTTPException(403, "System super role required")
    return payload


def get_allowed_organization_ids(payload: dict) -> List[int]:
    from src.db.database import query_person_by_pid, _fetch

    if payload.get("system_role") == "super":
        rows = _fetch("SELECT id FROM organization ORDER BY id")
        return [row["id"] for row in rows]

    pid = payload.get("pid")
    if not pid:
        return []
    persons = query_person_by_pid(pid)
    if not persons:
        return []
    rows = _fetch(
        "SELECT organization_id FROM membership WHERE person_id = %s ORDER BY organization_id",
        (persons[0]["id"],)
    )
    return [row["organization_id"] for row in rows]


def is_system_super(payload: dict) -> bool:
    return bool(payload and payload.get("system_role") == "super")
