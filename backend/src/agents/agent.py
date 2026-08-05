"""
Uni-Resource Agent — LangChain Agent.

Uses tool functions from src.tools.* which operate directly on PostgreSQL.

LangChain 0.1 API update:
- create_tool_calling_agent -> create_openai_tools_agent
- Tool class moved to langchain_core.tools
- Prompt must be ChatPromptTemplate with input_variables
"""
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain import hub

from src.tools import ALL_TOOLS
from src.logging_config import get_logger
from src.config import get_llm_config

logger = get_logger("agent")


def get_llm():
    """Initialize LLM from unified config (profile.yaml + DB_* env overrides)."""
    cfg = get_llm_config()
    return ChatOpenAI(
        model=cfg["model"],
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        temperature=cfg["temperature"],
    )


def create_uni_resource_agent(tools: list = None):
    """Create and return a LangChain agent with the given tools (or all tools by default)."""
    llm = get_llm()

    prompt = hub.pull("hwchase17/openai-tools-agent")
    resolved_tools = tools if tools is not None else ALL_TOOLS

    agent = create_openai_tools_agent(
        llm=llm,
        tools=resolved_tools,
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
