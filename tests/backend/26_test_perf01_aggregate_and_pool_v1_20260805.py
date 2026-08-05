"""PERF-01 contract tests: DB pool controls + aggregate first-screen APIs.

These tests are unit-level by design: no real PostgreSQL and no real LLM.
They guard the product contract without making default pytest depend on the
remote demo database.
"""
import asyncio

import pytest
from fastapi import HTTPException
from psycopg2.pool import PoolError
from starlette.requests import Request


def _request(path: str, query: str = "") -> Request:
    return Request({
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": query.encode("utf-8"),
    })


def test_pool_exhausted_raises_controlled_error(monkeypatch):
    from src.db import database

    class ExhaustedPool:
        def __init__(self, *args, **kwargs):
            pass

        def getconn(self):
            raise PoolError("connection pool exhausted")

        def closeall(self):
            pass

    database.close_connection_pool()
    monkeypatch.setattr(database, "ThreadedConnectionPool", ExhaustedPool)
    with pytest.raises(database.DatabasePoolExhaustedError):
        database.get_pooled_connection()
    database.close_connection_pool()


def test_pool_exhausted_fastapi_handler_returns_503():
    from src.app import database_pool_exhausted_handler
    from src.db.database import DatabasePoolExhaustedError

    response = asyncio.run(database_pool_exhausted_handler(
        _request("/seller/workbench"),
        DatabasePoolExhaustedError("pool exhausted"),
    ))
    assert response.status_code == 503
    assert b"Database is busy" in response.body


def test_seller_workbench_aggregates_business_dtos(monkeypatch):
    from src.routers import seller

    monkeypatch.setattr(seller, "require_ecommerce_context", lambda request: {
        "organization_id": 7,
        "person_id": 3,
        "puid": "zhansan",
        "ouid": "taobao_shop_a",
        "org_type": "ecommerce",
    })
    monkeypatch.setattr(seller, "get_seller_summary", lambda organization_id, **kwargs: {
        "status": "ok",
        "sales_amount": 120,
        "product_count": 2,
    })
    monkeypatch.setattr(seller, "query_stock", lambda organization_id: [{
        "product_uid": "SKU-001",
        "warehouse_code": "WH-A",
        "location_path": "A-01",
        "quantity": 50,
        "unit": "件",
    }])
    monkeypatch.setattr(seller, "query_inventory_movements", lambda organization_id, **kwargs: [{
        "movement_uid": "mv_demo",
        "operation_type": "purchase_in",
        "product_uid": "SKU-001",
        "warehouse_code": "WH-A",
    }])

    result = asyncio.run(seller.seller_workbench(_request("/seller/workbench")))

    assert result["status"] == "ok"
    assert result["summary"]["sales_amount"] == 120
    assert result["stock"][0]["product_uid"] == "SKU-001"
    assert result["movements"][0]["movement_uid"] == "mv_demo"
    for section in ("summary",):
        assert "id" not in result[section]
    for row in result["stock"] + result["movements"]:
        assert "id" not in row
        assert not any(key.endswith("_id") for key in row)


def test_seller_workbench_rejects_identity_query_params():
    from src.routers import seller

    with pytest.raises(HTTPException) as exc:
        asyncio.run(seller.seller_workbench(
            _request("/seller/workbench", "organization_id=1"),
        ))
    assert exc.value.status_code == 400


def test_spaces_dashboard_aggregates_business_dtos(monkeypatch):
    from src.routers import spaces

    monkeypatch.setattr(spaces, "require_strict_org_context", lambda request: {
        "organization_id": 8,
        "puid": "zhansan",
        "ouid": "xinye_campaign",
        "role": "owner",
    })
    monkeypatch.setattr(spaces, "get_space_overview", lambda organization_id, role: {
        "space": {"ouid": "xinye_campaign", "name": "火烧新野战役", "type": "campaign", "role": role},
        "counts": {"resources": 2, "persons": 2, "transactions": 0, "recent_events": 3},
        "funds": 0,
    })
    monkeypatch.setattr(spaces, "get_space_resources", lambda organization_id: {
        "grouped": {"physical": [], "knowledge": [], "financial": [], "human": []},
    })
    monkeypatch.setattr(spaces, "get_space_persons", lambda organization_id: [
        {"name": "诸葛亮", "puid": "zhugeliang", "role": "advisor"},
    ])
    monkeypatch.setattr(spaces, "get_space_transactions", lambda organization_id, limit=20: [])
    monkeypatch.setattr(spaces, "get_space_timeline", lambda organization_id: [
        {"seq": 1, "campaign_code": "fire_xinye", "campaign_name": "火烧新野", "title": "诱敌", "payload": {}},
    ])

    result = asyncio.run(spaces.space_dashboard(_request("/spaces/current/dashboard")))

    assert result["status"] == "ok"
    assert result["overview"]["space"]["ouid"] == "xinye_campaign"
    assert result["persons"][0]["puid"] == "zhugeliang"
    assert result["transactions"] == []
    assert result["timeline"]["events"][0]["campaign_code"] == "fire_xinye"
    assert "id" not in result["overview"]["space"]
    assert not any(key.endswith("_id") for key in result["persons"][0])


def test_spaces_dashboard_rejects_identity_query_params():
    from src.routers import spaces

    with pytest.raises(HTTPException) as exc:
        asyncio.run(spaces.space_dashboard(
            _request("/spaces/current/dashboard", "person_id=1"),
        ))
    assert exc.value.status_code == 400


def test_get_space_resources_batches_physical_locations(monkeypatch):
    from src.db import database

    calls = []

    def fake_fetch(sql, params=()):
        calls.append(sql)
        if "FROM resource r" in sql:
            return [
                {
                    "rid": 101,
                    "name": "军粮",
                    "type": "physical",
                    "unit": "石",
                    "amount": None,
                    "description": "新野守军粮草",
                },
                {
                    "rid": 102,
                    "name": "箭矢",
                    "type": "physical",
                    "unit": "支",
                    "amount": None,
                    "description": "城防箭矢",
                },
                {
                    "rid": 201,
                    "name": "作战纪要",
                    "type": "knowledge",
                    "unit": "份",
                    "amount": None,
                    "description": "战役复盘",
                },
            ]
        if "FROM resource_warehouse rw" in sql:
            assert params == (8, [101, 102])
            return [
                {
                    "rid": 101,
                    "warehouse_code": "DEPOT-A",
                    "location_path": "粮仓-1",
                    "quantity": 1000,
                    "unit": "石",
                },
                {
                    "rid": 102,
                    "warehouse_code": "DEPOT-A",
                    "location_path": "箭库-1",
                    "quantity": 5000,
                    "unit": "支",
                },
            ]
        raise AssertionError(f"unexpected SQL: {sql}")

    monkeypatch.setattr(database, "_fetch", fake_fetch)

    result = database.get_space_resources(8)

    assert len(calls) == 2
    physical = result["grouped"]["physical"]
    assert [item["name"] for item in physical] == ["军粮", "箭矢"]
    assert physical[0]["locations"][0]["warehouse_code"] == "DEPOT-A"
    assert physical[1]["locations"][0]["quantity"] == 5000.0
    assert result["grouped"]["knowledge"][0]["name"] == "作战纪要"
    for item in physical + result["grouped"]["knowledge"]:
        assert "rid" not in item
        assert "id" not in item
