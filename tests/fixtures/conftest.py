"""
测试配置文件
提供通用的pytest fixtures
"""

import os
import json
import pytest
import asyncio
from pathlib import Path
from typing import Dict, List, Any

from tests.fixtures.test_documents import (
    SAMPLE_ARCHITECTURE_DOC,
    SAMPLE_USER_SERVICE_DOC,
    SAMPLE_ASSESSMENT_SERVICE_DOC,
    SAMPLE_FORM_SERVICE_DOC,
    SAMPLE_DOCUMENT_SERVICE_DOC,
    SAMPLE_CONSULTANT_SERVICE_DOC,
    SAMPLE_API_DOCS
)
from tests.fixtures.mock_models import (
    MockLLM,
    MockVectorStore,
    MockEntityStorage,
    PREDEFINED_RESPONSES
)

# 配置临时测试目录
@pytest.fixture
def test_data_dir(tmp_path):
    """创建测试数据目录"""
    data_dir = tmp_path / "data"
    (data_dir / "input").mkdir(parents=True)
    (data_dir / "output").mkdir(parents=True)
    return data_dir

@pytest.fixture
def sample_input_files(test_data_dir):
    """创建样例输入文件"""
    input_dir = test_data_dir / "input"
    
    # 创建文档文件
    with open(input_dir / "architecture.md", "w", encoding="utf-8") as f:
        f.write(SAMPLE_ARCHITECTURE_DOC)
    
    with open(input_dir / "user_service.md", "w", encoding="utf-8") as f:
        f.write(SAMPLE_USER_SERVICE_DOC)
    
    with open(input_dir / "assessment_service.md", "w", encoding="utf-8") as f:
        f.write(SAMPLE_ASSESSMENT_SERVICE_DOC)
    
    with open(input_dir / "form_service.md", "w", encoding="utf-8") as f:
        f.write(SAMPLE_FORM_SERVICE_DOC)
    
    with open(input_dir / "document_service.md", "w", encoding="utf-8") as f:
        f.write(SAMPLE_DOCUMENT_SERVICE_DOC)
    
    with open(input_dir / "consultant_service.md", "w", encoding="utf-8") as f:
        f.write(SAMPLE_CONSULTANT_SERVICE_DOC)
    
    return input_dir

@pytest.fixture
def sample_entity_data():
    """提供样例实体数据"""
    return {
        "UserService": {
            "name": "UserService",
            "type": "Service",
            "parent": "Core"
        },
        "AssessmentService": {
            "name": "AssessmentService",
            "type": "Service",
            "parent": "Core"
        },
        "FormService": {
            "name": "FormService",
            "type": "Service",
            "parent": "Core"
        },
        "DocumentService": {
            "name": "DocumentService",
            "type": "Service",
            "parent": "Core"
        },
        "ConsultantService": {
            "name": "ConsultantService",
            "type": "Service",
            "parent": "Core"
        }
    }

@pytest.fixture
def mock_llm():
    """提供模拟LLM客户端"""
    llm = MockLLM(responses=PREDEFINED_RESPONSES)
    return llm

@pytest.fixture
def mock_vector_store():
    """提供模拟向量存储"""
    vector_store = MockVectorStore()
    
    # 添加样例数据
    docs = [
        {"page_content": SAMPLE_USER_SERVICE_DOC, "metadata": {"source": "user_service.md"}},
        {"page_content": SAMPLE_ASSESSMENT_SERVICE_DOC, "metadata": {"source": "assessment_service.md"}},
        {"page_content": SAMPLE_FORM_SERVICE_DOC, "metadata": {"source": "form_service.md"}},
        {"page_content": SAMPLE_DOCUMENT_SERVICE_DOC, "metadata": {"source": "document_service.md"}},
        {"page_content": SAMPLE_CONSULTANT_SERVICE_DOC, "metadata": {"source": "consultant_service.md"}}
    ]
    vector_store.add_documents(docs, "user_service")
    vector_store.add_documents(docs, "assessment_service")
    vector_store.add_documents(docs, "form_service")
    vector_store.add_documents(docs, "document_service")
    vector_store.add_documents(docs, "consultant_service")
    
    return vector_store

@pytest.fixture
def mock_entity_storage():
    """提供模拟实体存储"""
    entity_storage = MockEntityStorage()
    
    # 添加样例实体
    entity_storage.entities = {
        "UserService": {
            "module": "用户认证与资料管理服务",
            "description": "负责用户注册、登录、个人资料管理和认证授权",
            "components": ["AuthController", "ProfileService", "UserRepository"],
            "interfaces": ["REST API", "Cognito/Auth0集成"],
            "dependencies": ["评估服务", "通知服务"]
        },
        "AssessmentService": {
            "module": "评估与路径建议服务",
            "description": "管理移民申请者的资格评估流程与路径建议",
            "components": ["AssessmentController", "EligibilityService", "PathwayRecommendationEngine"],
            "interfaces": ["REST API", "OpenAI集成"],
            "dependencies": ["用户服务", "表格服务"]
        },
        "FormService": {
            "module": "智能表格生成服务",
            "description": "自动生成和管理加拿大移民申请表格",
            "components": ["FormController", "FormGenerationService", "PDFGenerator"],
            "interfaces": ["REST API", "PDF生成API"],
            "dependencies": ["用户服务", "文档服务"]
        }
    }
    
    return entity_storage

@pytest.fixture
def sample_input_text():
    """提供样例输入文本"""
    return "\n\n".join(SAMPLE_API_DOCS)

@pytest.fixture
def sample_global_constraints():
    """提供样例全局约束"""
    return {
        "命名规范": {
            "类命名": "驼峰命名法",
            "方法命名": "小驼峰命名法",
            "常量命名": "全大写下划线分隔"
        },
        "API设计": {
            "REST规范": "遵循RESTful设计原则",
            "版本控制": "URL路径版本控制(如/api/v1/)"
        },
        "安全规范": {
            "认证": "JWT认证",
            "授权": "基于角色的访问控制(RBAC)",
            "数据保护": "所有敏感数据加密存储"
        }
    }

# 注意：不再重新定义事件循环fixture，使用pytest-asyncio的loop_scope标记
# 在pytest.ini中已设置：asyncio_mode = auto 