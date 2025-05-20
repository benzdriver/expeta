from openai import OpenAI

_client = None

def get_embedding_client():
    """Get or create OpenAI client for embeddings"""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client 