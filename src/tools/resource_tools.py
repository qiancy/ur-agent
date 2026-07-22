"""Resource tools: query_resource, query_resource_warehouse."""
from typing import Optional
from langchain_core.tools import tool
import json

from src.db.database import (
    query_resource,
    query_resource_warehouse,
    get_resource_total,
    resolve_organization_id,
)


@tool
def query_resource_tool(name: str, oid: str = "shu", resource_type: Optional[str] = None) -> str:
    """
    Query resource information by name.

    Args:
        name: Name of the resource to query (partial match supported).
        oid: Organization business identifier, e.g. "shu".
        resource_type: Type filter: physical, financial, human, knowledge.
    """
    try:
        organization_id = resolve_organization_id(oid)
        results = query_resource(organization_id, name=name, resource_type=resource_type)
        if results:
            return json.dumps(results, default=str, ensure_ascii=False)
        return f"No resource found matching '{name}' in org {oid}"
    except Exception as e:
        return f"Error querying resources: {e}"


@tool
def query_resource_stock(
    resource_id: Optional[str] = None,
    location_path: Optional[str] = None,
    resource_name: Optional[str] = None,
    oid: str = "shu",
) -> str:
    """
    Query resource stock/quantity at different location levels.

    Args:
        resource_id: ID of the resource (optional if resource_name provided).
        location_path: Location path filter.
        resource_name: Name of the resource to find (optional if resource_id provided).
        oid: Organization business identifier, e.g. "shu".
    """
    try:
        organization_id = resolve_organization_id(oid)
        if resource_id is not None and not isinstance(resource_id, int):
            try:
                resource_id = int(resource_id)
            except (ValueError, TypeError):
                return f"Error: resource_id must be an integer, got '{resource_id}'"

        if resource_name and not resource_id:
            resources = query_resource(organization_id, name=resource_name)
            if resources:
                resource_id = resources[0]["id"]
            else:
                return f"No resource found matching '{resource_name}' in org {oid}"

        if resource_id is None:
            return "Error: resource_id is required or use resource_name to look up"

        results = query_resource_warehouse(resource_id, location_path=location_path)
        total = get_resource_total(resource_id)
        if results:
            return json.dumps({"details": results, "total": total}, default=str, ensure_ascii=False)
        return f"No stock found for resource {resource_id}"
    except Exception as e:
        return f"Error querying resource stock: {e}"
