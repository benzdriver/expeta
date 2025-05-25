"""
推理记忆管理模块。
提供存储、检索和管理推理过程中的决策、问答记录和关键结论。
基于向量数据库实现语义搜索和相关历史决策检索。
"""
import json
import time
from typing import Dict, List, Optional, Any, Union
from langchain_core.documents import Document

from knowledge.config import REASONING_COLLECTION, logger, DEFAULT_TOP_K
from knowledge.vector_store import get_vector_store, create_vector_store

def store_reasoning(
    entity_name: str,
    reasoning_type: str,
    round_goal: str,
    qa_history: List[Dict[str, str]],
    decisions: List[str],
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    存储推理过程记录。
    
    Args:
        entity_name: 实体名称
        reasoning_type: 推理类型 (例如: "global", "local")
        round_goal: 推理轮次目标
        qa_history: 问答历史列表
        decisions: 关键决策列表
        metadata: 额外元数据
        
    Returns:
        bool: 操作是否成功
    """
    try:
        # 准备记录内容
        reasoning_data = {
            "entity_name": entity_name,
            "reasoning_type": reasoning_type,
            "round_goal": round_goal,
            "qa_history": qa_history,
            "decisions": decisions,
            "timestamp": time.time(),
        }
        
        # 添加额外元数据
        if metadata:
            reasoning_data.update(metadata)
            
        # 转换为文本
        reasoning_text = json.dumps(reasoning_data, indent=2)
        
        # 创建元数据
        meta = {
            "entity_name": entity_name,
            "reasoning_type": reasoning_type,
            "round_goal": round_goal,
            "timestamp": time.time(),
            "is_reasoning": True
        }
        
        # 创建文档
        doc = Document(
            page_content=reasoning_text,
            metadata=meta
        )
        
        # 存储到向量数据库
        vector_store = get_vector_store(REASONING_COLLECTION)
        if vector_store is None:
            # 创建新集合
            create_vector_store([doc], collection_name=REASONING_COLLECTION)
            logger.log(f"✅ 创建推理记忆集合并存储推理记录: {entity_name}", role="memory")
        else:
            # 添加到现有集合
            vector_store.add_documents([doc])
            logger.log(f"✅ 推理记录已添加到集合: {entity_name}/{round_goal}", role="memory")
            
        return True
    except Exception as e:
        logger.log(f"❌ 存储推理记录失败: {e}", level="error", role="memory")
        return False

def retrieve_related_reasoning(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    filter_dict: Optional[Dict[str, Any]] = None,
    include_content: bool = True
) -> List[Dict[str, Any]]:
    """
    检索与查询相关的推理记录。
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        filter_dict: 过滤条件
        include_content: 是否包含完整内容
        
    Returns:
        List[Dict[str, Any]]: 相关推理记录列表
    """
    try:
        vector_store = get_vector_store(REASONING_COLLECTION)
        if vector_store is None:
            return []
            
        # 执行相似度搜索
        results = vector_store.similarity_search_with_score(query, k=top_k, filter=filter_dict)
        
        # 解析结果
        reasoning_records = []
        for doc, score in results:
            if doc.metadata.get("is_reasoning"):
                try:
                    if include_content:
                        record = json.loads(doc.page_content)
                    else:
                        # 只返回元数据和摘要
                        record = {
                            "entity_name": doc.metadata.get("entity_name", ""),
                            "reasoning_type": doc.metadata.get("reasoning_type", ""),
                            "round_goal": doc.metadata.get("round_goal", ""),
                            "timestamp": doc.metadata.get("timestamp", 0),
                            "decisions_count": len(json.loads(doc.page_content).get("decisions", []))
                        }
                    
                    record["similarity_score"] = float(score)
                    reasoning_records.append(record)
                except Exception as e:
                    logger.log(f"❌ 解析推理记录失败: {e}", level="error", role="memory")
                    
        return reasoning_records
    except Exception as e:
        logger.log(f"❌ 检索推理记录失败: {e}", level="error", role="memory")
        return []

def retrieve_entity_reasoning_history(
    entity_name: str,
    reasoning_type: Optional[str] = None,
    round_goal: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    检索特定实体的推理历史。
    
    Args:
        entity_name: 实体名称
        reasoning_type: 可选的推理类型过滤
        round_goal: 可选的轮次目标过滤
        
    Returns:
        List[Dict[str, Any]]: 推理记录列表，按时间戳排序
    """
    try:
        vector_store = get_vector_store(REASONING_COLLECTION)
        if vector_store is None:
            return []
            
        # 构建过滤条件
        filter_dict = {"entity_name": entity_name}
        if reasoning_type:
            filter_dict["reasoning_type"] = reasoning_type
        if round_goal:
            filter_dict["round_goal"] = round_goal
            
        # 获取所有匹配记录
        results = vector_store.similarity_search_with_score(
            entity_name,  # 使用实体名称作为基础查询
            k=100,  # 设置较大值以获取所有记录
            filter=filter_dict
        )
        
        # 解析结果
        reasoning_records = []
        for doc, _ in results:
            if doc.metadata.get("is_reasoning"):
                try:
                    record = json.loads(doc.page_content)
                    reasoning_records.append(record)
                except:
                    pass
                    
        # 按时间戳排序
        reasoning_records.sort(key=lambda x: x.get("timestamp", 0))
        return reasoning_records
    except Exception as e:
        logger.log(f"❌ 检索实体推理历史失败: {e}", level="error", role="memory")
        return []

def extract_decisions_from_qa(qa_history: List[Dict[str, str]]) -> List[str]:
    """
    从问答历史中提取关键决策点。
    
    Args:
        qa_history: 问答历史列表
        
    Returns:
        List[str]: 关键决策列表
    """
    decisions = []
    
    for qa in qa_history:
        question = qa.get("question", "")
        answer = qa.get("answer", "")
        
        # 添加包含决策关键词的答案
        if any(kw in answer.lower() for kw in ["应该", "决定", "选择", "采用", "使用", "定义", "确定", "建议"]):
            # 提取答案中的关键信息（简化处理，实际应用可能需要LLM提取）
            decisions.append(answer.strip())
    
    return decisions

def retrieve_similar_documents(
    query: str,
    collection_name: str = REASONING_COLLECTION,
    top_k: int = DEFAULT_TOP_K,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    根据查询检索相似文档。
    
    Args:
        query: 查询文本
        collection_name: 集合名称
        top_k: 返回结果数量
        filter_dict: 过滤条件
        
    Returns:
        List[Dict[str, Any]]: 相似文档列表
    """
    try:
        vector_store = get_vector_store(collection_name)
        if vector_store is None:
            return []
            
        # 执行相似度搜索
        results = vector_store.similarity_search_with_score(query, k=top_k, filter=filter_dict)
        
        # 解析结果
        documents = []
        for doc, score in results:
            try:
                # 解析文档内容
                document_data = json.loads(doc.page_content)
                # 添加元数据
                for key, value in doc.metadata.items():
                    document_data[key] = value
                # 添加相似度分数
                document_data["search_score"] = float(score)
                documents.append(document_data)
            except Exception as e:
                logger.log(f"❌ 解析文档失败: {e}", level="error", role="memory")
                
        return documents
    except Exception as e:
        logger.log(f"❌ 检索相似文档失败: {e}", level="error", role="memory")
        return []

# 为兼容测试添加的函数
async def store_reasoning_results(
    entity_name: str,
    round_goal: str,
    qa_history: List[Dict[str, str]],
    decisions: List[str],
    updated_summary: Optional[Dict[str, Any]] = None
) -> bool:
    """
    存储推理结果(兼容测试用例)
    
    Args:
        entity_name: 实体名称
        round_goal: 推理轮次目标
        qa_history: 问答历史列表
        decisions: 关键决策列表
        updated_summary: 更新后的实体摘要
        
    Returns:
        bool: 操作是否成功
    """
    metadata = {}
    if updated_summary:
        metadata["updated_summary"] = updated_summary
        
    return store_reasoning(
        entity_name=entity_name,
        reasoning_type="local",
        round_goal=round_goal,
        qa_history=qa_history,
        decisions=decisions,
        metadata=metadata
    )

# 添加异步版本
async def retrieve_entity_reasoning_history_async(
    entity_name: str,
    reasoning_type: Optional[str] = None,
    round_goal: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    异步检索特定实体的推理历史(兼容测试用例)。
    
    Args:
        entity_name: 实体名称
        reasoning_type: 可选的推理类型过滤
        round_goal: 可选的轮次目标过滤
        
    Returns:
        List[Dict[str, Any]]: 推理记录列表，按时间戳排序
    """
    # 调用同步版本
    return retrieve_entity_reasoning_history(
        entity_name=entity_name,
        reasoning_type=reasoning_type,
        round_goal=round_goal
    ) 