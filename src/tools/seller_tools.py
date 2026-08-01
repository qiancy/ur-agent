"""
Seller read-only LangChain tools for POST /seller/chat.

The shop context (``shop_key`` = internal organization PK) is bound into each
tool via closure and is passed positionally to DB helpers only. Tool schemas
exposed to the model contain business query parameters only — no identity
fields, no bare ``id``, no ``*_id``, no ``pid``/``oid``.

Outputs are JSON text with ``ensure_ascii=False`` and zero DB numeric PKs.
Failures return a safe error text without leaking SQL/connection details.
"""
import json
import re
from typing import Optional

from langchain_core.tools import tool

from src.db.database import (
    query_stock,
    query_inventory_movements,
    get_seller_summary,
    query_product_summary,
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _check_date(value: Optional[str], name: str) -> None:
    if value is not None and not _DATE_RE.match(value):
        raise ValueError(f"{name} 格式应为 YYYY-MM-DD")


def make_seller_tools(shop_key: int) -> list:
    """Create the Seller read-only tool set bound to ``shop_key``.

    ``shop_key`` is an internal database key used only inside the closure;
    it never appears in a tool schema or output.
    """

    @tool
    def seller_stock(product_uid: Optional[str] = None) -> str:
        """查询当前库存。可按商品编号（product_uid）过滤，否则返回全部商品库存。"""
        try:
            rows = query_stock(shop_key, product_uid)
            return json.dumps(rows, ensure_ascii=False, default=str)
        except Exception:
            return "查询失败: 库存查询失败，请稍后重试"

    @tool
    def seller_summary(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        low_stock_threshold: float = 5,
        top_n: int = 5,
    ) -> str:
        """查询店铺经营摘要：销售收入、采购支出、净现金流、库存估值、低库存、热销商品。

        日期可选，格式 YYYY-MM-DD。"""
        try:
            _check_date(date_from, "date_from")
            _check_date(date_to, "date_to")
            data = get_seller_summary(
                shop_key, date_from, date_to, low_stock_threshold, top_n,
            )
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception:
            return "查询失败: 经营摘要查询失败，请稍后重试"

    @tool
    def seller_product_summary(
        product_uid: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> str:
        """查询商品维度的经营汇总：采购/销售数量与金额。日期可选，格式 YYYY-MM-DD。"""
        try:
            _check_date(date_from, "date_from")
            _check_date(date_to, "date_to")
            data = query_product_summary(shop_key, product_uid, date_from, date_to)
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception:
            return "查询失败: 商品经营汇总查询失败，请稍后重试"

    @tool
    def seller_inventory_movements(
        product_uid: Optional[str] = None,
        operation_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> str:
        """查询库存流水。可按商品、操作类型（purchase_in/sales_out）、日期过滤，并可限制条数。"""
        try:
            _check_date(date_from, "date_from")
            _check_date(date_to, "date_to")
            rows = query_inventory_movements(
                shop_key, product_uid, operation_type,
                date_from, date_to, limit, offset,
            )
            return json.dumps(rows, ensure_ascii=False, default=str)
        except Exception:
            return "查询失败: 库存流水查询失败，请稍后重试"

    return [seller_stock, seller_summary, seller_product_summary, seller_inventory_movements]
