"""
Warehouse endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Query, Request

from src.models.schemas import WarehouseCreate
from src.db.database import create_warehouse, query_warehouse
from src.routers.deps import require_org_context

router = APIRouter(tags=["warehouse"])


@router.get("/warehouse")
@router.get("/warehouses")
async def list_warehouse(request: Request, name: Optional[str] = None):
    ctx = require_org_context(request)
    return query_warehouse(ctx["organization_id"], name=name)


@router.post("/warehouse", status_code=201)
@router.post("/warehouses", status_code=201)
async def add_warehouse(body: WarehouseCreate, request: Request):
    ctx = require_org_context(request)
    return create_warehouse(ctx["organization_id"], body.name, body.code,
                           body.location, body.description)
