"""
Shared dependencies for routers.

API-facing identifiers: puid/person_uid and ouid/organization_uid string business keys.
Internal: person_id (person.id), organization_id (organization.id) — numeric DB keys.

JWT payload uses: puid, ouid, system_role, role (strings only)
"""
from typing import Optional, List
from fastapi import Request, HTTPException
from src.auth.auth import decode_access_token


def _enforce_ecommerce_jwt(request: Request, ctx: dict):
    """If org is ecommerce, require JWT with matching ouid.

    Called at every return branch of require_org_context.
    Uses ctx['org_type'] — zero extra DB queries for non-ecommerce orgs.
    """
    if ctx.get("org_type") != "ecommerce":
        return
    token = request.headers.get("Authorization", "")
    if not token.startswith("Bearer "):
        raise HTTPException(401,
            "ecommerce organization requires JWT for all operations")
    payload = get_current_user(request)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    if payload.get("ouid") != ctx.get("ouid"):
        raise HTTPException(403, "JWT organization mismatch")


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
    Require valid JWT or ouid query param and return org context.
    Returns dict with puid/ouid (business IDs) and person_id/organization_id (internal numeric).
    """
    from src.db.database import (
        query_organization_by_ouid, query_person_by_puid, query_membership
    )

    payload = get_current_user(request)

    if payload:
        org_ouid = payload.get("ouid")
        puid = payload.get("puid")

        orgs = query_organization_by_ouid(org_ouid)
        if not orgs:
            raise HTTPException(401, "Invalid organization in token")
        org = orgs[0]

        persons = query_person_by_puid(puid)
        if not persons:
            raise HTTPException(401, "Invalid person in token")
        person = persons[0]

        memberships = query_membership(person["id"], org["id"])
        if not memberships:
            raise HTTPException(403, "No membership in this organization")

        ctx = _build_context(person, org, payload, memberships[0])
        ctx["org_type"] = org["type"]
        _enforce_ecommerce_jwt(request, ctx)
        return ctx

    # Public demo context for non-ecommerce organizations.
    ouid_param = request.query_params.get("ouid")
    if ouid_param is not None:
        orgs = query_organization_by_ouid(ouid_param)
        if orgs:
            org = orgs[0]
            ctx = {
                "puid": None,
                "ouid": org["ouid"],
                "person_id": None,
                "organization_id": org["id"],
                "system_role": "user",
                "role": None,
                "org_type": org["type"],
            }
            _enforce_ecommerce_jwt(request, ctx)
            return ctx

        raise HTTPException(404, "Organization not found")

    raise HTTPException(401, "Authentication required. Provide Bearer token or ouid query parameter.")


def require_strict_org_context(request: Request) -> dict:
    """Require JWT context only; no query-param context."""
    from src.db.database import (
        query_organization_by_ouid, query_person_by_puid, query_membership
    )

    payload = get_current_user(request)
    if not payload:
        raise HTTPException(401, "Authentication required. Provide Bearer token.")

    org_ouid = payload.get("ouid")
    puid = payload.get("puid")
    if not org_ouid or not puid:
        raise HTTPException(401, "JWT must include puid and ouid")

    orgs = query_organization_by_ouid(org_ouid)
    if not orgs:
        raise HTTPException(401, "Invalid organization in token")
    org = orgs[0]

    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(401, "Invalid person in token")
    person = persons[0]

    memberships = query_membership(person["id"], org["id"])
    if not memberships:
        raise HTTPException(403, "No membership in this organization")

    return _build_context(person, org, payload, memberships[0])


def _build_context(person: Optional[dict], org: dict, payload: dict, membership: Optional[dict]) -> dict:
    puid = person.get("puid") if person else None
    ouid = org.get("ouid")
    return {
        "puid": puid,
        "ouid": ouid,
        "person_id": person.get("id") if person else None,
        "organization_id": org["id"],
        "system_role": payload.get("system_role", "user"),
        "role": membership.get("role") if membership else payload.get("role"),
        "org_type": org.get("type"),
        "org_name": org.get("name"),
    }



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
    from src.db.database import query_person_by_puid, _fetch

    if payload.get("system_role") == "super":
        rows = _fetch("SELECT id FROM organization ORDER BY id")
        return [row["id"] for row in rows]

    puid = payload.get("puid")
    if not puid:
        return []
    persons = query_person_by_puid(puid)
    if not persons:
        return []
    rows = _fetch(
        "SELECT organization_id FROM membership WHERE person_id = %s ORDER BY organization_id",
        (persons[0]["id"],)
    )
    return [row["organization_id"] for row in rows]


def is_system_super(payload: dict) -> bool:
    return bool(payload and payload.get("system_role") == "super")
