# db/chroma_client.py

"""
ChromaDB客户端模块
用于与ChromaDB向量数据库进行交互
"""

import chromadb
from typing import Optional

def get_chroma_client():
    """
    获取ChromaDB客户端实例
    
    Returns:
        chromadb.Client: ChromaDB客户端实例
    """
    # 创建或获取ChromaDB客户端
    client = chromadb.Client()
    return client