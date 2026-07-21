"""Resource tools: query_resource, query_resource_warehouse."""
from typing import Optional
from langchain_core.tools import tool
import json

from src.db.database import query_resource, query_resource_warehouse, get_resource_total


@tool
def query_resource_tool(name: str, oid: int, resource_type: Optional[str] = None) -> str:
    """
    Query resource information by name.

    Args:
        name: Name of the resource to query (partial match supported).
        oid: Organization identifier for multi-tenant isolation.
        resource_type: Type filter: 'physical', 'financial', 'human', 'knowledge' (optional).

    Returns:
        JSON string containing resource information or error message.
    """
    try:
        results = query_resource(oid, name=name, resource_type=resource_type)
        if results:
            return json.dumps(results, default=str, ensure_ascii=False)
        return f"No resource found matching '{name}' in org {oid}"
    except Exception as e:
        return f"Error querying resources: {e}"


@tool
def query_resource_stock(resource_id: int, location_path: Optional[str] = None) -> str:
    """
    Query resource stock/quantity at different location levels.

    Args:
        resource_id: ID of the resource.
        location_path: Location path filter (e.g. 'A' for warehouse, 'A-1' for area, optional).

    Returns:
        JSON string with stock information or error message.
    """
    try:
        results = query_resource_warehouse(resource_id, location_path=location_path)
        total = get_resource_total(resource_id)
        if results:
            return json.dumps({
                "details": results,
                "total": total
            }, default=str, ensure_ascii=False)
        return f"No stock found for resource {resource_id}"
    except Exception as e:
        return f"Error querying resource stock: {e}"
