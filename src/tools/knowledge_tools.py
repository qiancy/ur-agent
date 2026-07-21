from typing import Optional
from langchain_core.tools import tool
import chromadb
import json

def get_chroma_client():
    return chromadb.Client()

@tool
def rag_search(query: str, oid: int) -> str:
    """
    Perform RAG (Retrieval-Augmented Generation) search within an organization.

    Args:
        query: Natural language query.
        oid: Organization identifier for multi-tenant isolation.

    Returns:
        Retrieved documents or error message.
    """
    try:
        client = get_chroma_client()
        collection_name = f"org_{oid}"
        collection = client.get_or_create_collection(name=collection_name)

        results = collection.query(query_texts=[query], n_results=5)

        formatted_results = []
        for i, document in enumerate(results['documents'][0]):
            formatted_results.append({
                'id': results['ids'][0][i],
                'document': document,
                'distance': results['distances'][0][i]
            })

        return json.dumps(formatted_results, default=str)
    except Exception as e:
        return f"Error performing RAG search: {str(e)}"


@tool
def store_knowledge(content: str, oid: int, title: str) -> str:
    """
    Store knowledge content in the vector database for a specific organization.

    Args:
        content: Knowledge content to store.
        oid: Organization identifier for multi-tenant isolation.
        title: Title for the knowledge item.

    Returns:
        Confirmation or error message.
    """
    try:
        client = get_chroma_client()
        collection_name = f"org_{oid}"
        collection = client.get_or_create_collection(name=collection_name)

        collection.add(
            documents=[content],
            metadatas=[{"title": title}],
            ids=[f"doc_{oid}_{len(collection.get()['ids'])}"]
        )

        return f"Successfully stored knowledge item '{title}' in org {oid}"
    except Exception as e:
        return f"Error storing knowledge: {str(e)}"
