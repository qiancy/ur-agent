from typing import List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from datetime import datetime
import os

# 导入所有工具
from src.tools.asset_tools import query_asset, transfer_asset
from src.tools.finance_tools import record_transaction, get_transaction_history
from src.tools.human_tools import manage_reminder, check_wellness
from src.tools.knowledge_tools import rag_search, store_knowledge

# 初始化LLM
def get_llm():
    # 使用本地模型（根据项目要求）
    return ChatOpenAI(
        model="qwen3-coder-30b-a3b-q4_k_m",
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
        api_key=os.getenv("LLM_API_KEY", "fake-key"),
        temperature=0.1
    )

# 创建工具列表
tools = [
    Tool(
        name="query_asset",
        func=query_asset,
        description="Query physical asset information by name. Use this tool to look up inventory items."
    ),
    Tool(
        name="transfer_asset",
        func=transfer_asset,
        description="Transfer physical asset from one context to another. Use this tool to move inventory between contexts."
    ),
    Tool(
        name="record_transaction",
        func=record_transaction,
        description="Record financial transactions within a context. Use this tool to log income or expenses."
    ),
    Tool(
        name="get_transaction_history",
        func=get_transaction_history,
        description="Get transaction history for a specific context. Use this tool to view financial records."
    ),

    Tool(
        name="manage_reminder",
        func=manage_reminder,
        description="Manage personnel reminders and tasks. Use this tool to set up or update reminders for people."
    ),
    Tool(
        name="check_wellness",
        func=check_wellness,
        description="Check wellness information for a person in a specific context. Use this tool to view person-related information."
    ),
    Tool(
        name="rag_search",
        func=rag_search,
        description="Perform RAG (Retrieval-Augmented Generation) search within a context. Use this tool to search knowledge base."
    ),
    Tool(
        name="store_knowledge",
        func=store_knowledge,
        description="Store knowledge content in the vector database for a specific context. Use this tool to add new knowledge."
    )
]

# 创建Agent提示模板
prompt_template = """你是一个统一资源管理AI助手。你能够管理四种类型的资源：

1. 物理资源：库存、设备、家具等
2. 知识资源：SOP、手册、政策等
3. 人员资源：家庭成员、员工、护理等
4. 财务资源：收入、支出、预算等

你可以使用的工具：
{tools}

请严格按照以下格式回复：
Thought: 我需要使用哪个工具来解决这个问题？
Action: 工具名称
Action Input: 工具输入参数

请始终使用这些工具来解决问题，不要凭空想象。

当前时间：{time}

用户问题：{input}

{agent_scratchpad}"""

# 创建Agent
def create_uni_resource_agent():
    llm = get_llm()
    
    prompt = PromptTemplate.from_template(prompt_template)
    
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True
    )
    
    return agent_executor

# 主函数
def main():
    agent = create_uni_resource_agent()
    print("Uni-Resource Agent 已启动")
    print("可用工具:")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    
    # 示例交互
    while True:
        user_input = input("\n请输入您的问题 (输入 'quit' 退出): ")
        if user_input.lower() == 'quit':
            break
        try:
            result = agent.invoke({"input": user_input})
            print(f"结果: {result['output']}")
        except Exception as e:
            print(f"错误: {str(e)}")

if __name__ == "__main__":
    main()