"""
知识管理模块集成测试
测试knowledge中的实际API接口
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 导入被测模块
from knowledge.vector_store import get_vector_store, create_vector_store, create_vector_store_async
from knowledge.entity_storage import store_entity_summary, retrieve_entity, retrieve_entity_async
from knowledge.context_retrieval import build_context_for_round
from knowledge.reasoning_memory import store_reasoning_results, retrieve_entity_reasoning_history, retrieve_entity_reasoning_history_async

# 测试向量存储功能
@pytest.mark.asyncio
async def test_vector_store_operations():
    """测试向量存储的基本操作"""
    
    # 模拟Qdrant客户端
    mock_qdrant = MagicMock()
    mock_client = MagicMock()
    mock_client.get_collections.return_value.collections = []
    
    with patch("knowledge.vector_store.QdrantClient", return_value=mock_client), \
         patch("knowledge.vector_store.Qdrant", return_value=mock_qdrant), \
         patch("knowledge.vector_store.get_embedding_model"):
        
        # 测试获取向量存储
        vector_store = get_vector_store("test_collection")
        assert vector_store is not None
        assert isinstance(vector_store, MagicMock)
        
        # 测试创建向量存储 - 使用异步版本
        documents = ["测试文档1", "测试文档2"]
        result = await create_vector_store_async(documents, "test_collection")
        assert result is not None

# 测试实体存储功能
@pytest.mark.asyncio
async def test_entity_storage_operations(mock_vector_store):
    """测试实体存储的基本操作"""
    
    # 模拟依赖
    with patch("knowledge.entity_storage.get_vector_store", return_value=mock_vector_store), \
         patch("knowledge.entity_storage.get_embedding_model"):
        
        # 测试存储实体摘要
        entity_name = "AssessmentService"
        summary = {
            "module": "评估与路径建议服务",
            "description": "管理移民申请者的资格评估流程与路径建议",
            "components": ["AssessmentController", "EligibilityService", "PathwayRecommendationEngine"],
            "interfaces": ["REST API", "OpenAI集成"],
            "dependencies": ["UserService", "FormService"]
        }
        
        # 存储实体
        result = await store_entity_summary(entity_name, summary)
        assert result is True
        
        # 检查调用历史
        assert len(mock_vector_store.call_history) > 0
        
        # 测试检索实体
        with patch("knowledge.entity_storage.retrieve_entity_async", 
                  return_value=summary):
            
            entity = await retrieve_entity_async(entity_name)
            assert entity is not None
            assert entity["module"] == "评估与路径建议服务"

# 测试上下文检索功能
@pytest.mark.asyncio
async def test_context_retrieval(mock_entity_storage):
    """测试上下文检索功能"""
    
    # 模拟依赖
    with patch("knowledge.context_retrieval.retrieve_entity", side_effect=mock_entity_storage.retrieve_entity), \
         patch("knowledge.context_retrieval.retrieve_entity_reasoning_history", 
              return_value=[
                  {"round_goal": "上下文理解", "decisions": ["决定1", "决定2"]},
                  {"round_goal": "架构模式", "decisions": ["决定3", "决定4"]}
              ]), \
         patch("knowledge.context_retrieval.retrieve_related_reasoning", 
              return_value=[
                  {"entity_name": "FormService", "round_goal": "上下文理解", "decisions": ["决定5", "决定6"]}
              ]):
        
        # 测试构建上下文
        context = await build_context_for_round(
            entity_name="UserService",
            round_num=2,
            round_goal="架构模式与最佳实践应用",
            current_summary={"module": "用户认证与资料管理服务", "description": "管理用户身份验证和个人资料"},
            previous_qa=[{"question": "问题1", "answer": "回答1"}],
            global_constraints={"命名规范": {"类命名": "驼峰命名法"}}
        )
        
        # 验证结果
        assert context
        assert isinstance(context, str)
        assert "UserService" in context or "用户服务" in context
        assert "架构模式" in context
        assert "决定" in context
        assert "驼峰命名法" in context

# 测试推理记忆功能
@pytest.mark.asyncio
async def test_reasoning_memory(mock_vector_store):
    """测试推理记忆功能"""
    
    # 模拟依赖
    with patch("knowledge.reasoning_memory.get_vector_store", return_value=mock_vector_store):
        
        # 测试存储推理结果
        result = await store_reasoning_results(
            entity_name="DocumentService",
            round_goal="架构模式与最佳实践应用",
            qa_history=[{"question": "问题1", "answer": "回答1"}],
            decisions=["决定使用Serverless函数", "决定集成S3存储", "决定使用OpenAI进行文档分析"],
            updated_summary={"module": "文档管理与分析服务", "description": "管理用户上传的所有文档及内容分析"}
        )
        
        assert result is True
        assert len(mock_vector_store.call_history) > 0
        
        # 测试检索推理历史
        expected_result = [
            {"entity_name": "DocumentService", 
             "round_goal": "架构模式与最佳实践应用",
             "decisions": ["决定使用Serverless函数", "决定集成S3存储", "决定使用OpenAI进行文档分析"],
             "search_score": 0.95}
        ]
        with patch("knowledge.reasoning_memory.retrieve_similar_documents", 
                  return_value=expected_result):
            
            history = await retrieve_entity_reasoning_history_async("DocumentService")
            assert history
            assert isinstance(history, list)
            assert len(history) > 0
            assert "决定使用Serverless函数" in history[0]["decisions"]

# 测试完整知识流程
@pytest.mark.asyncio
async def test_complete_knowledge_workflow(mock_vector_store, mock_entity_storage):
    """测试完整知识管理流程"""
    
    # 模拟所有依赖
    with patch("knowledge.vector_store.QdrantClient", return_value=MagicMock()), \
         patch("knowledge.vector_store.Qdrant", return_value=mock_vector_store), \
         patch("knowledge.vector_store.get_embedding_model"), \
         patch("knowledge.entity_storage.get_vector_store", return_value=mock_vector_store), \
         patch("knowledge.entity_storage.get_embedding_model"), \
         patch("knowledge.reasoning_memory.get_vector_store", return_value=mock_vector_store), \
         patch("knowledge.context_retrieval.retrieve_entity", side_effect=mock_entity_storage.retrieve_entity), \
         patch("knowledge.context_retrieval.retrieve_entity_reasoning_history", 
              return_value=[
                  {"round_goal": "上下文理解", "decisions": ["决定1", "决定2"]}
              ]), \
         patch("knowledge.context_retrieval.retrieve_related_reasoning", 
              return_value=[]), \
         patch("knowledge.reasoning_memory.retrieve_entity_reasoning_history_async", 
              return_value=[
                  {"round_goal": "上下文理解", "decisions": ["决定1", "决定2"]}
              ]):
        
        # 1. 存储实体摘要
        entity_name = "ConsultantService"
        summary = {
            "module": "顾问匹配与协作服务",
            "description": "管理客户和移民顾问之间的匹配与协作",
            "components": ["ConsultantController", "MatchingService", "WorkspaceService"],
            "interfaces": ["REST API", "实时消息API"],
            "dependencies": ["UserService", "DocumentService", "FormService"]
        }
        
        await store_entity_summary(entity_name, summary)
        
        # 2. 构建推理上下文
        context = await build_context_for_round(
            entity_name=entity_name,
            round_num=1,
            round_goal="上下文理解与基础架构识别",
            current_summary=summary,
            previous_qa=[],
            global_constraints={"命名规范": {"类命名": "驼峰命名法"}}
        )
        
        assert context
        assert "顾问匹配" in context or "协作服务" in context
        
        # 3. 存储推理结果
        await store_reasoning_results(
            entity_name=entity_name,
            round_goal="上下文理解与基础架构识别",
            qa_history=[
                {"question": "这个服务的主要职责是什么?", 
                 "answer": "管理客户和移民顾问之间的匹配与协作，包括顾问匹配算法、预约管理和协作工作区"}
            ],
            decisions=["确定使用实时通信技术", "确定需要顾问匹配算法", "确定使用MongoDB存储工作区数据"],
            updated_summary=summary
        )
        
        # 4. 检索实体和推理历史
        with patch("knowledge.entity_storage.retrieve_entity_async",
                  return_value=summary), \
             patch("knowledge.reasoning_memory.retrieve_similar_documents",
                  return_value=[
                      {"entity_name": entity_name, 
                       "round_goal": "上下文理解与基础架构识别",
                       "decisions": ["确定使用实时通信技术", "确定需要顾问匹配算法"],
                       "search_score": 0.95}
                  ]):
            
            # 检索实体 - 使用异步版本
            entity = await retrieve_entity_async(entity_name)
            assert entity is not None
            assert entity["module"] == "顾问匹配与协作服务"
            
            # 检索推理历史 - 使用异步版本
            history = await retrieve_entity_reasoning_history_async(entity_name)
            assert history
            assert len(history) > 0
            assert "上下文理解" in history[0]["round_goal"] 