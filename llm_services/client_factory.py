from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

_chat_client = None
_embedding_client = None

def get_chat_client(
    model_name: str = "gpt-4",
    temperature: float = 0.0,
    streaming: bool = False
) -> BaseChatModel:
    """获取或创建 LangChain Chat 客户端"""
    global _chat_client
    if _chat_client is None:
        _chat_client = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            streaming=streaming
        )
    return _chat_client

def get_embedding_client() -> Embeddings:
    """获取或创建 LangChain Embedding 客户端"""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )
    return _embedding_client 