"""
Chat endpoint with Agent integration.
"""
import asyncio
from fastapi import APIRouter, HTTPException
from src.logging_config import setup_logging

from src.models.schemas import ChatRequest
from src.db.database import query_organization, get_org_members

logger = setup_logging("api.chat")

router = APIRouter(tags=["chat"])

IDENTITY_MESSAGES = {
    "我是谁", "我是谁？", "我是谁?",
    "你是谁", "你是谁？", "你是谁?",
    "当前空间", "当前组织",
}


def _get_org_context(oid: int) -> dict:
    rows = query_organization(oid=oid)
    if not rows:
        return {"id": oid, "name": f"组织 {oid}", "type": "unknown"}
    org = rows[0]
    return {"id": org["id"], "name": org["name"], "type": org["type"]}


@router.post("/chat")
async def chat(body: ChatRequest):
    try:
        message = body.message.strip()
        org = _get_org_context(body.oid)
        logger.info("Chat request: oid=%s, org=%s, message=%s", body.oid, org["name"], message[:100])

        if message in IDENTITY_MESSAGES:
            members = get_org_members(body.oid)
            member_text = "、".join(
                f"{m['name']}({m['role'] or '成员'})" for m in members[:5]
            ) or "暂无成员"
            response = (
                f"当前空间来自数据库 organization 表：{org['name']}，类型 {org['type']}，组织 ID {org['id']}。"
                f"该空间成员包括：{member_text}。"
            )
            logger.info("Chat fast-path response from DB: %s", response)
            return {"response": response, "oid": body.oid}

        agent_input = (
            f"数据库已确认当前 organization.id={org['id']}，name={org['name']}，type={org['type']}。\n"
            "调用工具时必须显式传入上述 oid。\n"
            f"用户问题: {message}"
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
        return {"response": result.get('output', ''), "oid": body.oid}
    except asyncio.TimeoutError:
        logger.error("Chat request timed out (30s)")
        raise HTTPException(504, "AI agent timed out. Is the LLM server running?")
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(500, f"Agent error: {e}")
