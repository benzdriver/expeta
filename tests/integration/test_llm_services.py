"""
LLM服务模块集成测试
测试llm_services中的实际API接口
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

# 导入被测模块
from llm_services.executor import run_prompt
from llm_services.client_factory import get_embedding_client
from llm_services.chat import chat_completion
from llm_services.rag import retrieve_context_for_entity

@pytest.fixture
def setup_env_vars():
    """设置测试环境变量"""
    os.environ["OPENAI_API_KEY"] = "test-api-key"
    yield
    os.environ.pop("OPENAI_API_KEY", None)

@pytest.mark.asyncio
async def test_run_prompt_with_parsing(setup_env_vars, mock_llm):
    """测试LLM执行器带解析功能"""
    
    # 模拟OpenAI客户端
    with patch("llm_services.executor.ChatOpenAI", return_value=mock_llm):
        
        # 定义解析函数
        def parse_result(text):
            try:
                return json.loads(text)
            except:
                return {"error": "解析失败"}
        
        # 执行测试
        result = await run_prompt(
            user_message="分析UserService模块",
            system_message="你是一个架构分析工具",
            model="gpt-4",
            parse_response=parse_result
        )
        
        # 验证结果
        assert "module" in result
        assert result["module"] == "用户认证与资料管理服务"
        assert "components" in result
        assert len(result["components"]) > 0
        assert "AuthController" in result["components"]
        
        # 验证模型调用
        assert mock_llm.get_call_count() == 1
        assert "你是一个架构分析工具" in mock_llm.call_history[0]["messages"][0]["content"]

@pytest.mark.asyncio
async def test_run_prompt_with_chunking(setup_env_vars, mock_llm, sample_input_text):
    """测试LLM执行器的自动分块功能"""
    
    # 模拟OpenAI客户端
    with patch("llm_services.executor.ChatOpenAI", return_value=mock_llm):
        
        # 定义结果合并函数
        def merge_results(accumulated_result, new_result):
            if not accumulated_result:
                return new_result
            if isinstance(accumulated_result, dict) and isinstance(new_result, dict):
                accumulated_result.update(new_result)
                return accumulated_result
            return accumulated_result
        
        # 执行测试
        result = await run_prompt(
            user_message=sample_input_text,  # 较长文本
            system_message="分析这些服务模块",
            model="gpt-4",
            max_input_tokens=1000,  # 设置较小的分块大小
            parse_response=json.loads,
            merge_result=merge_results
        )
        
        # 验证结果
        assert isinstance(result, dict)
        assert mock_llm.get_call_count() > 1  # 应该被多次调用

@pytest.mark.asyncio
async def test_chat_completion(setup_env_vars, mock_llm):
    """测试聊天完成功能"""
    
    # 模拟OpenAI客户端
    with patch("llm_services.chat.ChatOpenAI", return_value=mock_llm):
        
        # 执行测试
        messages = [
            {"role": "system", "content": "你是一个架构设计助手"},
            {"role": "user", "content": "分析架构风格"}
        ]
        
        response = await chat_completion(messages, model="gpt-4")
        
        # 验证结果
        assert "系统类型" in response
        assert "架构风格" in response
        assert "Serverless架构" in response
        assert "加拿大移民申请" in response
        
        # 验证模型调用
        assert mock_llm.get_call_count() == 1
        assert messages[0]["content"] in mock_llm.call_history[0]["messages"][0]["content"]

@pytest.mark.asyncio
async def test_retrieve_context_for_entity(setup_env_vars, mock_vector_store, sample_input_text):
    """测试实体上下文检索功能"""
    
    # 模拟向量存储
    with patch("llm_services.rag.get_vector_store", return_value=mock_vector_store):
        
        # 执行测试
        context = await retrieve_context_for_entity("AssessmentService", sample_input_text)
        
        # 验证结果
        assert context
        assert isinstance(context, str)
        assert "AssessmentService" in context or "评估服务" in context or "路径建议" in context
        
        # 验证向量存储调用
        assert len(mock_vector_store.call_history) > 0
        assert "AssessmentService" in mock_vector_store.call_history[0]["query"]

@pytest.mark.asyncio
async def test_get_embedding_client(setup_env_vars):
    """测试嵌入客户端工厂"""
    
    # 模拟嵌入模型
    mock_embeddings = MagicMock()
    
    with patch("llm_services.client_factory.OpenAIEmbeddings", return_value=mock_embeddings):
        
        # 执行测试
        client = get_embedding_client()
        
        # 验证结果
        assert client is not None
        assert client == mock_embeddings 