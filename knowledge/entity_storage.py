"""
实体存储模块。
提供对架构实体（模块、组件、服务等）的存储、检索和更新功能。
使用向量数据库进行相似实体检索和冲突检测。
"""
import json
from typing import Dict, List, Optional, Any, Union
from langchain_core.documents import Document
from qdrant_client import models
from datetime import datetime

from knowledge.config import ENTITY_COLLECTION, GLOBAL_DECISIONS_COLLECTION, logger
from knowledge.vector_store import get_qdrant_client, get_vector_store, create_vector_store, init_collection
from knowledge.embeddings import get_embedding_model

def store_entity(name: str, 
                entity_data: Dict[str, Any], 
                collection_name: str = ENTITY_COLLECTION) -> Optional[Document]:
    """
    存储实体到向量数据库。
    
    Args:
        name: 实体名称
        entity_data: 实体数据字典
        collection_name: 集合名称
        
    Returns:
        Optional[Document]: 存储的文档对象，失败时返回None
    """
    try:
        # 确保集合存在
        init_collection(collection_name)
        
        # 准备元数据
        metadata = {
            "entity_name": name,
            "entity_type": entity_data.get("module", "Unknown"),
            "description": entity_data.get("description", ""),
            "is_entity": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # 转换为JSON字符串
        content = json.dumps(entity_data, ensure_ascii=False, indent=2)
        
        # 创建文档
        doc = Document(page_content=content, metadata=metadata)
        
        # 存储到向量数据库
        vector_store = create_vector_store(
            documents=[doc],
            collection_name=collection_name,
            recreate=False
        )
        
        if vector_store:
            logger.log(f"✅ 已存储实体: {name}", role="memory")
            return doc
        else:
            logger.log(f"❌ 存储实体失败: {name}", level="error", role="memory")
            return None
    except Exception as e:
        logger.log(f"❌ 存储实体异常: {e}", level="error", role="memory")
        return None

def update_entity(name: str, 
                 entity_data: Dict[str, Any], 
                 collection_name: str = ENTITY_COLLECTION) -> bool:
    """
    更新实体数据。
    先删除现有实体，再存储新版本。
    
    Args:
        name: 实体名称
        entity_data: 更新后的实体数据
        collection_name: 集合名称
        
    Returns:
        bool: 操作是否成功
    """
    try:
        client = get_qdrant_client()
        
        # 查询现有实体ID
        search_result = client.search(
            collection_name=collection_name,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.entity_name",
                        match=models.MatchValue(value=name)
                    ),
                    models.FieldCondition(
                        key="metadata.is_entity",
                        match=models.MatchValue(value=True)
                    )
                ]
            ),
            limit=10
        )
        
        # 删除现有实体
        if search_result:
            point_ids = [hit.id for hit in search_result]
            client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=point_ids
                )
            )
            logger.log(f"🗑️ 已删除旧实体: {name} (找到 {len(point_ids)} 个点)", role="memory")
        
        # 存储新实体
        result = store_entity(name, entity_data, collection_name)
        return result is not None
    except Exception as e:
        logger.log(f"❌ 更新实体失败: {e}", level="error", role="memory")
        return False

def retrieve_entity(name: str, 
                   collection_name: str = ENTITY_COLLECTION) -> Optional[Dict[str, Any]]:
    """
    检索实体数据。
    
    Args:
        name: 实体名称
        collection_name: 集合名称
        
    Returns:
        Optional[Dict[str, Any]]: 实体数据字典，未找到时返回None
    """
    try:
        vector_store = get_vector_store(collection_name)
        if not vector_store:
            logger.log(f"⚠️ 找不到向量存储: {collection_name}", level="warning", role="memory")
            return None
        
        # 搜索实体
        client = get_qdrant_client()
        results = client.search(
            collection_name=collection_name,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.entity_name",
                        match=models.MatchValue(value=name)
                    ),
                    models.FieldCondition(
                        key="metadata.is_entity",
                        match=models.MatchValue(value=True)
                    )
                ]
            ),
            limit=1
        )
        
        if not results:
            logger.log(f"⚠️ 找不到实体: {name}", level="warning", role="memory")
            return None
        
        # 解析结果
        payload = results[0].payload
        if "page_content" in payload:
            content = payload["page_content"]
            try:
                entity_data = json.loads(content)
                logger.log(f"✅ 已检索实体: {name}", role="memory")
                return entity_data
            except json.JSONDecodeError:
                logger.log(f"❌ 实体数据解析失败: {name}", level="error", role="memory")
                return None
        else:
            logger.log(f"❌ 实体数据格式错误: {name}", level="error", role="memory")
            return None
    except Exception as e:
        logger.log(f"❌ 检索实体失败: {e}", level="error", role="memory")
        return None

# 添加异步版本以兼容测试
async def retrieve_entity_async(name: str, 
                              collection_name: str = ENTITY_COLLECTION) -> Optional[Dict[str, Any]]:
    """异步版本的实体检索函数"""
    return retrieve_entity(name, collection_name)

def retrieve_similar_entities(query: str, 
                             top_k: int = 5, 
                             collection_name: str = ENTITY_COLLECTION,
                             filter_dict: Optional[Dict[str, Union[str, List[str]]]] = None) -> List[Dict[str, Any]]:
    """
    检索与查询相似的实体。
    
    Args:
        query: 搜索查询
        top_k: 返回结果数量
        collection_name: 集合名称
        filter_dict: 过滤条件
        
    Returns:
        List[Dict[str, Any]]: 相似实体列表
    """
    try:
        vector_store = get_vector_store(collection_name)
        if not vector_store:
            logger.log(f"⚠️ 找不到向量存储: {collection_name}", level="warning", role="memory")
            return []
        
        # 准备过滤条件
        filter_conditions = []
        filter_conditions.append(
            models.FieldCondition(
                key="metadata.is_entity",
                match=models.MatchValue(value=True)
            )
        )
        
        if filter_dict:
            for key, value in filter_dict.items():
                if isinstance(value, list):
                    # 多值匹配（OR关系）
                    or_conditions = []
                    for val in value:
                        or_conditions.append(
                            models.FieldCondition(
                                key=f"metadata.{key}",
                                match=models.MatchValue(value=val)
                            )
                        )
                    filter_conditions.append(models.Filter(should=or_conditions, should_match_threshold=1))
                else:
                    # 单值匹配
                    filter_conditions.append(
                        models.FieldCondition(
                            key=f"metadata.{key}",
                            match=models.MatchValue(value=value)
                        )
                    )
        
        # 创建查询过滤器
        query_filter = models.Filter(must=filter_conditions)
        
        # 获取嵌入模型
        embedding_model = get_embedding_model()
        
        # 生成查询向量
        query_embedding = embedding_model.embed_query(query)
        
        # 搜索相似实体
        client = get_qdrant_client()
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=top_k
        )
        
        # 解析结果
        entities = []
        for hit in results:
            try:
                entity_data = json.loads(hit.payload.get("page_content", "{}"))
                entity_name = hit.payload.get("metadata", {}).get("entity_name", "Unknown")
                
                # 添加元数据
                entity_data["name"] = entity_name
                entity_data["similarity_score"] = hit.score
                
                entities.append(entity_data)
            except (json.JSONDecodeError, KeyError):
                continue
        
        logger.log(f"✅ 检索到 {len(entities)} 个相似实体", role="memory")
        return entities
    except Exception as e:
        logger.log(f"❌ 检索相似实体失败: {e}", level="error", role="memory")
        return []

def detect_entity_conflicts(entity_name: str, 
                          entity_data: Dict[str, Any], 
                          threshold: float = 0.85) -> List[Dict[str, Any]]:
    """
    检测实体冲突。
    基于语义相似度识别可能存在冲突的实体。
    
    Args:
        entity_name: 实体名称
        entity_data: 实体数据
        threshold: 相似度阈值（0-1），高于此值视为冲突
        
    Returns:
        List[Dict[str, Any]]: 冲突实体列表
    """
    try:
        # 创建描述字符串
        description = entity_data.get("description", "")
        module_type = entity_data.get("module", "Unknown")
        query = f"名称: {entity_name}, 类型: {module_type}, 描述: {description}"
        
        # 检索相似实体
        similar_entities = retrieve_similar_entities(
            query=query,
            top_k=5,
            filter_dict={"entity_type": module_type}
        )
        
        # 过滤出可能冲突的实体
        conflicts = []
        for entity in similar_entities:
            # 跳过自身
            if entity.get("name") == entity_name:
                continue
                
            # 检查相似度
            if entity.get("similarity_score", 0) > threshold:
                conflicts.append(entity)
        
        if conflicts:
            logger.log(f"⚠️ 检测到 {len(conflicts)} 个冲突实体", level="warning", role="memory")
        else:
            logger.log(f"✅ 未检测到冲突实体", role="memory")
            
        return conflicts
    except Exception as e:
        logger.log(f"❌ 冲突检测失败: {e}", level="error", role="memory")
        return []

# 为兼容测试添加的函数
async def store_entity_summary(name: str, summary: Dict[str, Any]) -> bool:
    """异步存储实体摘要"""
    result = store_entity(name, summary)
    return result is not None

# 全局决策相关函数
async def store_global_decisions(system_name: str, decisions: List[Dict[str, Any]]) -> bool:
    """
    存储全局架构决策。
    
    Args:
        system_name: 系统名称
        decisions: 决策列表
        
    Returns:
        bool: 操作是否成功
    """
    try:
        # 确保集合存在
        init_collection(GLOBAL_DECISIONS_COLLECTION)
        
        # 准备数据
        content = json.dumps(decisions, ensure_ascii=False, indent=2)
        metadata = {
            "system_name": system_name,
            "decision_count": len(decisions),
            "timestamp": datetime.now().isoformat(),
            "is_global_decision": True
        }
        
        # 创建文档
        doc = Document(page_content=content, metadata=metadata)
        
        # 存储到向量数据库
        vector_store = create_vector_store(
            documents=[doc],
            collection_name=GLOBAL_DECISIONS_COLLECTION,
            recreate=False
        )
        
        if vector_store:
            logger.log(f"✅ 已存储全局决策: {system_name} ({len(decisions)} 项)", role="memory")
            return True
        else:
            logger.log(f"❌ 存储全局决策失败: {system_name}", level="error", role="memory")
            return False
    except Exception as e:
        logger.log(f"❌ 存储全局决策异常: {e}", level="error", role="memory")
        return False

async def retrieve_global_decisions(system_name: str) -> Optional[List[Dict[str, Any]]]:
    """
    检索全局架构决策。
    
    Args:
        system_name: 系统名称
        
    Returns:
        Optional[List[Dict[str, Any]]]: 决策列表，未找到时返回None
    """
    try:
        vector_store = get_vector_store(GLOBAL_DECISIONS_COLLECTION)
        if not vector_store:
            logger.log(f"⚠️ 找不到全局决策集合", level="warning", role="memory")
            return None
        
        # 搜索决策
        client = get_qdrant_client()
        results = client.search(
            collection_name=GLOBAL_DECISIONS_COLLECTION,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.system_name",
                        match=models.MatchValue(value=system_name)
                    ),
                    models.FieldCondition(
                        key="metadata.is_global_decision",
                        match=models.MatchValue(value=True)
                    )
                ]
            ),
            limit=1
        )
        
        if not results:
            logger.log(f"⚠️ 找不到全局决策: {system_name}", level="warning", role="memory")
            return None
        
        # 解析结果
        payload = results[0].payload
        if "page_content" in payload:
            content = payload["page_content"]
            try:
                decisions = json.loads(content)
                logger.log(f"✅ 已检索全局决策: {system_name} ({len(decisions)} 项)", role="memory")
                return decisions
            except json.JSONDecodeError:
                logger.log(f"❌ 全局决策数据解析失败: {system_name}", level="error", role="memory")
                return None
        else:
            logger.log(f"❌ 全局决策数据格式错误: {system_name}", level="error", role="memory")
            return None
    except Exception as e:
        logger.log(f"❌ 检索全局决策失败: {e}", level="error", role="memory")
        return None

def list_entities(collection_name: str = ENTITY_COLLECTION) -> List[str]:
    """
    列出存储中的所有实体名称。
    
    Args:
        collection_name: 集合名称
    
    Returns:
        List[str]: 实体名称列表
    """
    try:
        client = get_qdrant_client()
        if not client:
            logger.log("❌ 无法获取Qdrant客户端", level="error", role="memory")
            return []
        
        # 检查集合是否存在
        collections = client.get_collections().collections
        if not any(c.name == collection_name for c in collections):
            logger.log(f"⚠️ 集合不存在: {collection_name}", level="warning", role="memory")
            return []
        
        # 查询是实体的文档
        filter_query = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.is_entity",
                    match=models.MatchValue(value=True)
                )
            ]
        )
        
        # 使用scroll搜索获取所有实体
        results = client.scroll(
            collection_name=collection_name,
            scroll_filter=filter_query,
            limit=100,
            with_payload=True
        )[0]  # scroll返回(points, next_page_offset)元组
        
        # 提取实体名称
        entity_names = []
        for point in results:
            metadata = point.payload.get("metadata", {})
            entity_name = metadata.get("entity_name")
            if entity_name:
                entity_names.append(entity_name)
        
        logger.log(f"✅ 列出 {len(entity_names)} 个实体", role="memory")
        return entity_names
    except Exception as e:
        logger.log(f"❌ 列出实体失败: {e}", level="error", role="memory")
        return []
