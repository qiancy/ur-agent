# models/llm_client.py

"""
LLM客户端模块
用于与本地LLM进行交互
"""

from langchain_openai import ChatOpenAI
from typing import Optional
import os

def get_llm_client(model_name: Optional[str] = None):
    """
    获取LLM客户端实例
    
    Args:
        model_name (str, optional): 模型名称
        
    Returns:
        ChatOpenAI: LLM客户端实例
    """
    # 使用本地模型路径
    if model_name is None:
        model_name = "qwen3-coder-30b-a3b-q4_k_m"
    
    # 配置本地模型路径
    base_url = os.getenv("LLM_BASE_URL", "http://localhost:8000/v1")
    api_key = os.getenv("LLM_API_KEY", "fake-key")
    
    # 创建LLM客户端
    llm = ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=0.1
    )
    
    return llm