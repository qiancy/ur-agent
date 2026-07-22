"""
Person endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Query

from src.models.schemas import PersonCreate
from src.db.database import query_person, create_person

router = APIRouter(tags=["person"])


@router.get("/person")
@router.get("/personnel")
async def list_person(oid: int = Query(...), name: Optional[str] = None):
    return query_person(oid, name=name)


@router.post("/person", status_code=201)
@router.post("/personnel", status_code=201)
async def add_person(body: PersonCreate):
    return create_person(body.name, body.birth_date)
