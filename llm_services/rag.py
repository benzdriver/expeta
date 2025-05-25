from common import print_log
from pathlib import Path
import os
from typing import List, Optional
from langchain_community.vectorstores import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from qdrant_client import QdrantClient, models
from qdrant_client.http import models as rest
from qdrant_client.http.exceptions import UnexpectedResponse

from llm_services.client_factory import get_embedding_client

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
        print_log(f"🌥️ Using Qdrant cloud service: {host}")
        return QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            https=port == 443  # Enable HTTPS for standard HTTPS port
        )
    
    # Fallback to local service
    local_path = "data/qdrant"
    print_log(f"💾 Using local Qdrant: {local_path}")
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    return QdrantClient(path=local_path)

def clean_vector_store():
    """清理现有的向量存储"""
    client = get_qdrant_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        print_log(f"✨ 已清理集合: {COLLECTION_NAME}")
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
    
    print_log(f"已创建集合: {COLLECTION_NAME}", level="info")

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
    print_log(f"已将文档添加到集合: {COLLECTION_NAME}", level="info")
    
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
        print_log(f"加载向量存储失败: {e}", level="error")
        return None

def embedding_retrieve(query: str, all_text: str, k: int = 3) -> str:
    """使用向量检索获取相关文本"""
    # 获取向量存储
    vector_store = get_vector_store()
    if vector_store is None:
        print_log(f"向量存储不存在，返回完整文本", level="warning")
        return all_text
        
    # 执行相似度搜索
    results = vector_store.similarity_search(query, k=k)
    return "\n\n".join(doc.page_content for doc in results)

async def retrieve_context_for_entity(entity_name: str, all_text: str, k: int = 5) -> str:
    """
    为实体检索相关上下文
    
    Args:
        entity_name: 实体名称
        all_text: 所有文档内容
        k: 检索结果数量
        
    Returns:
        str: 相关上下文文本
    """
    print_log(f"🔍 为实体 {entity_name} 检索上下文...")
    
    # 构建查询
    query = f"关于 {entity_name} 的信息、定义、功能、设计和用途"
    
    # 检查向量存储是否存在，如果不存在则创建
    vector_store = get_vector_store()
    if vector_store is None:
        print_log(f"向量存储不存在，创建新的向量存储", level="warning")
        
        # 拆分文本并创建元数据
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # 分割文本
        texts = text_splitter.split_text(all_text)
        metadatas = [{"source": "document", "index": i} for i in range(len(texts))]
        
        # 创建向量存储
        create_vector_store(texts, metadatas)
        
        # 重新获取向量存储
        vector_store = get_vector_store()
        
        if vector_store is None:
            print_log(f"创建向量存储失败，返回部分原始文本", level="error")
            # 如果还是失败，返回文本的一部分
            return all_text[:10000] if len(all_text) > 10000 else all_text
    
    # 执行相似度搜索
    results = vector_store.similarity_search(query, k=k)
    
    # 合并结果
    context = "\n\n".join(doc.page_content for doc in results)
    
    # 如果检索结果太少，添加一些原始文本
    if len(context) < 500:
        print_log(f"检索结果过少，添加更多上下文", level="warning")
        # 直接搜索文本中包含实体名称的段落
        import re
        entity_regex = re.compile(r'([^.!?]*\b' + re.escape(entity_name) + r'\b[^.!?]*[.!?])', re.IGNORECASE)
        direct_matches = entity_regex.findall(all_text)
        
        # 添加直接匹配结果
        if direct_matches:
            context += "\n\n直接匹配段落:\n\n" + "\n".join(direct_matches[:5])
    
    print_log(f"已找到 {len(results)} 个相关段落", level="info")
    return context 