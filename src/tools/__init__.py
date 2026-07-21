"""LangChain tools for Uni-Resource Agent."""
from src.tools.resource_tools import query_resource_tool, query_resource_stock
from src.tools.finance_tools import (
    record_transaction,
    get_transaction_history,
    get_summary,
)
from src.tools.human_tools import manage_reminder, check_wellness
from src.tools.knowledge_tools import rag_search, store_knowledge

ALL_TOOLS = [
    query_resource_tool,
    query_resource_stock,
    record_transaction,
    get_transaction_history,
    get_summary,
    manage_reminder,
    check_wellness,
    rag_search,
    store_knowledge,
]
