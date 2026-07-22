"""
Warehouse endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Query

from src.models.schemas import WarehouseCreate
from src.db.database import create_warehouse, query_warehouse

router = APIRouter(tags=["warehouse"])


@router.get("/warehouse")
@router.get("/warehouses")
async def list_warehouse(oid: int = Query(...), name: Optional[str] = None):
    return query_warehouse(oid, name=name)


@router.post("/warehouse", status_code=201)
@router.post("/warehouses", status_code=201)
async def add_warehouse(body: WarehouseCreate):
    return create_warehouse(body.oid, body.name, body.code,
                           body.location, body.description)
