"""
Party endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Query

from src.models.schemas import PartyCreate
from src.db.database import query_party, create_party, query_party_by_transaction

router = APIRouter(tags=["party"])


@router.get("/party")
async def list_party(oid: int = Query(...), pid: Optional[int] = None,
                     name: Optional[str] = None):
    return query_party(oid, pid=pid, name=name)


@router.get("/party/transaction/{transaction_id}")
async def list_party_by_transaction(transaction_id: int):
    return query_party_by_transaction(transaction_id)


@router.post("/party", status_code=201)
async def add_party(body: PartyCreate):
    return create_party(body.pid, body.oid, body.transaction_id,
                        body.role, body.description,
                        body.funds_change, body.reputation_change)
