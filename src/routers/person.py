"""
Person endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Query, Request

from src.models.schemas import PersonCreate
from src.db.database import query_person, create_person
from src.routers.deps import require_org_context

router = APIRouter(tags=["person"])


@router.get("/person")
@router.get("/personnel")
async def list_person(request: Request, name: Optional[str] = None):
    ctx = require_org_context(request)
    return query_person(ctx["organization_id"], name=name)


@router.post("/person", status_code=201)
@router.post("/personnel", status_code=201)
async def add_person(body: PersonCreate):
    return create_person(body.name, body.birth_date)
