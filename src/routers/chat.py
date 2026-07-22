"""
Chat endpoint with Agent integration.
"""
import asyncio
from fastapi import APIRouter, HTTPException, Request
from src.logging_config import setup_logging

from src.models.schemas import ChatRequest
from src.db.database import query_organization, get_org_members
from src.routers.deps import get_current_user

logger = setup_logging("api.chat")

router = APIRouter(tags=["chat"])

IDENTITY_MESSAGES = {
    "我是谁", "我是谁？", "我是谁?",
    "你是谁", "你是谁？", "你是谁?",
    "当前空间", "当前组织",
}


def _get_org_context(org_id: int) -> dict:
    rows = query_organization(org_id=org_id)
    if not rows:
        return {"id": org_id, "name": f"Org {org_id}", "type": "unknown"}
    org = rows[0]
    return {"id": org["id"], "name": org["name"], "type": org["type"]}


def _resolve_org_id(request: Request, body: ChatRequest) -> int:
    """Resolve organization_id from JWT, query param, or request body."""
    # 1. Try JWT
    payload = get_current_user(request)
    if payload:
        from src.db.database import query_organization_by_oid
        orgs = query_organization_by_oid(payload.get("oid"))
        if orgs:
            return orgs[0]["id"]

    # 2. Try query param
    oid_param = request.query_params.get("oid")
    if oid_param is not None:
        try:
            return int(oid_param)
        except (ValueError, TypeError):
            from src.db.database import query_organization_by_oid
            orgs = query_organization_by_oid(oid_param)
            if orgs:
                return orgs[0]["id"]

    # 3. Try body oid field (backward compat)
    if hasattr(body, 'oid') and body.oid is not None:
        return body.oid

    raise HTTPException(401, "Organization context required. Provide Bearer token, oid query param, or oid in body.")


@router.post("/chat")
async def chat(body: ChatRequest, request: Request):
    try:
        org_id = _resolve_org_id(request, body)
        message = body.message.strip()
        org = _get_org_context(org_id)

        # Get oid string for response
        from src.db.database import _fetch
        org_rows = _fetch("SELECT oid FROM organization WHERE id = %s", (org_id,))
        oid_str = org_rows[0]["oid"] if org_rows else str(org_id)

        logger.info("Chat request: oid=%s, org=%s, message=%s", oid_str, org["name"], message[:100])

        if message in IDENTITY_MESSAGES:
            members = get_org_members(org_id)
            member_text = "、".join(
                f"{m['name']}({m['role'] or 'member'})" for m in members[:5]
            ) or "no members"
            response = (
                f"Organization: {org['name']}, type: {org['type']}, id: {org['id']}. "
                f"Members: {member_text}."
            )
            logger.info("Chat fast-path response from DB: %s", response)
            return {"response": response, "oid": oid_str}

        agent_input = (
            f"Database confirmed organization.id={org['id']}, name={org['name']}, type={org['type']}.\n"
            "When calling tools, you MUST explicitly pass the oid.\n"
            f"User question: {message}"
        )

        def _run_agent():
            from src.agents.agent import create_uni_resource_agent
            from langchain.agents import AgentExecutor
            from src.tools import ALL_TOOLS
            agent = create_uni_resource_agent()
            agent_executor = AgentExecutor(
                agent=agent,
                tools=ALL_TOOLS,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=4,
                return_intermediate_steps=True,
            )
            return agent_executor.invoke({"input": agent_input})

        result = await asyncio.wait_for(
            asyncio.to_thread(_run_agent), timeout=30
        )
        steps = result.get("intermediate_steps", [])
        if steps:
            logger.info("Chat intermediate steps: %s", steps)
        logger.info("Chat response: %s", result.get('output', '')[:500])
        return {"response": result.get('output', ''), "oid": oid_str}
    except asyncio.TimeoutError:
        logger.error("Chat request timed out (30s)")
        raise HTTPException(504, "AI agent timed out. Is the LLM server running?")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(500, f"Agent error: {e}")
