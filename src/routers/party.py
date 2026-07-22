"""
Party endpoints.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request

from src.models.schemas import PartyCreate
from src.db.database import (
    query_party, create_party, query_party_by_transaction,
    query_person_by_pid, query_membership,
)
from src.routers.deps import require_org_context

router = APIRouter(tags=["party"])


@router.get("/party")
async def list_party(request: Request, name: Optional[str] = None):
    ctx = require_org_context(request)
    return query_party(ctx["organization_id"], name=name)


@router.get("/party/transaction/{transaction_id}")
async def list_party_by_transaction(transaction_id: int):
    return query_party_by_transaction(transaction_id)


@router.post("/party", status_code=201)
async def add_party(body: PartyCreate, request: Request):
    ctx = require_org_context(request)
    person_id = ctx["person_id"]

    if body.pid:
        persons = query_person_by_pid(body.pid)
        if not persons:
            raise HTTPException(404, "Person not found")
        person_id = persons[0]["id"]
        if not query_membership(person_id, ctx["organization_id"]):
            raise HTTPException(403, "Person is not a member of this organization")
    elif person_id is None:
        raise HTTPException(400, "pid is required when no Bearer token is provided")

    return create_party(
        person_id=person_id,
        organization_id=ctx["organization_id"],
        transaction_id=body.transaction_id,
        role=body.role,
        description=body.description,
        funds_change=body.funds_change,
        reputation_change=body.reputation_change,
    )
