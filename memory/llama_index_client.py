import os
from pathlib import Path
from typing import List
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from qdrant_client import QdrantClient

class LlamaIndexClient:
    def __init__(self, input_dir="data/input", collection_name=None, dimension=1536):
        self.input_dir = input_dir
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION", "doc-index")
        self.dimension = dimension
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.qdrant_client = QdrantClient(
            host=self.qdrant_host,
            port=self.qdrant_port,
            api_key=self.qdrant_api_key,
            https=True
        )
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=self.collection_name
        )
        self.embed_model = OpenAIEmbedding()
        self.index = None

        # 自动检测并创建 collection（如不存在）
        existing_collections = [c.name for c in self.qdrant_client.get_collections().collections]
        if self.collection_name not in existing_collections:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config={"size": self.dimension, "distance": "Cosine"}
            )

        print("QDRANT_HOST =", self.qdrant_host)
        print("QDRANT_PORT =", self.qdrant_port)
        print("QDRANT_API_KEY =", self.qdrant_api_key)

    def build(self, doc_paths: List[Path] = None):
        docs = []
        if doc_paths:
            for p in doc_paths:
                docs.extend(SimpleDirectoryReader(str(p.parent)).load_data())
        else:
            docs = SimpleDirectoryReader(self.input_dir).load_data()
        self.index = VectorStoreIndex.from_documents(
            docs,
            vector_store=self.vector_store,
            embed_model=self.embed_model
        )

    def query(self, query_text, top_k=3):
        if self.index is None:
            self.index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                embed_model=self.embed_model
            )
        query_engine = self.index.as_query_engine(similarity_top_k=top_k)
        response = query_engine.query(query_text)
        return [str(response)]

    def load(self):
        if self.index is None:
            self.index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                embed_model=self.embed_model
            ) 