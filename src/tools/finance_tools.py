"""Finance tools: record_transaction, get_transaction_history, get_summary."""
from typing import Optional
from langchain_core.tools import tool
import json

from src.db.database import (
    create_transaction,
    get_transactions,
    resolve_organization_id,
    _fetch,
)


@tool
def record_transaction(
    amount: Optional[float] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    oid: str = "shu",
) -> str:
    """
    Record a financial transaction.

    Args:
        amount: Transaction amount (positive).
        category: Transaction category.
        description: Transaction description.
        oid: Organization business identifier, e.g. "shu".
    """
    try:
        if amount is None:
            return "Error: amount is required"
        if not category:
            return "Error: category is required"
        if not description:
            return "Error: description is required"
        if amount <= 0:
            return "Error: Transaction amount must be positive"

        organization_id = resolve_organization_id(oid)
        result = create_transaction(
            amount=amount,
            category=category,
            description=description,
            organization_id=organization_id,
        )
        return json.dumps(result, default=str, ensure_ascii=False)
    except Exception as e:
        return f"Error recording transaction: {e}"


@tool
def get_transaction_history(oid: str = "shu", person_name: Optional[str] = None) -> str:
    """
    Get transaction history for a specific organization.

    Args:
        oid: Organization business identifier, e.g. "shu".
        person_name: Filter by person name (optional; not implemented yet).
    """
    try:
        organization_id = resolve_organization_id(oid)
        txns = get_transactions(organization_id)
        if txns:
            return json.dumps(txns, default=str, ensure_ascii=False)
        return f"No transactions found for org {oid}"
    except Exception as e:
        return f"Error retrieving transaction history: {e}"


@tool
def get_summary(oid: str = "shu") -> str:
    """
    Get financial summary for an organization.

    Args:
        oid: Organization business identifier, e.g. "shu".
    """
    try:
        organization_id = resolve_organization_id(oid)
        outflow_rows = _fetch(
            "SELECT COALESCE(SUM(t.amount), 0) AS total "
            "FROM transaction t "
            "JOIN party p ON p.transaction_id = t.id "
            "WHERE p.organization_id = %s AND p.role = 'payer'",
            (organization_id,),
        )
        total_outflow = float(outflow_rows[0]["total"])

        count_rows = _fetch(
            "SELECT COUNT(DISTINCT t.id) AS cnt "
            "FROM transaction t "
            "JOIN party p ON p.transaction_id = t.id "
            "WHERE p.organization_id = %s",
            (organization_id,),
        )

        summary = {
            "oid": oid,
            "total_outflow": total_outflow,
            "transaction_count": count_rows[0]["cnt"],
        }
        return json.dumps(summary, default=str, ensure_ascii=False)
    except Exception as e:
        return f"Error retrieving financial summary: {e}"
