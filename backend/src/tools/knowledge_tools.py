from langchain_core.tools import tool
import chromadb
import json

from src.db.database import resolve_organization_id


def get_chroma_client():
    return chromadb.Client()


@tool
def rag_search(query: str, ouid: str = "shu") -> str:
    """
    Perform RAG search within an organization.

    Args:
        query: Natural language query.
        ouid: Organization business identifier, e.g. "shu".
    """
    try:
        resolve_organization_id(ouid)
        client = get_chroma_client()
        collection_name = f"org_{ouid}"
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
def store_knowledge(content: str, ouid: str = "shu", title: str = "") -> str:
    """
    Store knowledge content in the vector database for a specific organization.

    Args:
        content: Knowledge content to store.
        ouid: Organization business identifier, e.g. "shu".
        title: Title for the knowledge item.
    """
    try:
        resolve_organization_id(ouid)
        client = get_chroma_client()
        collection_name = f"org_{ouid}"
        collection = client.get_or_create_collection(name=collection_name)

        collection.add(
            documents=[content],
            metadatas=[{"title": title}],
            ids=[f"doc_{ouid}_{len(collection.get()['ids'])}"]
        )

        return f"Successfully stored knowledge item '{title}' in org {ouid}"
    except Exception as e:
        return f"Error storing knowledge: {str(e)}"
