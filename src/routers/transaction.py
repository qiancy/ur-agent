"""
Transaction endpoints.
"""
from fastapi import APIRouter, Query, Request

from src.models.schemas import TransactionCreate
from src.db.database import create_transaction, get_transactions
from src.routers.deps import require_org_context

router = APIRouter(tags=["transaction"])


@router.get("/transaction")
@router.get("/transactions")
async def list_transaction(request: Request, limit: int = 20):
    ctx = require_org_context(request)
    return get_transactions(ctx["organization_id"], limit=limit)


@router.post("/transaction", status_code=201)
@router.post("/transactions", status_code=201)
async def add_transaction(body: TransactionCreate, request: Request):
    ctx = require_org_context(request)
    return create_transaction(body.amount, body.category, body.description,
                              organization_id=ctx["organization_id"])
