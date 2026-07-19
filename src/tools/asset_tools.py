from typing import Optional
from langchain_core.tools import tool
import psycopg2
from psycopg2.extras import RealDictCursor
import json

from src.db.database import get_db_connection

@tool
def query_asset(name: str, context_id: int, warehouse: Optional[str] = None) -> str:
    """
    Query physical asset information by name.
    
    Args:
        name (str): Name of the asset to query
        context_id (int): Context identifier for multi-tenant isolation
        warehouse (Optional[str]): Warehouse name to filter by (optional)
        
    Returns:
        str: JSON string containing asset information or error message
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query with context isolation and optional warehouse filter
        query = """
            SELECT id, name, type, quantity, status, lifecycle_log 
            FROM physical_assets 
            WHERE context_id = %s AND name = %s
        """
        params = [context_id, name]
        
        if warehouse:
            query += " AND warehouse = %s"
            params.append(warehouse)
            
        cur.execute(query, params)
        result = cur.fetchone()
        
        if result:
            return json.dumps(dict(result))
        else:
            return f"No asset found with name '{name}' in context {context_id}"
            
    except psycopg2.Error as e:
        return f"Database error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

@tool
def transfer_asset(asset_id: str, from_context: int, to_context: int, quantity: int) -> str:
    """
    Transfer physical asset from one context to another.
    
    Args:
        asset_id (str): ID of the asset to transfer
        from_context (int): Source context identifier
        to_context (int): Destination context identifier
        quantity (int): Quantity to transfer
        
    Returns:
        str: Success message or error message
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if asset exists in source context
        cur.execute("""
            SELECT id, name, quantity, type 
            FROM physical_assets 
            WHERE id = %s AND context_id = %s
        """, (asset_id, from_context))
        
        asset = cur.fetchone()
        if not asset:
            return f"Asset with ID '{asset_id}' not found in context {from_context}"
            
        # Check if quantity is sufficient
        if asset['quantity'] < quantity:
            return f"Insufficient quantity. Available: {asset['quantity']}, Requested: {quantity}"
            
        # Update source context (reduce quantity)
        cur.execute("""
            UPDATE physical_assets 
            SET quantity = quantity - %s
            WHERE id = %s AND context_id = %s
        """, (quantity, asset_id, from_context))
        
        # Check if asset exists in destination context
        cur.execute("""
            SELECT id FROM physical_assets 
            WHERE name = %s AND context_id = %s
        """, (asset['name'], to_context))
        
        existing_asset = cur.fetchone()
        
        if existing_asset:
            # Update existing asset in destination context
            cur.execute("""
                UPDATE physical_assets 
                SET quantity = quantity + %s
                WHERE id = %s
            """, (quantity, existing_asset['id']))
        else:
            # Create new asset in destination context
            cur.execute("""
                INSERT INTO physical_assets (context_id, name, type, quantity, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (to_context, asset['name'], asset['type'], quantity, 'active'))
            
        conn.commit()
        return f"Successfully transferred {quantity} of '{asset['name']}' from context {from_context} to {to_context}"
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        return f"Database error: {str(e)}"
    except Exception as e:
        if conn:
            conn.rollback()
        return f"Unexpected error: {str(e)}"
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass