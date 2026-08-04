"""
Organization and membership endpoints.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Request

from src.models.schemas import OrgCreate, MembershipAdd
from src.routers.deps import require_strict_org_context
from src.db.database import (
    create_organization, query_organization,
    add_membership, get_org_members, get_person_memberships,
    query_person_by_puid, query_organization_by_ouid,
)

router = APIRouter(tags=["organization"])


@router.get("/organizations")
async def list_organizations(org_type: Optional[str] = None, name: Optional[str] = None):
    return query_organization(org_type=org_type, name=name)


@router.post("/organizations", status_code=201)
async def add_organization(body: OrgCreate):
    return create_organization(body.name, body.org_type, body.description,
                               body.funds, body.reputation, ouid=body.ouid)


@router.get("/organizations/{ouid}/members")
async def list_org_members(ouid: str):
    orgs = query_organization_by_ouid(ouid)
    if not orgs:
        raise HTTPException(404, "Organization not found")
    return get_org_members(orgs[0]["id"])


@router.post("/organizations/members", status_code=201)
async def add_org_member(body: MembershipAdd, request: Request):
    """Governed member add: caller must be owner/admin of the org (JWT context).

    Only member/viewer roles can be assigned; personal space members cannot be added.
    """
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


@router.get("/persons/{puid}/organizations")
async def list_person_orgs(puid: str):
    persons = query_person_by_puid(puid)
    if not persons:
        raise HTTPException(404, "Person not found")
    return get_person_memberships(persons[0]["id"])
