"""
模拟模型fixtures
提供各种测试场景下需要的模拟对象和数据
"""

import json
from typing import Dict, List, Any, Optional, Callable

class MockLLM:
    """用于测试的模拟LLM客户端"""
    
    def __init__(self, responses: Dict[str, str] = None):
        """
        初始化模拟LLM客户端
        
        Args:
            responses: 预定义的问题和回答字典
        """
        self.responses = responses or {}
        self.default_response = json.dumps({
            "analysis": "这是一个模拟分析结果",
            "suggestions": ["建议1", "建议2", "建议3"],
            "code_examples": [],
        })
        self.call_history = []
    
    async def acompletion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        模拟异步完成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 模拟响应
        """
        prompt = " ".join([m.get("content", "") for m in messages])
        self.call_history.append({"messages": messages, "kwargs": kwargs})
        
        for key, response in self.responses.items():
            if key in prompt:
                return {"choices": [{"message": {"content": response}}]}
        
        return {"choices": [{"message": {"content": self.default_response}}]}
    
    def add_response(self, key: str, response: str):
        """
        添加预定义响应
        
        Args:
            key: 触发关键词
            response: 对应的响应
        """
        self.responses[key] = response
    
    def get_call_count(self) -> int:
        """获取调用次数"""
        return len(self.call_history)
    
    def reset(self):
        """重置调用历史"""
        self.call_history = []


class MockVectorStore:
    """用于测试的模拟向量存储"""
    
    def __init__(self, documents: Dict[str, List[Dict[str, Any]]] = None):
        """
        初始化模拟向量存储
        
        Args:
            documents: 预定义的文档集合
        """
        self.documents = documents or {}
        self.call_history = []
    
    def similarity_search_with_score(self, query: str, k: int = 3, **kwargs) -> List[tuple]:
        """
        模拟相似度搜索
        
        Args:
            query: 查询字符串
            k: 返回结果数量
            **kwargs: 其他参数
            
        Returns:
            List[tuple]: 文档和分数对的列表
        """
        self.call_history.append({"query": query, "k": k, "kwargs": kwargs})
        
        results = []
        for key, docs in self.documents.items():
            if key in query.lower() and docs:
                for i, doc in enumerate(docs[:k]):
                    score = 1.0 - (i * 0.1)  # 模拟的相似度分数
                    results.append((doc, score))
        
        # 如果没有找到匹配的文档，返回默认文档
        if not results:
            default_doc = {"page_content": "这是默认文档内容", "metadata": {"source": "default"}}
            results = [(default_doc, 0.5)]
        
        return results
    
    def add_documents(self, documents: List[Dict[str, Any]], collection_name: str = "default"):
        """
        添加文档到存储
        
        Args:
            documents: 文档列表
            collection_name: 集合名称
        """
        self.documents[collection_name] = documents
    
    def reset(self):
        """重置调用历史"""
        self.call_history = []


class MockEntityStorage:
    """用于测试的模拟实体存储"""
    
    def __init__(self, entities: Dict[str, Dict[str, Any]] = None):
        """
        初始化模拟实体存储
        
        Args:
            entities: 预定义的实体字典
        """
        self.entities = entities or {}
        self.call_history = []
    
    async def store_entity_summary(self, entity_name: str, summary: Dict[str, Any]) -> bool:
        """
        存储实体摘要
        
        Args:
            entity_name: 实体名称
            summary: 实体摘要
            
        Returns:
            bool: 操作是否成功
        """
        self.call_history.append({"operation": "store", "entity_name": entity_name, "summary": summary})
        self.entities[entity_name] = summary
        return True
    
    async def retrieve_entity(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        检索实体
        
        Args:
            entity_name: 实体名称
            
        Returns:
            Optional[Dict[str, Any]]: 实体摘要或None
        """
        self.call_history.append({"operation": "retrieve", "entity_name": entity_name})
        return self.entities.get(entity_name)
    
    def reset(self):
        """重置调用历史"""
        self.call_history = []


# 预定义的回答
PREDEFINED_RESPONSES = {
    "UserService": json.dumps({
        "module": "用户认证与资料管理服务",
        "description": "负责用户注册、登录、个人资料管理和认证授权",
        "components": ["AuthController", "ProfileService", "UserRepository"],
        "interfaces": ["REST API", "Cognito/Auth0集成"],
        "dependencies": ["评估服务", "通知服务"]
    }),
    "AssessmentService": json.dumps({
        "module": "评估与路径建议服务",
        "description": "管理移民申请者的资格评估流程与路径建议",
        "components": ["AssessmentController", "EligibilityService", "PathwayRecommendationEngine"],
        "interfaces": ["REST API", "OpenAI集成"],
        "dependencies": ["用户服务", "表格服务"]
    }),
    "FormService": json.dumps({
        "module": "智能表格生成服务",
        "description": "自动生成和管理加拿大移民申请表格",
        "components": ["FormController", "FormGenerationService", "PDFGenerator"],
        "interfaces": ["REST API", "PDF生成API"],
        "dependencies": ["用户服务", "文档服务"]
    }),
    "DocumentService": json.dumps({
        "module": "文档管理与分析服务",
        "description": "管理用户上传的所有文档及内容分析",
        "components": ["DocumentController", "DocumentAnalysisService", "StorageService"],
        "interfaces": ["REST API", "S3/Blob存储API"],
        "dependencies": ["用户服务", "表格服务"]
    }),
    "ConsultantService": json.dumps({
        "module": "顾问匹配与协作服务",
        "description": "管理客户和移民顾问之间的匹配与协作",
        "components": ["ConsultantController", "MatchingService", "WorkspaceService"],
        "interfaces": ["REST API", "实时消息API"],
        "dependencies": ["用户服务", "文档服务", "表格服务"]
    }),
    "架构风格": json.dumps({
        "系统类型": "加拿大移民申请SaaS平台",
        "架构风格": "Serverless架构",
        "前端": "Next.js + React",
        "后端": "Serverless函数 (Node.js)",
        "数据库": ["MongoDB Atlas"],
        "云服务": ["AWS Lambda/Azure Functions", "S3/Blob存储", "Cognito/Auth0"]
    }),
    "全局约束": json.dumps({
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
    })
} 