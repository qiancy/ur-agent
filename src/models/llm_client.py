# models/llm_client.py

"""
LLM客户端模块 (DEPRECATED)
与本地LLM进行交互

请改用 src.agents.agent.get_llm()；本模块仅保留对旧调用的兼容，
配置来源已统一到 src.config.get_llm_config()。
"""

from langchain_openai import ChatOpenAI
from typing import Optional
from src.config import get_llm_config

def get_llm_client(model_name: Optional[str] = None):
    """
    获取LLM客户端实例（DEPRECATED，请改用 src.agents.agent.get_llm）
    
    Args:
        model_name (str, optional): 模型名称；默认取统一配置 LLM_MODEL
        
    Returns:
        ChatOpenAI: LLM客户端实例
    """
    cfg = get_llm_config()

    if model_name is None:
        model_name = cfg["model"]

    llm = ChatOpenAI(
        model=model_name,
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        temperature=cfg["temperature"],
    )
    
    return llm