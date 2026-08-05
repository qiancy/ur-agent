"""
Seller Agent — read-only agent for POST /seller/chat.

Uses a local system prompt. Only accepts the explicit Seller read-only tool
list passed by the caller; there is no default all-tools fallback.

LangGraph (1.x) migration:
- AgentExecutor 已移除，改用 langgraph.prebuilt.create_react_agent
- 返回 CompiledStateGraph，通过 {"messages": [...]} 调用
"""
from langgraph.prebuilt import create_react_agent

from src.agents.agent import get_llm

_SELLER_SYSTEM_PROMPT = (
    "你是店铺经营查询助手。你只能查询当前登录店铺的经营数据，工具已经绑定当前店铺上下文。"
    "支持查询：当前库存、低库存商品、销售收入、采购支出、商品经营汇总、库存流水。"
    "不得要求用户提供身份字段、内部编号或数据库主键；不得执行任何写入操作。"
    "工具返回的是 JSON 文本，请用自然语言向用户总结关键结果。"
)


def create_seller_agent(tools):
    """Create a read-only agent bound to the given Seller tools.

    ``tools`` must be produced by ``make_seller_tools``; it is never defaulted
    to the global ALL_TOOLS.
    """
    return create_react_agent(
        model=get_llm(),
        tools=tools,
        prompt=_SELLER_SYSTEM_PROMPT,
    )
