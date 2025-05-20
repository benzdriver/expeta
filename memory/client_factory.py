from dotenv import load_dotenv
load_dotenv()
import os
from memory.embedding_client import EmbeddingClient
from memory.embedding_client import LocalEmbeddingClient
from memory.llama_index_client import LlamaIndexClient
# from memory.external.pinecone_client import PineconeEmbeddingClient
# from memory.external.weaviate_client import WeaviateEmbeddingClient
# 更多可插拔客户端...

def get_embedding_client(name: str = "pinecone") -> EmbeddingClient:
    print(f"[DEBUG] 强制使用 Pinecone/LlamaIndexClient，无论参数: {name}")
    return LlamaIndexClient()
