"""
Transaction endpoints.
"""
from fastapi import APIRouter, Query

from src.models.schemas import TransactionCreate
from src.db.database import create_transaction, get_transactions

router = APIRouter(tags=["transaction"])


@router.get("/transaction")
@router.get("/transactions")
async def list_transaction(oid: int = Query(...), limit: int = 20):
    return get_transactions(oid, limit=limit)


@router.post("/transaction", status_code=201)
@router.post("/transactions", status_code=201)
async def add_transaction(body: TransactionCreate):
    return create_transaction(body.amount, body.category, body.description)
