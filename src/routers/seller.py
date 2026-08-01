import re
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from src.models.schemas import SellerPurchaseIn, SellerSalesOut
from src.db.database import (
    execute_purchase_in, execute_sales_out, query_stock, query_inventory_movements,
    get_seller_summary, query_product_summary,
)
from src.routers.deps import require_strict_org_context

router = APIRouter(prefix="/seller", tags=["seller"])

_IDENTITY_QUERY_PARAMS = {"puid", "ouid"}
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _reject_identity_params(request: Request) -> None:
    """Reject identity/internal-PK query params instead of silently ignoring them.

    Generic rule: bare `id`, any `*_id` (organization_id, person_id,
    resource_id, warehouse_id, transaction_id, resource_warehouse_id,
    inventory_movement_id, ...) and puid/ouid are not accepted in query
    strings. The shop context comes only from the JWT.
    """
    for key in request.query_params:
        key_l = key.lower()
        if key_l == "id" or key_l.endswith("_id") or key_l in _IDENTITY_QUERY_PARAMS:
            raise HTTPException(400, f"Query parameter '{key}' is not allowed")


def _parse_date_param(value: Optional[str], name: str):
    if value is None:
        return None
    if not _DATE_RE.match(value):
        raise HTTPException(422, f"Invalid {name}, expected YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(422, f"Invalid {name}, expected YYYY-MM-DD")


def _validate_date_range(date_from, date_to) -> None:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(422, "date_from must not be after date_to")


@router.post("/purchase-in")
async def purchase_in(body: SellerPurchaseIn, request: Request):
    ctx = require_strict_org_context(request)
    try:
        return execute_purchase_in(
            organization_id=ctx["organization_id"],
            operator_person_id=ctx["person_id"],
            product_uid=body.product_uid,
            warehouse_code=body.warehouse_code,
            location_path=body.location_path,
            quantity=body.quantity,
            unit=body.unit,
            total_amount=body.total_amount,
            counterparty_name=body.counterparty_name,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/sales-out")
async def sales_out(body: SellerSalesOut, request: Request):
    ctx = require_strict_org_context(request)
    try:
        return execute_sales_out(
            organization_id=ctx["organization_id"],
            operator_person_id=ctx["person_id"],
            product_uid=body.product_uid,
            warehouse_code=body.warehouse_code,
            location_path=body.location_path,
            quantity=body.quantity,
            unit=body.unit,
            total_amount=body.total_amount,
            counterparty_name=body.counterparty_name,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/stock")
async def stock(request: Request, product_uid: Optional[str] = None):
    _reject_identity_params(request)
    ctx = require_strict_org_context(request)
    return query_stock(ctx["organization_id"], product_uid=product_uid)


@router.get("/inventory-movements")
async def inventory_movements(
    request: Request,
    product_uid: Optional[str] = None,
    operation_type: Optional[str] = Query(default=None, pattern="^(purchase_in|sales_out)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: Optional[int] = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    _reject_identity_params(request)
    _validate_date_range(_parse_date_param(date_from, "date_from"),
                         _parse_date_param(date_to, "date_to"))
    ctx = require_strict_org_context(request)
    return query_inventory_movements(
        ctx["organization_id"],
        product_uid=product_uid,
        operation_type=operation_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get("/summary")
async def seller_summary(
    request: Request,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    low_stock_threshold: float = Query(default=5, ge=0),
    top_n: int = Query(default=5, ge=1, le=20),
):
    _reject_identity_params(request)
    _validate_date_range(_parse_date_param(date_from, "date_from"),
                         _parse_date_param(date_to, "date_to"))
    ctx = require_strict_org_context(request)
    return get_seller_summary(
        ctx["organization_id"],
        date_from=date_from,
        date_to=date_to,
        low_stock_threshold=low_stock_threshold,
        top_n=top_n,
    )


@router.get("/product-summary")
async def seller_product_summary(
    request: Request,
    product_uid: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    _reject_identity_params(request)
    _validate_date_range(_parse_date_param(date_from, "date_from"),
                         _parse_date_param(date_to, "date_to"))
    ctx = require_strict_org_context(request)
    return query_product_summary(
        ctx["organization_id"],
        product_uid=product_uid,
        date_from=date_from,
        date_to=date_to,
    )
