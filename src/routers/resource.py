"""
Resource and resource-warehouse endpoints.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request

from src.models.schemas import ResourceCreate, ResourceWarehouseCreate
from src.db.database import (
    query_resource, create_resource,
    create_resource_warehouse, query_resource_warehouse, get_resource_total,
    query_person_by_pid,
)
from src.routers.deps import require_org_context

router = APIRouter(tags=["resource"])


@router.get("/resource")
@router.get("/assets")
async def list_resource(request: Request, name: Optional[str] = None,
                        resource_type: Optional[str] = None):
    ctx = require_org_context(request)
    return query_resource(ctx["organization_id"], name=name, resource_type=resource_type)


@router.post("/resource", status_code=201)
@router.post("/assets", status_code=201)
async def add_resource(body: ResourceCreate, request: Request):
    ctx = require_org_context(request)
    person_id = None
    if body.pid:
        persons = query_person_by_pid(body.pid)
        if not persons:
            raise HTTPException(404, "Person not found")
        person_id = persons[0]["id"]
    return create_resource(ctx["organization_id"], body.name, body.resource_type,
                           body.unit, body.amount, body.currency,
                           person_id, body.content)


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
