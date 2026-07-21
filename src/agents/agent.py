"""
Uni-Resource Agent — LangChain Agent.

Uses tool functions from src.tools.* which operate directly on PostgreSQL.
"""
import os
from langchain.agents import initialize_agent, AgentType
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI

from src.tools import ALL_TOOLS
from src.logging_config import get_logger

logger = get_logger("agent")


def get_llm():
    """Initialize LLM (local llama.cpp or remote)."""
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "qwen3-coder-30b-a3b-q4_k_m"),
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
        api_key=os.getenv("LLM_API_KEY", "fake-key"),
        temperature=0.1,
    )


def create_uni_resource_agent():
    """Create and return a LangChain agent with all Uni-Resource tools."""
    llm = get_llm()

    tools = [
        Tool(name=t.name, func=t, description=t.description)
        for t in ALL_TOOLS
    ]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        return_intermediate_steps=True,
    )
    return agent


if __name__ == "__main__":
    agent = create_uni_resource_agent()
    logger.info("Uni-Resource Agent started")
    logger.info("Tools: %s", [t.name for t in ALL_TOOLS])

    while True:
        user_input = input("\n> ")
        if user_input.lower() in ("quit", "exit", "q"):
            break
        try:
            result = agent.invoke({"input": user_input})
            logger.info("Answer: %s", result['output'])
        except Exception as e:
            logger.error("Error: %s", e)
