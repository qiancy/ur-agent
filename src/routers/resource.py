"""
Resource and resource-warehouse endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Query

from src.models.schemas import ResourceCreate, ResourceWarehouseCreate
from src.db.database import (
    query_resource, create_resource,
    create_resource_warehouse, query_resource_warehouse, get_resource_total,
)

router = APIRouter(tags=["resource"])


@router.get("/resource")
@router.get("/assets")
async def list_resource(oid: int = Query(...), name: Optional[str] = None,
                        resource_type: Optional[str] = None):
    return query_resource(oid, name=name, resource_type=resource_type)


@router.post("/resource", status_code=201)
@router.post("/assets", status_code=201)
async def add_resource(body: ResourceCreate):
    return create_resource(body.oid, body.name, body.resource_type,
                           body.unit, body.amount, body.currency,
                           body.pid, body.content)


@router.get("/resource-warehouse")
async def list_resource_warehouse(resource_id: int = Query(...),
                                   location_path: Optional[str] = None):
    return query_resource_warehouse(resource_id, location_path=location_path)


@router.post("/resource-warehouse", status_code=201)
async def add_resource_warehouse(body: ResourceWarehouseCreate):
    return create_resource_warehouse(body.resource_id, body.location_path,
                                     body.quantity, body.unit)


@router.get("/resource-warehouse/total")
async def get_total(resource_id: int = Query(...)):
    return get_resource_total(resource_id)
