from pathlib import Path
import json
from typing import List, Dict
import numpy as np
from llm.client_factory import get_embedding_client

def load_vector_db() -> tuple[List[str], List[List[float]]]:
    """Load the vector database from disk"""
    vector_dir = Path("data/vector")
    chunks = json.loads((vector_dir / "chunks.json").read_text())
    embeddings = json.loads((vector_dir / "architecture_embeddings.json").read_text())
    return chunks, embeddings

def embedding_retrieve(query: str, all_text: str, top_k: int = 3) -> str:
    """Retrieve relevant context using semantic search"""
    # If vector DB doesn't exist, return full text
    vector_dir = Path("data/vector")
    if not (vector_dir / "chunks.json").exists():
        return all_text
        
    # Load chunks and embeddings
    chunks, stored_embeddings = load_vector_db()
    
    # Get query embedding
    client = get_embedding_client()
    query_embedding = client.get_embedding(query)
    
    # Calculate similarities
    similarities = np.dot(stored_embeddings, query_embedding)
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    # Return concatenated relevant chunks
    return "\n\n".join([chunks[i] for i in top_indices]) 