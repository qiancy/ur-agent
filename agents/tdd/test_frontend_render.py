"""BE-05 前端展示层纯函数单测（无 DB、无 HTTP）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.frontend import (
    _fmt_num, _money, _seller_metrics_html, _filter_stock,
    _seller_stock_html, _seller_low_html, _seller_status_text,
)

FORBIDDEN = {
    "id", "person_id", "organization_id", "resource_id",
    "warehouse_id", "transaction_id", "pid", "oid",
}


def _summary(**overrides):
    data = {
        "sales_amount": 12840.0,
        "purchase_amount": 7260.0,
        "net_cash_flow": 5580.0,
        "movement_count": 18,
        "product_count": 6,
        "estimated_inventory_value": 48930.0,
        "valuation_method": "purchase_avg",
        "low_stock_items": [
            {"product_uid": "usb_cable_1m", "quantity": 4, "unit": "件"},
            {"product_uid": "charger_20w", "quantity": 2, "unit": "件"},
        ],
        "top_products_by_sales": [],
    }
    data.update(overrides)
    return data


def _stock_rows():
    return [
        {"product_uid": "phone_case_black", "warehouse_code": "WH-A",
         "location_path": "A-01-03", "quantity": 42, "unit": "件"},
        {"product_uid": "usb_cable_1m", "warehouse_code": "WH-A",
         "location_path": "A-02-01", "quantity": 4, "unit": "件"},
        {"product_uid": "charger_20w", "warehouse_code": "WH-B",
         "location_path": "B-01-08", "quantity": 11, "unit": "件"},
    ]


def test_metrics_html_contains_five_cards():
    html = _seller_metrics_html(_summary())
    for label in ("销售收入", "采购支出", "净现金流", "库存估值", "低库存"):
        assert label in html
    assert "¥12,840" in html
    assert "2" in html


def test_metrics_html_has_no_db_ids():
    html = _seller_metrics_html(_summary())
    for key in FORBIDDEN:
        assert key not in html


def test_stock_html_tags_low_stock():
    low_set = {"usb_cable_1m", "charger_20w"}
    html = _seller_stock_html(_stock_rows(), low_set)
    assert "phone_case_black" in html
    assert '<span class="be05-tag low">低库存</span>' in html
    assert '<span class="be05-tag ok">充足</span>' in html


def test_stock_html_has_no_db_ids():
    html = _seller_stock_html(_stock_rows(), set())
    for key in FORBIDDEN:
        assert key not in html


def test_filter_stock_warehouse():
    rows = _filter_stock(_stock_rows(), warehouse="WH-B")
    assert [r["product_uid"] for r in rows] == ["charger_20w"]


def test_filter_stock_only_low():
    rows = _filter_stock(_stock_rows(), only_low=True, low_set={"usb_cable_1m"})
    assert [r["product_uid"] for r in rows] == ["usb_cable_1m"]


def test_low_html_contains_items_and_no_ids():
    html = _seller_low_html(_summary())
    assert "usb_cable_1m" in html and "charger_20w" in html
    for key in FORBIDDEN:
        assert key not in html


def test_status_text_counts_low():
    text = _seller_status_text(_summary())
    assert "2 个低库存商品" in text


def test_fmt_num_none_and_decimal():
    assert _fmt_num(None) == "-"
    assert _fmt_num(12840.0) == "12,840"
    assert _fmt_num(5580.5) == "5,580.50"


def test_money_prefix():
    assert _money(12840.0) == "¥12,840"
    assert _money(None) == "-"
