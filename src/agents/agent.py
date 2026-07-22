"""
Uni-Resource Agent — LangChain Agent.

Uses tool functions from src.tools.* which operate directly on PostgreSQL.

LangChain 0.1 API update:
- create_tool_calling_agent -> create_openai_tools_agent
- Tool class moved to langchain_core.tools
- Prompt must be ChatPromptTemplate with input_variables
"""
import os
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain import hub

from src.tools import ALL_TOOLS
from src.logging_config import get_logger

logger = get_logger("agent")


def get_llm():
    """Initialize LLM (local llama.cpp or remote)."""
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "qwen3-coder-80b"),
        base_url=os.getenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1"),
        api_key=os.getenv("LLM_API_KEY", "fake-key"),
        temperature=0.1,
    )


def create_uni_resource_agent():
    """Create and return a LangChain agent with all Uni-Resource tools."""
    llm = get_llm()

    prompt = hub.pull("hwchase17/openai-tools-agent")

    agent = create_openai_tools_agent(
        llm=llm,
        tools=ALL_TOOLS,
        prompt=prompt,
    )
    
    return agent


if __name__ == "__main__":
    agent = create_uni_resource_agent()
    logger.info("Uni-Resource Agent started")
    logger.info("Tools: %s", [t.name for t in ALL_TOOLS])

    agent_executor = AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=20,
        max_execution_time=30
    )

    while True:
        user_input = input("\n> ")
        if user_input.lower() in ("quit", "exit", "q"):
            break
        try:
            result = agent_executor.invoke({"input": user_input})
            logger.info("Answer: %s", result.get('output', 'No output'))
        except Exception as e:
            logger.error("Error: %s", e)
