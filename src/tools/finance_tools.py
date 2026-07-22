"""Finance tools: record_transaction, get_transaction_history, get_summary."""
from typing import Optional
from langchain_core.tools import tool
import json

from src.db.database import (
    create_transaction,
    get_transactions,
    _fetch,
)


@tool
def record_transaction(
    amount: Optional[float] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    oid: int = 1,
) -> str:
    """
    Record a financial transaction.

    Args:
        amount: Transaction amount (positive).
        category: Transaction category (e.g. '军费', '俸禄', '军需').
        description: Transaction description.

    Returns:
        Transaction confirmation as JSON or error message.
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
        
        result = create_transaction(
            amount=amount,
            category=category,
            description=description,
            oid=oid,
        )
        return json.dumps(result, default=str, ensure_ascii=False)
    except Exception as e:
        return f"Error recording transaction: {e}"


@tool
def get_transaction_history(
    oid: int = 1,
    person_name: Optional[str] = None
) -> str:
    """
    Get transaction history for a specific organization.

    Args:
        oid: Organization identifier for multi-tenant isolation.
        person_name: Filter by person name (optional).

    Returns:
        JSON string with transaction history or error message.
    """
    try:
        if not isinstance(oid, int):
            try:
                oid = int(oid)
            except (ValueError, TypeError):
                return "Error: oid must be an integer"
        
        txns = get_transactions(oid)
        if txns:
            return json.dumps(txns, default=str, ensure_ascii=False)
        return f"No transactions found for org {oid}"
    except Exception as e:
        return f"Error retrieving transaction history: {e}"


@tool
def get_summary(oid: int = 1) -> str:
    """
    Get financial summary: total outflow and transaction count for an organization.

    Args:
        oid: Organization identifier for multi-tenant isolation. Default: 1 (蜀国).

    Returns:
        JSON string with financial summary.
    """
    try:
        outflow_rows = _fetch(
            "SELECT COALESCE(SUM(t.amount), 0) AS total "
            "FROM transaction t "
            "JOIN party p ON p.transaction_id = t.id "
            "WHERE p.oid = %s AND p.role = 'payer'",
            (oid,),
        )
        total_outflow = float(outflow_rows[0]["total"])

        count_rows = _fetch(
            "SELECT COUNT(DISTINCT t.id) AS cnt "
            "FROM transaction t "
            "JOIN party p ON p.transaction_id = t.id "
            "WHERE p.oid = %s",
            (oid,),
        )

        summary = {
            "oid": oid,
            "total_outflow": total_outflow,
            "transaction_count": count_rows[0]["cnt"],
        }
        return json.dumps(summary, default=str, ensure_ascii=False)
    except Exception as e:
        return f"Error retrieving financial summary: {e}"
