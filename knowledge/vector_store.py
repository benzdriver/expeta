"""
向量存储管理模块。
提供向量数据库的创建、访问和管理功能，支持文档、实体和推理记录的存储和检索。
基于Qdrant向量数据库实现，提供统一接口。
"""
from typing import List, Optional, Dict, Union
from pathlib import Path
import traceback
import json
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse, ApiException
from langchain_community.vectorstores import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# 导入路径已更新
from knowledge.config import *
from knowledge.embeddings import get_embedding_model

def get_qdrant_client() -> QdrantClient:
    """
    获取Qdrant客户端连接（云或本地）。
    
    Returns:
        QdrantClient: Qdrant客户端实例
        
    Raises:
        ConnectionError: 连接Qdrant服务失败时抛出
    """
    try:
        if QDRANT_HOST and QDRANT_API_KEY:
            logger.log(f"🌥️ 尝试连接Qdrant云服务: {QDRANT_HOST}", role="memory")
            client = QdrantClient(
                host=QDRANT_HOST,
                port=QDRANT_PORT,
                api_key=QDRANT_API_KEY,
                timeout=30,  # 增加超时时间
                prefer_grpc=False,  # 使用HTTP而不是gRPC
                check_compatibility=False  # 跳过版本兼容性检查
            )
            # 测试连接是否正常
            try:
                collections = client.get_collections()
                collection_names = [c.name for c in collections.collections]
                logger.log(f"✅ 成功连接Qdrant云服务，当前有 {len(collection_names)} 个集合", role="memory")
                return client
            except UnexpectedResponse as e:
                error_details = "未知错误"
                http_status = "未知"
                try:
                    if hasattr(e, 'response'):
                        http_status = str(e.response.status_code)
                        error_data = json.loads(e.response.text)
                        error_details = error_data.get('status', {}).get('error', 'API详细错误未知')
                except Exception:
                    pass
                
                logger.log(f"❌ Qdrant云服务API响应异常(HTTP {http_status}): {error_details}", level="error", role="memory")
                logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
                
                if "403" in http_status:
                    logger.log("⚠️ 可能是API密钥无效或权限不足，请检查QDRANT_API_KEY环境变量", level="warning", role="memory")
                elif "401" in http_status:
                    logger.log("⚠️ 认证失败，请检查QDRANT_API_KEY是否正确设置", level="warning", role="memory")
                
                # 抛出异常而不是回退到本地存储
                raise ConnectionError(f"Qdrant云服务连接失败: {str(e)}")
            
            except ApiException as e:
                logger.log(f"❌ Qdrant云服务API错误: {str(e)}", level="error", role="memory")
                logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
                
                # 抛出异常而不是回退到本地存储
                raise ConnectionError(f"Qdrant云服务API错误: {str(e)}")
        else:
            logger.log(f"💻 使用本地Qdrant: {QDRANT_PATH}", role="memory")
            Path(QDRANT_PATH).parent.mkdir(parents=True, exist_ok=True)
            return QdrantClient(path=QDRANT_PATH)
    except Exception as e:
        logger.log(f"❌ Qdrant连接初始化失败: {str(e)}", level="error", role="memory")
        logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
        raise ConnectionError(f"无法连接到Qdrant: {str(e)}")

def clean_collection(collection_name: str) -> bool:
    """
    清理指定集合。
    
    Args:
        collection_name: 集合名称
        
    Returns:
        bool: 操作是否成功
    """
    try:
        client = get_qdrant_client()
        client.delete_collection(collection_name)
        logger.log(f"✨ 已清理集合: {collection_name}", role="memory")
        return True
    except UnexpectedResponse as e:
        # 集合可能不存在，先检查响应状态码
        if hasattr(e, 'response') and e.response.status_code == 404:
            logger.log(f"⚠️ 集合不存在，跳过清理: {collection_name}", level="warning", role="memory")
            return True
        # 其他API错误
        logger.log(f"❌ 清理集合API响应异常: {str(e)}", level="error", role="memory")
        logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
        return False
    except ApiException as e:
        logger.log(f"❌ 清理集合API错误: {str(e)}", level="error", role="memory")
        logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
        return False
    except Exception as e:
        logger.log(f"❌ 清理集合失败: {e}", level="error", role="memory")
        logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
        return False

def init_collection(collection_name: str, dimension: int = VECTOR_SIZE) -> bool:
    """
    初始化向量集合。
    
    Args:
        collection_name: 集合名称
        dimension: 向量维度
        
    Returns:
        bool: 操作是否成功
    """
    try:
        client = get_qdrant_client()
        
        # 检查集合是否已存在
        collections = client.get_collections().collections
        if any(c.name == collection_name for c in collections):
            logger.log(f"⚠️ 集合已存在: {collection_name}", level="warning", role="memory")
            return True
        
        # 创建集合
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=dimension,
                distance=models.Distance.COSINE
            )
        )
        
        logger.log(f"✅ 已创建集合: {collection_name}", role="memory")
        return True
    except Exception as e:
        logger.log(f"❌ 创建集合失败: {e}", level="error", role="memory")
        return False

def init_all_collections(dimension: int = VECTOR_SIZE) -> bool:
    """
    初始化所有预定义的集合。
    
    Args:
        dimension: 向量维度
        
    Returns:
        bool: 所有集合是否成功初始化
    """
    success = True
    logger.log("🚀 开始初始化所有向量集合...", role="memory")
    
    for collection_name in ALL_COLLECTIONS:
        result = init_collection(collection_name, dimension)
        if not result:
            success = False
            logger.log(f"❌ 初始化集合失败: {collection_name}", level="error", role="memory")
    
    if success:
        logger.log(f"✅ 所有集合初始化完成", role="memory")
    else:
        logger.log(f"⚠️ 部分集合初始化失败", level="warning", role="memory")
    
    return success

def create_vector_store(
    documents: Union[List[str], List[Document]], 
    metadatas: Optional[List[Dict]] = None,
    collection_name: str = DOCS_COLLECTION,
    recreate: bool = False
) -> Optional[Qdrant]:
    """
    创建向量存储或向现有存储添加文档。
    
    Args:
        documents: 文档文本列表或Document对象列表
        metadatas: 元数据列表，与documents一一对应
        collection_name: 集合名称
        recreate: 是否重新创建集合（清除现有数据）
        
    Returns:
        Optional[Qdrant]: 向量存储实例，失败时返回None
    """
    try:
        logger.log(f"📝 开始处理 {len(documents)} 个文档 (集合: {collection_name})", role="memory")
        
        # 处理输入文档
        doc_objects = []
        if documents and isinstance(documents[0], str):
            # 将文本转换为Document对象
            for i, text in enumerate(documents):
                meta = {} if not metadatas or i >= len(metadatas) else metadatas[i]
                doc_objects.append(Document(page_content=text, metadata=meta))
        else:
            # 已经是Document对象
            doc_objects = documents
        
        # 文本分割
        logger.log(f"✂️ 对文档进行分块 (块大小: {CHUNK_SIZE}, 重叠: {CHUNK_OVERLAP})", level="debug", role="memory")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        splits = text_splitter.split_documents(doc_objects)
        logger.log(f"🧩 文档拆分成 {len(splits)} 个块", level="debug", role="memory")
        
        # 获取嵌入模型
        try:
            embeddings = get_embedding_model()
        except Exception as e:
            logger.log(f"❌ 获取嵌入模型失败: {str(e)}", level="error", role="memory")
            logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
            return None
        
        # 获取Qdrant客户端
        try:
            client = get_qdrant_client()
        except ConnectionError as e:
            logger.log(f"❌ 获取Qdrant客户端失败: {str(e)}", level="error", role="memory")
            return None
        
        # 检查是否需要重新创建集合
        if recreate:
            logger.log(f"🔄 重新创建集合: {collection_name}", role="memory")
            clean_collection(collection_name)
        
        # 检查集合是否存在
        try:
            collections = client.get_collections().collections
            collection_exists = any(c.name == collection_name for c in collections)
        except Exception as e:
            logger.log(f"❌ 获取集合列表失败: {str(e)}", level="error", role="memory")
            logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
            logger.log(f"⚠️ 假设集合不存在并尝试创建", level="warning", role="memory")
            collection_exists = False
        
        vector_store = None
        try:
            if collection_exists and not recreate:
                # 向现有集合添加文档
                logger.log(f"➕ 向现有集合 '{collection_name}' 添加文档", role="memory")
                vector_store = Qdrant(
                    client=client,
                    collection_name=collection_name,
                    embeddings=embeddings
                )
                vector_store.add_documents(splits)
                logger.log(f"✅ 向集合 '{collection_name}' 添加了 {len(splits)} 个文档片段", role="memory")
            else:
                # 创建新集合
                logger.log(f"🆕 创建新集合 '{collection_name}'", role="memory")
                if QDRANT_HOST and QDRANT_API_KEY:
                    try:
                        # 尝试使用云服务
                        logger.log(f"☁️ 使用Qdrant云服务创建集合: {collection_name}", level="debug", role="memory")
                        url = f"https://{QDRANT_HOST}:{QDRANT_PORT}"
                        vector_store = Qdrant.from_documents(
                            splits,
                            embeddings,
                            url=url,
                            api_key=QDRANT_API_KEY,
                            collection_name=collection_name,
                            force_recreate=True,
                            prefer_grpc=False
                        )
                        logger.log(f"✅ 在云服务上创建集合 '{collection_name}' 成功", role="memory")
                    except Exception as cloud_error:
                        # 云服务失败，报告错误
                        logger.log(f"❌ 云服务创建集合失败: {str(cloud_error)}", level="error", role="memory")
                        logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
                        
                        # 检查是否为API密钥相关错误
                        error_str = str(cloud_error).lower()
                        if "403" in error_str or "401" in error_str or "api key" in error_str or "authentication" in error_str:
                            logger.log("⚠️ API密钥可能无效，请检查QDRANT_API_KEY环境变量", level="warning", role="memory")
                        
                        return None
                else:
                    # 本地存储
                    logger.log(f"💻 使用本地存储创建集合: {collection_name}", level="debug", role="memory")
                    vector_store = Qdrant.from_documents(
                        splits,
                        embeddings,
                        path=QDRANT_PATH,
                        collection_name=collection_name,
                        force_recreate=True
                    )
                    logger.log(f"✅ 创建集合 '{collection_name}' 包含 {len(splits)} 个文档片段", role="memory")
        except Exception as e:
            logger.log(f"❌ 创建/更新向量存储失败: {str(e)}", level="error", role="memory")
            logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
            
            # 检查是否为API密钥相关错误
            error_str = str(e).lower()
            if "403" in error_str or "401" in error_str or "api key" in error_str or "authentication" in error_str:
                logger.log("⚠️ API密钥可能无效，请检查QDRANT_API_KEY环境变量", level="warning", role="memory")
            
            return None
        
        return vector_store
    except Exception as e:
        logger.log(f"❌ 创建向量存储过程中发生未预期错误: {str(e)}", level="error", role="memory")
        logger.log(f"🔍 详细错误: {traceback.format_exc()}", level="debug", role="memory")
        return None

# 添加异步版本以兼容测试
async def create_vector_store_async(
    documents: Union[List[str], List[Document]], 
    metadatas: Optional[List[Dict]] = None,
    collection_name: str = DOCS_COLLECTION,
    recreate: bool = False
) -> Optional[Qdrant]:
    """异步版本的向量存储创建函数"""
    return create_vector_store(documents, metadatas, collection_name, recreate)

def get_vector_store(collection_name: str) -> Optional[Qdrant]:
    """
    获取向量存储实例。
    
    Args:
        collection_name: 集合名称
        
    Returns:
        Optional[Qdrant]: 向量存储实例，失败时返回None
    """
    try:
        # 检查集合是否存在
        client = get_qdrant_client()
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            logger.log(f"⚠️ 集合不存在: {collection_name}", level="warning", role="memory")
            return None
        
        # 获取嵌入模型
        embeddings = get_embedding_model()
        
        # 创建向量存储实例
        if QDRANT_HOST and QDRANT_API_KEY:
            # 云服务
            url = f"https://{QDRANT_HOST}:{QDRANT_PORT}"
            vector_store = Qdrant(
                client=client,
                collection_name=collection_name,
                embeddings=embeddings
            )
        else:
            # 本地存储
            vector_store = Qdrant(
                client=client,
                collection_name=collection_name,
                embeddings=embeddings
            )
        
        logger.log(f"✅ 获取向量存储: '{collection_name}'", role="memory")
        return vector_store
    except Exception as e:
        logger.log(f"❌ 获取向量存储失败: {e}", level="error", role="memory")
        return None
