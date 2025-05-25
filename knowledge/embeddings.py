"""
向量嵌入模型管理模块。
提供统一的嵌入模型访问点，避免在各处重复创建嵌入实例。
"""
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from knowledge.config import EMBEDDING_MODEL

# 全局嵌入模型实例
_embedding_model = None

def get_embedding_model() -> Embeddings:
    """
    获取嵌入模型单例。
    保证整个应用中使用同一个OpenAI嵌入模型实例，提高性能和一致性。
    
    Returns:
        Embeddings: LangChain嵌入模型实例
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = OpenAIEmbeddings(
            model=EMBEDDING_MODEL
        )
    return _embedding_model 