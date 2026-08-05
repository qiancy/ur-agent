"""
Chat endpoint with Agent integration.
"""
import asyncio
from fastapi import APIRouter, HTTPException, Request
from src.logging_config import setup_logging

from src.models.schemas import ChatRequest
from src.routers.deps import require_org_context
from langchain_core.messages import HumanMessage

logger = setup_logging("api.chat")

router = APIRouter(tags=["chat"])

IDENTITY_MESSAGES = {
    "我是谁", "我是谁？", "我是谁?",
    "你是谁", "你是谁？", "你是谁?",
    "当前空间", "当前组织",
}

def _get_org_context(ctx: dict) -> dict:
    return {
        "name": ctx.get("org_name") or ctx.get("ouid") or "Unknown",
        "type": ctx.get("org_type", "unknown"),
        "ouid": ctx.get("ouid"),
    }


@router.post("/chat")
async def chat(body: ChatRequest, request: Request):
    try:
        ctx = require_org_context(request)
        if ctx.get("org_type") == "ecommerce":
            raise HTTPException(
                403,
                "Ecommerce organizations must use /seller/chat (Seller AI is the only "
                "allowed AI entry point for ecommerce organizations)",
            )
        message = body.message.strip()
        org = _get_org_context(ctx)
        ouid_str = ctx["ouid"]

        logger.info("Chat request: ouid=%s, org=%s, message=%s",
                     ouid_str, org["name"], message[:100])

        if message in IDENTITY_MESSAGES:
            from src.db.database import get_org_members
            members = get_org_members(ctx["organization_id"])
            member_text = "、".join(
                f"{m['name']}({m['role'] or 'member'})" for m in members[:5]
            ) or "no members"
            response = (
                f"Organization: {org['name']}, type: {org['type']}. "
                f"Members: {member_text}."
            )
            logger.info("Chat fast-path response from DB: %s", response)
            return {"response": response, "ouid": ouid_str}

        agent_input = (
            f"Database confirmed organization name={org['name']}, type={org['type']}.\n"
            "When calling tools, you MUST explicitly pass the ouid.\n"
            f"User question: {message}"
        )

        def _run_agent():
            from src.agents.agent import create_uni_resource_agent
            from src.tools import ALL_TOOLS
            tools = list(ALL_TOOLS)
            graph = create_uni_resource_agent(tools=tools)
            result = graph.invoke({"messages": [HumanMessage(content=agent_input)]})
            output = result["messages"][-1].content if result.get("messages") else ""
            return {"output": output, "intermediate_steps": []}

        result = await asyncio.wait_for(
            asyncio.to_thread(_run_agent), timeout=30
        )
        steps = result.get("intermediate_steps", [])
        if steps:
            logger.info("Chat intermediate steps: %s", steps)
        logger.info("Chat response: %s", result.get('output', '')[:500])
        return {"response": result.get('output', ''), "ouid": ouid_str}
    except asyncio.TimeoutError:
        logger.error("Chat request timed out (30s)")
        raise HTTPException(504, "AI agent timed out. Is the LLM server running?")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(500, f"Agent error: {e}")
