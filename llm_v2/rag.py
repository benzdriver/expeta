from pathlib import Path
import os
from typing import List, Optional
from langchain_community.vectorstores import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from qdrant_client import QdrantClient, models
from qdrant_client.http import models as rest
from qdrant_client.http.exceptions import UnexpectedResponse

from llm_v2.client_factory import get_embedding_client

# Qdrant configuration
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "expeta_docs")
VECTOR_SIZE = 1536  # OpenAI embedding dimension

def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client (cloud or local)"""
    # Try cloud configuration first
    host = os.getenv("QDRANT_HOST")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    api_key = os.getenv("QDRANT_API_KEY")
    
    if host and api_key:
        print(f"🌥️ Using Qdrant cloud service: {host}")
        return QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            https=port == 443  # Enable HTTPS for standard HTTPS port
        )
    
    # Fallback to local service
    local_path = "data/qdrant"
    print(f"💾 Using local Qdrant: {local_path}")
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=local_path)

def clean_vector_store():
    """清理现有的向量存储"""
    client = get_qdrant_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"✨ 已清理集合: {COLLECTION_NAME}")
    except UnexpectedResponse:
        # 集合可能不存在，忽略错误
        pass

def init_collection(dimension: int = VECTOR_SIZE):
    """初始化 Qdrant 集合"""
    client = get_qdrant_client()
    
    # 创建集合
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=dimension,
            distance=models.Distance.COSINE
        )
    )
    
    print(f"✅ 已创建集合: {COLLECTION_NAME}")

def create_vector_store(texts: List[str], metadatas: Optional[List[dict]] = None) -> Qdrant:
    """创建向量存储"""
    # 清理现有存储
    clean_vector_store()
    
    # 创建文档对象
    documents = [
        Document(page_content=text, metadata=meta or {})
        for text, meta in zip(texts, metadatas or [{}] * len(texts))
    ]
    
    # 创建文本分割器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    # 分割文档
    splits = text_splitter.split_documents(documents)
    
    # 获取 embedding 模型
    embeddings = get_embedding_client()
    
    # 创建 Qdrant 存储
    client = get_qdrant_client()
    vector_store = Qdrant(
        client=client,
        collection_name=COLLECTION_NAME,
        embeddings=embeddings
    )
    
    # 添加文档
    vector_store.add_documents(splits)
    print(f"✅ 已将文档添加到集合: {COLLECTION_NAME}")
    
    return vector_store

def get_vector_store() -> Optional[Qdrant]:
    """获取现有的向量存储"""
    try:
        client = get_qdrant_client()
        embeddings = get_embedding_client()
        
        # 检查集合是否存在
        collections = client.get_collections().collections
        if not any(c.name == COLLECTION_NAME for c in collections):
            return None
            
        return Qdrant(
            client=client,
            collection_name=COLLECTION_NAME,
            embeddings=embeddings
        )
    except Exception as e:
        print(f"❌ 加载向量存储失败: {e}")
        return None

def embedding_retrieve(query: str, all_text: str, k: int = 3) -> str:
    """使用向量检索获取相关文本"""
    # 获取向量存储
    vector_store = get_vector_store()
    if vector_store is None:
        print("⚠️ 向量存储不存在，返回完整文本")
        return all_text
        
    # 执行相似度搜索
    results = vector_store.similarity_search(query, k=k)
    return "\n\n".join(doc.page_content for doc in results) 