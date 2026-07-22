"""
Organization and membership endpoints.
"""
from typing import Optional
from fastapi import APIRouter

from src.models.schemas import OrgCreate, MembershipAdd
from src.db.database import (
    create_organization, query_organization,
    add_membership, get_org_members, get_person_memberships,
)

router = APIRouter(tags=["organization"])


@router.get("/organizations")
async def list_organizations(org_type: Optional[str] = None, name: Optional[str] = None):
    return query_organization(org_type=org_type, name=name)


@router.post("/organizations", status_code=201)
async def add_organization(body: OrgCreate):
    return create_organization(body.name, body.org_type, body.description,
                               body.funds, body.reputation, oid=body.oid)


@router.get("/organizations/{oid}/members")
async def list_org_members(oid: int):
    return get_org_members(oid)


@router.post("/organizations/members", status_code=201)
async def add_org_member(body: MembershipAdd):
    return add_membership(body.pid, body.oid, body.role)


@router.get("/persons/{pid}/organizations")
async def list_person_orgs(pid: int):
    return get_person_memberships(pid)
