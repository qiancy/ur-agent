import re
import asyncio
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from starlette.concurrency import run_in_threadpool

from src.models.schemas import (
    SellerPurchaseIn, SellerSalesOut, SellerChatRequest,
    SellerProductCreate, SellerProductStatus,
)
from src.db.database import (
    execute_purchase_in, execute_sales_out, query_stock, query_inventory_movements,
    get_seller_summary, query_product_summary,
    list_seller_products, create_seller_product, set_seller_product_status,
)
from src.routers.deps import require_ecommerce_context
from src.agents.seller_agent import create_seller_agent
from src.tools.seller_tools import make_seller_tools
from langchain_core.messages import HumanMessage

router = APIRouter(prefix="/seller", tags=["seller"])

_IDENTITY_QUERY_PARAMS = {"puid", "ouid"}
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_WRITE_INTENT_PHRASES = (
    "帮我入库", "帮我采购入库", "帮我进货",
    "帮我出库", "帮我卖出", "帮我卖", "帮我买",
    "修改库存", "调整库存", "改库存",
    "创建", "新增", "删除", "记录一笔",
)
_READ_INTENT_EXCLUSIONS = (
    "支出", "流水", "统计", "查询", "列表", "金额", "汇总", "余额", "多少",
)
_IDENTITY_MARKERS = ("我是谁", "当前空间", "当前店铺")


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
    ctx = require_ecommerce_context(request)
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
    ctx = require_ecommerce_context(request)
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
    ctx = require_ecommerce_context(request)
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
    ctx = require_ecommerce_context(request)
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
    ctx = require_ecommerce_context(request)
    return get_seller_summary(
        ctx["organization_id"],
        date_from=date_from,
        date_to=date_to,
        low_stock_threshold=low_stock_threshold,
        top_n=top_n,
    )


@router.get("/workbench")
async def seller_workbench(
    request: Request,
    movements_limit: int = Query(default=10, ge=1, le=50),
    low_stock_threshold: float = Query(default=5, ge=0),
    top_n: int = Query(default=5, ge=1, le=20),
):
    _reject_identity_params(request)
    ctx = require_ecommerce_context(request)
    organization_id = ctx["organization_id"]
    summary, stock_rows, movements = await asyncio.gather(
        run_in_threadpool(
            get_seller_summary,
            organization_id,
            low_stock_threshold=low_stock_threshold,
            top_n=top_n,
        ),
        run_in_threadpool(query_stock, organization_id),
        run_in_threadpool(
            query_inventory_movements,
            organization_id,
            limit=movements_limit,
        ),
    )
    return {
        "status": "ok",
        "summary": summary,
        "stock": stock_rows,
        "movements": movements,
    }


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
    ctx = require_ecommerce_context(request)
    return query_product_summary(
        ctx["organization_id"],
        product_uid=product_uid,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/products")
async def seller_products(request: Request):
    _reject_identity_params(request)
    ctx = require_ecommerce_context(request)
    return list_seller_products(ctx["organization_id"])


@router.post("/products", status_code=201)
async def seller_create_product(body: SellerProductCreate, request: Request):
    ctx = require_ecommerce_context(request)
    try:
        return create_seller_product(
            ctx["organization_id"],
            product_uid=body.product_uid,
            unit=body.unit,
            description=body.description,
        )
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.patch("/products/{product_uid}")
async def seller_patch_product(product_uid: str, body: SellerProductStatus,
                               request: Request):
    ctx = require_ecommerce_context(request)
    try:
        return set_seller_product_status(
            ctx["organization_id"], product_uid, body.status,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


def _is_write_intent(message: str) -> bool:
    """Write-intent detection: write verb phrase minus read-intent nouns."""
    if not any(p in message for p in _WRITE_INTENT_PHRASES):
        return False
    if any(w in message for w in _READ_INTENT_EXCLUSIONS):
        return False
    return True


_READ_ONLY_NOTICE = (
    "当前版本的 Seller AI 只支持经营查询，不能代你执行入库、出库、"
    "修改库存或创建记录。请使用人工操作入口完成写入。"
)


@router.post("/chat")
async def seller_chat(body: SellerChatRequest, request: Request):
    ctx = require_ecommerce_context(request)

    _reject_identity_params(request)

    message = body.message.strip()
    if not message:
        raise HTTPException(422, "message must not be empty")

    ouid = ctx["ouid"]

    if any(marker in message for marker in _IDENTITY_MARKERS):
        return {
            "response": f"当前店铺：{ctx.get('org_name', '')}，"
                        f"组织标识：{ouid}，当前用户：{ctx.get('puid', '')}。",
            "ouid": ouid,
        }

    if _is_write_intent(message):
        return {"response": _READ_ONLY_NOTICE, "ouid": ouid}

    try:
        tools = make_seller_tools(ctx["organization_id"])
        graph = create_seller_agent(tools)
        result = graph.invoke({"messages": [HumanMessage(content=message)]})
        output = result["messages"][-1].content if result.get("messages") else ""
        return {"response": output, "ouid": ouid}
    except TimeoutError:
        raise HTTPException(504, "AI 处理超时，请稍后重试")
    except Exception:
        raise HTTPException(502, "AI 处理失败，请稍后重试")
