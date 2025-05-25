"""
文档处理模块集成测试
测试document_processing中的实际API接口
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 导入被测模块
from document_processing.entity_discovery import discover_entities
from document_processing.content_analyzer import analyze_document_content
from document_processing.initial_summarizer import generate_initial_summary

@pytest.mark.asyncio
async def test_discover_entities(mock_llm, sample_input_text):
    """测试实体发现功能"""
    
    # 模拟LLM客户端
    with patch("document_processing.entity_discovery.run_prompt", side_effect=async_mock_discover_entities):
        
        # 执行测试
        entities = await discover_entities(sample_input_text)
        
        # 验证结果
        assert entities
        assert isinstance(entities, list)
        assert len(entities) >= 3  # 至少有3个实体
        
        # 验证实体格式
        for entity in entities:
            assert "name" in entity
            assert "type" in entity
            assert "parent" in entity

@pytest.mark.asyncio
async def test_analyze_document_content(mock_llm, sample_input_text):
    """测试文档内容分析功能"""
    
    # 模拟LLM客户端
    with patch("document_processing.content_analyzer.run_prompt", side_effect=async_mock_content_analysis):
        
        # 执行测试
        analysis = await analyze_document_content(sample_input_text)
        
        # 验证结果
        assert analysis
        assert isinstance(analysis, dict)
        assert "system_type" in analysis
        assert "main_components" in analysis
        assert "dependencies" in analysis
        assert "technology_stack" in analysis
        
        # 验证内容
        assert "移民申请" in analysis["system_type"]
        assert len(analysis["main_components"]) >= 3
        assert "Node.js" in analysis["technology_stack"]["backend"]

@pytest.mark.asyncio
async def test_generate_initial_summary(mock_llm):
    """测试初始摘要生成功能"""
    
    entity = {"name": "UserService", "type": "Service", "parent": "Core"}
    context = "UserService负责处理所有与用户账户相关的操作，包括用户注册与登录、个人信息管理等。"
    
    # 模拟LLM客户端
    with patch("document_processing.initial_summarizer.run_prompt", side_effect=mock_generate_summary):
        
        # 执行测试
        summary = await generate_initial_summary(entity, context)
        
        # 验证结果
        assert summary
        assert isinstance(summary, dict)
        assert "module" in summary
        assert "description" in summary
        assert "components" in summary
        assert "interfaces" in summary
        assert "dependencies" in summary
        
        # 验证具体字段
        assert summary["module"] == "用户认证与资料管理服务"
        assert "用户注册" in summary["description"]
        assert len(summary["components"]) >= 2
        assert "REST API" in summary["interfaces"]

@pytest.mark.asyncio
async def test_process_input_documents(mock_llm, sample_input_files):
    """测试完整文档处理流程"""
    
    # 模拟所有相关函数
    with patch("document_processing.content_analyzer.run_prompt", side_effect=async_mock_content_analysis), \
         patch("document_processing.entity_discovery.run_prompt", side_effect=async_mock_discover_entities):
        
        # 读取文档文件
        all_text = ""
        for file_path in sorted(sample_input_files.glob("*.md")):
            all_text += f"\n\n### FILE: {file_path.name} ###\n\n"
            all_text += file_path.read_text(encoding="utf-8")
        
        # 测试内容分析
        analysis = await analyze_document_content(all_text)
        assert analysis and isinstance(analysis, dict)
        
        # 测试实体发现
        entities = await discover_entities(all_text)
        assert entities and isinstance(entities, list)
        
        # 为每个实体生成初始摘要
        with patch("document_processing.initial_summarizer.run_prompt", side_effect=async_mock_initial_summary):
            for entity in entities[:2]:  # 仅测试前两个实体
                summary = await generate_initial_summary(entity, all_text)
                assert summary and isinstance(summary, dict)
                assert "module" in summary
                assert "description" in summary

# 模拟异步函数

async def async_mock_discover_entities(*args, **kwargs):
    """模拟实体发现结果"""
    return [
        {"name": "UserService", "type": "Service", "parent": "Core"},
        {"name": "AssessmentService", "type": "Service", "parent": "Core"},
        {"name": "FormService", "type": "Service", "parent": "Core"},
        {"name": "DocumentService", "type": "Service", "parent": "Core"},
        {"name": "ConsultantService", "type": "Service", "parent": "Core"}
    ]

async def async_mock_content_analysis(*args, **kwargs):
    """模拟文档内容分析结果"""
    return {
        "system_type": "加拿大移民申请SaaS平台",
        "description": "为申请人提供加拿大移民申请流程指导、评估和表格处理的智能平台，支持顾问匹配和协作",
        "main_components": [
            "用户认证与资料管理服务",
            "评估与路径建议服务",
            "智能表格生成服务",
            "文档管理与分析服务",
            "顾问匹配与协作服务"
        ],
        "dependencies": [
            {"source": "评估服务", "target": "用户服务", "type": "uses"},
            {"source": "表格服务", "target": "用户服务", "type": "uses"},
            {"source": "表格服务", "target": "文档服务", "type": "uses"},
            {"source": "顾问服务", "target": "用户服务", "type": "uses"}
        ],
        "technology_stack": {
            "frontend": "Next.js + React + Tailwind CSS",
            "backend": "Serverless函数 (Node.js)",
            "database": ["MongoDB Atlas"],
            "storage": "AWS S3 / Azure Blob Storage",
            "authentication": "AWS Cognito / Auth0",
            "ai": "OpenAI API"
        }
    }

async def async_mock_initial_summary(*args, **kwargs):
    """模拟初始摘要生成结果"""
    # 从kwargs中获取实体和上下文
    entity = kwargs.get("entity", {})
    if not entity and "prompt_template" in kwargs:
        # 如果没有直接提供实体，尝试从prompt_template中提取
        return {
            "module": "用户认证与资料管理服务",
            "description": "负责用户注册、登录、个人资料管理和认证授权",
            "components": ["AuthController", "ProfileService", "UserRepository"],
            "interfaces": ["REST API", "Cognito/Auth0集成"],
            "dependencies": ["评估服务", "通知服务"],
            "frontend": {
                "pages": ["登录页", "注册页", "用户档案页"],
                "components": ["登录表单", "注册表单", "个人资料表单"],
                "routes": ["/login", "/register", "/profile"]
            },
            "backend": {
                "controllers": ["AuthController", "ProfileController"],
                "services": ["AuthService", "ProfileService"],
                "repositories": ["UserRepository"],
                "api": ["/api/auth", "/api/profile"]
            }
        }
    
    entity_name = entity.get("name", "Unknown") if entity else "Unknown"
    
    if "UserService" in entity_name:
        return {
            "module": "用户认证与资料管理服务",
            "description": "负责用户注册、登录、个人资料管理和认证授权",
            "components": ["AuthController", "ProfileService", "UserRepository"],
            "interfaces": ["REST API", "Cognito/Auth0集成"],
            "dependencies": ["评估服务", "通知服务"],
            "frontend": {
                "pages": ["登录页", "注册页", "用户档案页"],
                "components": ["登录表单", "注册表单", "个人资料表单"],
                "routes": ["/login", "/register", "/profile"]
            },
            "backend": {
                "controllers": ["AuthController", "ProfileController"],
                "services": ["AuthService", "ProfileService"],
                "repositories": ["UserRepository"],
                "api": ["/api/auth", "/api/profile"]
            }
        }
    elif "AssessmentService" in entity_name:
        return {
            "module": "评估与路径建议服务",
            "description": "管理移民申请者的资格评估流程与路径建议",
            "components": ["AssessmentController", "EligibilityService", "PathwayRecommendationEngine"],
            "interfaces": ["REST API", "OpenAI集成"],
            "dependencies": ["用户服务", "表格服务"],
            "frontend": {
                "pages": ["评估问卷页", "评估结果页", "路径比较页"],
                "components": ["评估步骤导航", "问卷表单", "评分卡片"],
                "routes": ["/assessment", "/assessment/results", "/pathways/compare"]
            },
            "backend": {
                "controllers": ["AssessmentController", "PathwayController"],
                "services": ["EligibilityService", "RecommendationService"],
                "repositories": ["AssessmentRepository", "ProgramRepository"],
                "api": ["/api/assessments", "/api/pathways"]
            }
        }
    elif "FormService" in entity_name:
        return {
            "module": "智能表格生成服务",
            "description": "自动生成和管理加拿大移民申请表格",
            "components": ["FormController", "FormGenerationService", "PDFGenerator"],
            "interfaces": ["REST API", "PDF生成API"],
            "dependencies": ["用户服务", "文档服务"],
            "frontend": {
                "pages": ["表格列表页", "表格编辑页", "表格预览页"],
                "components": ["表格生成向导", "表格编辑器", "PDF预览器"],
                "routes": ["/forms", "/forms/:id/edit", "/forms/:id/preview"]
            },
            "backend": {
                "controllers": ["FormController", "TemplateController"],
                "services": ["FormGenerationService", "ValidationService"],
                "repositories": ["FormRepository", "TemplateRepository"],
                "api": ["/api/forms", "/api/templates"]
            }
        }
    elif "DocumentService" in entity_name:
        return {
            "module": "文档管理与分析服务",
            "description": "管理用户上传的所有文档及内容分析",
            "components": ["DocumentController", "DocumentAnalysisService", "StorageService"],
            "interfaces": ["REST API", "S3/Blob存储API"],
            "dependencies": ["用户服务", "表格服务"],
            "frontend": {
                "pages": ["文档上传页", "文档列表页", "文档详情页"],
                "components": ["文档上传器", "文件列表", "文档分析结果"],
                "routes": ["/documents/upload", "/documents", "/documents/:id"]
            },
            "backend": {
                "controllers": ["DocumentController", "AnalysisController"],
                "services": ["StorageService", "AnalysisService"],
                "repositories": ["DocumentRepository"],
                "api": ["/api/documents", "/api/documents/:id/analyze"]
            }
        }
    elif "ConsultantService" in entity_name:
        return {
            "module": "顾问匹配与协作服务",
            "description": "管理客户和移民顾问之间的匹配与协作",
            "components": ["ConsultantController", "MatchingService", "WorkspaceService"],
            "interfaces": ["REST API", "实时消息API"],
            "dependencies": ["用户服务", "文档服务", "表格服务"],
            "frontend": {
                "pages": ["顾问目录页", "预约页", "工作区页"],
                "components": ["顾问卡片", "预约日历", "消息聊天框"],
                "routes": ["/consultants", "/appointments", "/workspace/:id"]
            },
            "backend": {
                "controllers": ["ConsultantController", "WorkspaceController"],
                "services": ["MatchingService", "WorkspaceService"],
                "repositories": ["ConsultantRepository", "WorkspaceRepository"],
                "api": ["/api/consultants", "/api/workspaces"]
            }
        }
    else:
        return {
            "module": f"{entity_name}",
            "description": f"{entity_name}的默认描述",
            "components": ["Controller", "Service", "Repository"],
            "interfaces": ["REST API"],
            "dependencies": []
        }

# 添加一个专门用于test_generate_initial_summary的mock函数
async def mock_generate_summary(*args, **kwargs):
    """专门为test_generate_initial_summary测试设计的mock函数"""
    return {
        "module": "用户认证与资料管理服务",
        "description": "负责用户注册、登录、个人资料管理和认证授权",
        "components": ["AuthController", "ProfileService", "UserRepository"],
        "interfaces": ["REST API", "Cognito/Auth0集成"],
        "dependencies": ["评估服务", "通知服务"],
        "frontend": {
            "pages": ["登录页", "注册页", "用户档案页"],
            "components": ["登录表单", "注册表单", "个人资料表单"],
            "routes": ["/login", "/register", "/profile"]
        },
        "backend": {
            "controllers": ["AuthController", "ProfileController"],
            "services": ["AuthService", "ProfileService"],
            "repositories": ["UserRepository"],
            "api": ["/api/auth", "/api/profile"]
        }
    } 