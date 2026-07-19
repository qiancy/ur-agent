from typing import Optional
from langchain_core.tools import tool
import psycopg2
from psycopg2.extras import RealDictCursor
import json

from src.db.database import get_db_connection

@tool
def record_transaction(amount: float, category: str, description: str, context_id: int) -> str:
    """
    Record financial transactions within a context.
    
    Args:
        amount (float): Transaction amount
        category (str): Transaction category
        description (str): Transaction description
        context_id (int): Context identifier for multi-tenant isolation
        
    Returns:
        str: Transaction confirmation or error message
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Validate amount is positive
        if amount <= 0:
            return "Error: Transaction amount must be positive"
            
        # Insert new transaction
        cur.execute("""
            INSERT INTO transactions (context_id, amount, category, description, transaction_date)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id, amount, category, description, transaction_date
        """, (context_id, amount, category, description))
        
        transaction = cur.fetchone()
        conn.commit()
        
        # Return transaction details as JSON
        return json.dumps(dict(transaction), default=str)
        
    except Exception as e:
        return f"Error recording transaction: {str(e)}"
    finally:
        if conn:
            conn.close()

@tool
def get_transaction_history(context_id: int) -> str:
    """
    Get transaction history for a specific context.
    
    Args:
        context_id (int): Context identifier for multi-tenant isolation
        
    Returns:
        str: JSON string with transaction history or error message
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query transaction history
        cur.execute("""
            SELECT * FROM transactions 
            WHERE context_id = %s 
            ORDER BY transaction_date DESC
        """, (context_id,))
        
        transactions = cur.fetchall()
        
        if transactions:
            # Convert to regular dict for JSON serialization
            transactions_data = [dict(transaction) for transaction in transactions]
            return json.dumps(transactions_data, default=str)
        else:
            return f"No transactions found for context {context_id}"
            
    except Exception as e:
        return f"Error retrieving transaction history: {str(e)}"
    finally:
        if conn:
            conn.close()

@tool
def get_summary(context_id: int) -> str:
    """
    Get financial summary for a specific context.
    
    Args:
        context_id (int): Context identifier for multi-tenant isolation
        
    Returns:
        str: JSON string with financial summary or error message
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Calculate total income (positive amounts)
        cur.execute("""
            SELECT SUM(amount) as total_income 
            FROM transactions 
            WHERE context_id = %s AND amount > 0
        """, (context_id,))
        
        total_income = cur.fetchone()['total_income'] or 0
        
        # Calculate total expenses (negative amounts)
        cur.execute("""
            SELECT SUM(ABS(amount)) as total_expenses 
            FROM transactions 
            WHERE context_id = %s AND amount < 0
        """, (context_id,))
        
        total_expenses = cur.fetchone()['total_expenses'] or 0
        
        # Calculate net balance
        balance = total_income - total_expenses
        
        # Get transaction counts
        cur.execute("""
            SELECT COUNT(*) as total_transactions
            FROM transactions 
            WHERE context_id = %s
        """, (context_id,))
        
        total_transactions = cur.fetchone()['total_transactions'] or 0
        
        # Format summary
        summary = {
            "context_id": context_id,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": balance,
            "total_transactions": total_transactions
        }
        
        return json.dumps(summary, default=str)
        
    except Exception as e:
        return f"Error retrieving financial summary: {str(e)}"
    finally:
        if conn:
            conn.close()
