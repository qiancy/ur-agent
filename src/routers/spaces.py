"""Spaces observation endpoints (BE-10).

Strict JWT only (`require_strict_org_context`) — never accepts ouid/puid query
params. Business-facing DTOs only, no DB numeric ids.
"""
from fastapi import APIRouter, HTTPException, Query, Request

from src.routers.deps import require_strict_org_context
from src.db.database import (
    get_space_overview, get_space_resources, get_space_persons,
    get_space_transactions, get_space_timeline,
)

router = APIRouter(prefix="/spaces", tags=["spaces"])

_IDENTITY_QUERY_PARAMS = {"puid", "ouid"}


def _reject_identity_params(request: Request) -> None:
    """Reject identity/internal-PK query params; context comes only from JWT."""
    for key in request.query_params:
        key_l = key.lower()
        if key_l == "id" or key_l.endswith("_id") or key_l in _IDENTITY_QUERY_PARAMS:
            raise HTTPException(400, f"Query parameter '{key}' is not allowed")


@router.get("/current/overview")
async def space_overview(request: Request):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return get_space_overview(ctx["organization_id"], ctx.get("role"))


@router.get("/current/resources")
async def space_resources(request: Request):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return get_space_resources(ctx["organization_id"])


@router.get("/current/persons")
async def space_persons(request: Request):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return get_space_persons(ctx["organization_id"])


@router.get("/current/transactions")
async def space_transactions(request: Request, limit: int = Query(default=20, ge=1, le=100)):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return get_space_transactions(ctx["organization_id"], limit=limit)


@router.get("/current/timeline")
async def space_timeline(request: Request):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return {"events": get_space_timeline(ctx["organization_id"])}
