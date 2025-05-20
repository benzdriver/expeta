from pathlib import Path
import os
from typing import List, Dict
import numpy as np
from langchain_community.vectorstores import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from llm_v2.client_factory import get_embedding_client

# Qdrant configuration
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "doc-index")
SUMMARY_COLLECTION_NAME = os.getenv("QDRANT_SUMMARY_COLLECTION", "entity-summaries")
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_PATH = "data/qdrant"

def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client (cloud or local)"""
    if QDRANT_HOST and QDRANT_API_KEY:
        print(f"🌥️ Using Qdrant cloud service: {QDRANT_HOST}")
        return QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            api_key=QDRANT_API_KEY
        )
    else:
        # Otherwise, use local path
        print(f"💻 Using local Qdrant at {QDRANT_PATH}")
        return QdrantClient(path=QDRANT_PATH)

def create_vector_store(documents: List[str], collection_name: str = COLLECTION_NAME):
    """Create a vector store from documents"""
    print("📚 Creating vector store...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    all_chunks = []
    for doc in documents:
        chunks = text_splitter.split_text(doc)
        all_chunks.extend(chunks)
    
    # Convert to Langchain documents
    docs = [Document(page_content=chunk) for chunk in all_chunks]
    
    # Get embedding model
    embedding_client = get_embedding_client()
    
    # Create vector store
    client = get_qdrant_client()
    Qdrant.from_documents(
        docs,
        embedding_client,
        url=f"http://{QDRANT_HOST}:{QDRANT_PORT}" if QDRANT_HOST else None,
        path=QDRANT_PATH if not QDRANT_HOST else None,
        api_key=QDRANT_API_KEY if QDRANT_HOST else None,
        collection_name=collection_name,
        force_recreate=True
    )
    
    print(f"✅ Vector store created with {len(docs)} chunks")
    return docs

def embedding_retrieve(query: str, documents: str):
    """Retrieve related docs using vector search"""
    
    # Get embedding model
    embedding_client = get_embedding_client()
    
    # Get vector store
    client = get_qdrant_client()
    vector_store = Qdrant(
        client=client,
        collection_name=COLLECTION_NAME,
        embeddings=embedding_client
    )
    
    # Search for similar documents
    results = vector_store.similarity_search_with_score(query, k=5)
    
    # Extract relevant context
    context = "\n\n".join([doc.page_content for doc, score in results])
    
    return context

def store_entity_summary(entity_name: str, summary: Dict):
    """Store entity summary in vector database
    
    Args:
        entity_name: Name of the entity
        summary: Entity summary as JSON object
    """
    print(f"📥 Storing entity summary: {entity_name}")
    
    # Convert summary to text
    import json
    summary_text = json.dumps(summary, indent=2)
    
    # Create a document
    doc = Document(
        page_content=summary_text,
        metadata={
            "entity_name": entity_name,
            "entity_type": summary.get("module", "Unknown"),
            "entity_description": summary.get("description", ""),
            "is_summary": True
        }
    )
    
    # Get embedding model
    embedding_client = get_embedding_client()
    
    # Get vector store
    client = get_qdrant_client()
    
    # Initialize collection if it doesn't exist
    try:
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        if SUMMARY_COLLECTION_NAME not in collection_names:
            # Create a new collection for summaries
            vector_store = Qdrant.from_documents(
                [doc],  # Just to initialize
                embedding_client,
                url=f"http://{QDRANT_HOST}:{QDRANT_PORT}" if QDRANT_HOST else None,
                path=QDRANT_PATH if not QDRANT_HOST else None,
                api_key=QDRANT_API_KEY if QDRANT_HOST else None,
                collection_name=SUMMARY_COLLECTION_NAME,
                force_recreate=True
            )
            print(f"✅ Created new summary collection: {SUMMARY_COLLECTION_NAME}")
        else:
            # Use existing collection
            vector_store = Qdrant(
                client=client,
                collection_name=SUMMARY_COLLECTION_NAME,
                embeddings=embedding_client
            )
            
            # Add document to collection
            vector_store.add_documents([doc])
            print(f"✅ Added summary to existing collection: {SUMMARY_COLLECTION_NAME}")
    except Exception as e:
        print(f"❌ Error storing summary: {e}")
        return None
    
    return doc

def retrieve_entity_summaries(query: str, top_k: int = 5):
    """Retrieve entity summaries from vector database
    
    Args:
        query: Query string
        top_k: Number of top results
        
    Returns:
        List of entity summaries
    """
    try:
        # Get embedding model
        embedding_client = get_embedding_client()
        
        # Get vector store
        client = get_qdrant_client()
        
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        if SUMMARY_COLLECTION_NAME not in collection_names:
            print(f"❌ Summary collection not found: {SUMMARY_COLLECTION_NAME}")
            return []
            
        # Initialize vector store
        vector_store = Qdrant(
            client=client,
            collection_name=SUMMARY_COLLECTION_NAME,
            embeddings=embedding_client
        )
        
        # Search for similar summaries
        results = vector_store.similarity_search_with_score(query, k=top_k)
        
        # Parse summaries
        summaries = []
        for doc, score in results:
            if doc.metadata.get("is_summary"):
                import json
                try:
                    summary = json.loads(doc.page_content)
                    summary["entity_name"] = doc.metadata.get("entity_name")
                    summary["search_score"] = float(score)
                    summaries.append(summary)
                except:
                    pass
        
        return summaries
    except Exception as e:
        print(f"❌ Error retrieving summaries: {e}")
        return []

def retrieve_dependencies(dependencies: List[str], top_k: int = 3):
    """Retrieve summaries for dependencies
    
    Args:
        dependencies: List of dependency names
        top_k: Number of results per dependency
        
    Returns:
        Dict mapping dependency names to their summaries
    """
    result = {}
    
    for dep in dependencies:
        summaries = retrieve_entity_summaries(dep, top_k=1)
        if summaries:
            result[dep] = summaries[0]
    
    return result 