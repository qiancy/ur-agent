"""
Summary endpoint.
"""
from fastapi import APIRouter, Request
from src.db.database import _fetch
from src.routers.deps import require_org_context

router = APIRouter(tags=["summary"])


@router.get("/summary")
async def get_summary(request: Request):
    ctx = require_org_context(request)
    org_id = ctx["organization_id"]
    org_rows = _fetch("SELECT funds, reputation FROM organization WHERE id = %s", (org_id,))
    if not org_rows:
        return {
            "ouid": ctx["ouid"],
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
        "WHERE p.organization_id = %s AND p.role = 'payer'", (org_id,))
    total_outflow = float(outflow_rows[0]["total"])

    count_rows = _fetch(
        "SELECT COUNT(DISTINCT t.id) AS cnt "
        "FROM transaction t "
        "JOIN party p ON p.transaction_id = t.id "
        "WHERE p.organization_id = %s", (org_id,))

    return {
        "ouid": ctx["ouid"],
        "funds": float(org["funds"]),
        "reputation": org["reputation"],
        "total_outflow": total_outflow,
        "transaction_count": count_rows[0]["cnt"],
    }
