from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from src.models.schemas import SellerPurchaseIn, SellerSalesOut
from src.db.database import (
    execute_purchase_in, execute_sales_out, query_stock, query_inventory_movements,
)
from src.routers.deps import require_strict_org_context

router = APIRouter(prefix="/seller", tags=["seller"])


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
    ctx = require_strict_org_context(request)
    return query_stock(ctx["organization_id"], product_uid=product_uid)


@router.get("/inventory-movements")
async def inventory_movements(
    request: Request, product_uid: Optional[str] = None,
):
    ctx = require_strict_org_context(request)
    return query_inventory_movements(ctx["organization_id"], product_uid=product_uid)
