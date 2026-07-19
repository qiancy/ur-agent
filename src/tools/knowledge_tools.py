from typing import Optional
from langchain_core.tools import tool
import chromadb
import json

# ChromaDB client
def get_chroma_client():
    # In a real implementation, this would use proper connection management
    return chromadb.Client()

@tool
def rag_search(query: str, context_id: int) -> str:
    """
    Perform RAG (Retrieval-Augmented Generation) search within a context.
    
    Args:
        query (str): Natural language query
        context_id (int): Context identifier for multi-tenant isolation
        
    Returns:
        str: Retrieved documents or error message
    """
    client = None
    try:
        client = get_chroma_client()
        
        # Create or get collection for this context
        collection_name = f"context_{context_id}"
        collection = client.get_or_create_collection(name=collection_name)
        
        # Perform search
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
        
        # Format results
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
    finally:
        # In a real implementation, we might want to close connections
        pass

@tool
def store_knowledge(content: str, context_id: int, title: str) -> str:
    """
    Store knowledge content in the vector database for a specific context.
    
    Args:
        content (str): Knowledge content to store
        context_id (int): Context identifier for multi-tenant isolation
        title (str): Title for the knowledge item
        
    Returns:
        str: Confirmation or error message
    """
    client = None
    try:
        client = get_chroma_client()
        
        # Create or get collection for this context
        collection_name = f"context_{context_id}"
        collection = client.get_or_create_collection(name=collection_name)
        
        # Add document
        collection.add(
            documents=[content],
            metadatas=[{"title": title}],
            ids=[f"doc_{context_id}_{len(collection.get()['ids'])}"]
        )
        
        return f"Successfully stored knowledge item '{title}' in context {context_id}"
        
    except Exception as e:
        return f"Error storing knowledge: {str(e)}"
    finally:
        # In a real implementation, we might want to close connections
        pass
