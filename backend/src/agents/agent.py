"""
Uni-Resource Agent — LangGraph ReAct Agent.

Uses tool functions from src.tools.* which operate directly on PostgreSQL.

LangGraph (1.x) migration:
- AgentExecutor 已移除，改用 langgraph.prebuilt.create_react_agent
- 返回 CompiledStateGraph，通过 {"messages": [...]} 调用
- 最终输出从 result["messages"][-1].content 提取
"""
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from src.tools import ALL_TOOLS
from src.logging_config import get_logger
from src.config import get_llm_config

logger = get_logger("agent")


def get_llm():
    """Initialize LLM from unified config (profile.yaml + DB_* env overrides)."""
    cfg = get_llm_config()
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=cfg["model"],
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        temperature=cfg["temperature"],
    )


def create_uni_resource_agent(tools=None):
    """Create and return a LangGraph ReAct agent graph with the given tools."""
    llm = get_llm()
    resolved_tools = tools if tools is not None else ALL_TOOLS
    return create_react_agent(
        model=get_llm(),
        tools=resolved_tools,
    )


def _extract_output(result: dict) -> str:
    messages = result.get("messages", [])
    if not messages:
        return ""
    last = messages[-1]
    return last.content if hasattr(last, "content") else str(last)


if __name__ == "__main__":
    graph = create_uni_resource_agent()
    logger.info("Uni-Resource Agent started")
    logger.info("Tools: %s", [t.name for t in ALL_TOOLS])

    while True:
        user_input = input("\n> ")
        if user_input.lower() in ("quit", "exit", "q"):
            break
        try:
            result = graph.invoke({"messages": [HumanMessage(content=user_input)]})
            logger.info("Answer: %s", _extract_output(result))
        except Exception as e:
            logger.error("Error: %s", e)
