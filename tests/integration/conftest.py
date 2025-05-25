"""
集成测试的conftest配置
导入通用fixture以确保pytest可以发现它们
"""

import pytest
import os
import sys
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent.parent.absolute()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# 导入所有fixture
from tests.fixtures.conftest import *
from tests.fixtures.mock_models import *

# 添加知识库测试所需的fixture
@pytest.fixture
def mock_vector_store():
    """提供模拟的向量存储"""
    class MockVectorStore:
        def __init__(self):
            self.call_history = []
            self.documents = []
        
        def add_documents(self, documents, **kwargs):
            self.call_history.append(("add_documents", documents, kwargs))
            self.documents.extend(documents)
            return True
            
        def similarity_search(self, query, **kwargs):
            self.call_history.append(("similarity_search", query, kwargs))
            return self.documents[:min(len(self.documents), kwargs.get("k", 4))]
            
        def similarity_search_with_score(self, query, **kwargs):
            self.call_history.append(("similarity_search_with_score", query, kwargs))
            return [(doc, 0.95) for doc in self.documents[:min(len(self.documents), kwargs.get("k", 4))]]
    
    return MockVectorStore()

@pytest.fixture
def mock_entity_storage():
    """提供模拟的实体存储"""
    class MockEntityStorage:
        def __init__(self):
            self.entities = {
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
        
        async def retrieve_entity(self, name):
            return self.entities.get(name)
            
        async def store_entity_summary(self, name, summary):
            self.entities[name] = summary
            return True
    
    return MockEntityStorage() 