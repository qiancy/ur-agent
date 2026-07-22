"""
Summary endpoint.
"""
from fastapi import APIRouter, Query
from src.db.database import _fetch

router = APIRouter(tags=["summary"])


@router.get("/summary")
async def get_summary(oid: int = Query(...)):
    org_rows = _fetch("SELECT funds, reputation FROM organization WHERE id = %s", (oid,))
    if not org_rows:
        return {
            "oid": oid,
            "funds": 0.0,
            "reputation": 0,
            "total_outflow": 0.0,
            "transaction_count": 0,
        }
    org = org_rows[0]

    outflow_rows = _fetch(
        "SELECT COALESCE(SUM(t.amount), 0) AS total "
        "FROM transaction t "
        "JOIN party p ON p.transaction_id = t.id "
        "WHERE p.oid = %s AND p.role = 'payer'", (oid,))
    total_outflow = float(outflow_rows[0]["total"])

    count_rows = _fetch(
        "SELECT COUNT(DISTINCT t.id) AS cnt "
        "FROM transaction t "
        "JOIN party p ON p.transaction_id = t.id "
        "WHERE p.oid = %s", (oid,))

    return {
        "oid": oid,
        "funds": float(org["funds"]),
        "reputation": org["reputation"],
        "total_outflow": total_outflow,
        "transaction_count": count_rows[0]["cnt"],
    }
