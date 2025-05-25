"""
推理模块集成测试
测试reasoning中的全局和局部推理功能
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 导入全局推理模块
from reasoning.global_reasoning.system_analyzer import analyze_system
from reasoning.global_reasoning.constraints_generator import generate_constraints
from reasoning.global_reasoning.global_chain import run_global_reasoning

# 导入局部推理模块
from reasoning.local_reasoning.context_builder import build_reasoning_context
from reasoning.local_reasoning.question_generators import generate_questions
from reasoning.local_reasoning.answer_generators import generate_answer
from reasoning.local_reasoning.summary_updaters import update_entity_summary
from reasoning.local_reasoning.local_chain import run_local_reasoning

@pytest.mark.asyncio
async def test_global_reasoning_system_analyzer(mock_llm, sample_input_text):
    """测试系统分析器功能"""
    
    # 模拟LLM客户端
    with patch("reasoning.global_reasoning.system_analyzer.run_prompt", side_effect=async_mock_system_analysis):
        
        # 执行测试
        analysis = await analyze_system(sample_input_text)
        
        # 验证结果
        assert analysis
        assert isinstance(analysis, dict)
        assert "system_type" in analysis
        assert "architecture_style" in analysis
        assert "technology_stack" in analysis
        
        # 验证内容
        assert "移民申请" in analysis["system_type"]
        assert "Serverless" in analysis["architecture_style"]
        assert "Node.js" in analysis["technology_stack"]["backend"]

@pytest.mark.asyncio
async def test_global_reasoning_constraints_generator(mock_llm, sample_input_text):
    """测试约束生成器功能"""
    
    # 模拟系统分析结果
    system_analysis = {
        "system_type": "加拿大移民申请SaaS平台",
        "architecture_style": "Serverless架构",
        "technology_stack": {
            "frontend": "Next.js + React",
            "backend": "Serverless函数 (Node.js)",
            "database": ["MongoDB Atlas"]
        }
    }
    
    # 模拟LLM客户端
    with patch("reasoning.global_reasoning.constraints_generator.run_prompt", side_effect=async_mock_constraints_generation):
        
        # 执行测试
        constraints = await generate_constraints(system_analysis, sample_input_text)
        
        # 验证结果
        assert constraints
        assert isinstance(constraints, dict)
        assert "命名规范" in constraints
        assert "API设计" in constraints
        assert "安全规范" in constraints
        
        # 验证内容
        assert "驼峰命名法" in constraints["命名规范"]["类命名"]
        assert "REST规范" in constraints["API设计"]
        assert "JWT" in constraints["安全规范"]["认证"]

@pytest.mark.asyncio
async def test_global_reasoning_chain(mock_llm, sample_input_text):
    """测试全局推理链"""
    
    # 模拟所有相关函数
    with patch("reasoning.global_reasoning.system_analyzer.run_prompt", side_effect=async_mock_system_analysis), \
         patch("reasoning.global_reasoning.constraints_generator.run_prompt", side_effect=async_mock_constraints_generation), \
         patch("knowledge.entity_storage.store_entity_summary", return_value=True):
        
        # 执行测试
        results = await run_global_reasoning(sample_input_text)
        
        # 验证结果
        assert results
        assert isinstance(results, dict)
        assert "system_analysis" in results
        assert "constraints" in results
        assert "architecture_charter" in results
        
        # 验证内容
        assert "移民申请" in results["system_analysis"]["system_type"]
        assert "命名规范" in results["constraints"]
        assert "架构风格" in results["architecture_charter"]

@pytest.mark.asyncio
async def test_local_reasoning_context_builder(mock_entity_storage, sample_global_constraints):
    """测试局部推理上下文构建器"""
    
    # 模拟依赖
    with patch("reasoning.local_reasoning.context_builder.build_context_for_round", 
              return_value="这是针对UserService的推理上下文，包含全局约束和历史决策信息"):
        
        # 执行测试
        context = await build_reasoning_context(
            entity_name="UserService",
            round_num=1,
            round_goal="上下文理解与基础架构识别",
            current_summary={"module": "用户认证与资料管理服务", "description": "管理用户身份验证和个人资料"},
            previous_qa=[],
            global_constraints=sample_global_constraints
        )
        
        # 验证结果
        assert context
        assert isinstance(context, str)
        assert "UserService" in context or "用户服务" in context
        assert "全局约束" in context

@pytest.mark.asyncio
async def test_local_reasoning_question_generator(mock_llm):
    """测试问题生成器功能"""
    
    # 模拟LLM客户端
    with patch("reasoning.local_reasoning.question_generators.run_prompt", side_effect=async_mock_question_generation):
        
        # 执行测试
        questions = await generate_questions(
            context="这是关于UserService的上下文信息",
            round_goal="上下文理解与基础架构识别",
            round_num=1
        )
        
        # 验证结果
        assert questions
        assert isinstance(questions, list)
        assert len(questions) >= 3
        
        # 验证问题内容
        assert any("职责" in q for q in questions)
        assert any("接口" in q for q in questions)
        assert any("依赖" in q for q in questions)

@pytest.mark.asyncio
async def test_local_reasoning_answer_generator(mock_llm):
    """测试回答生成器功能"""
    
    # 模拟LLM客户端
    with patch("reasoning.local_reasoning.answer_generators.run_prompt", side_effect=async_mock_answer_generation):
        
        # 执行测试
        answer = await generate_answer(
            entity_name="UserService",
            question="这个服务的主要职责是什么?",
            context="这是关于UserService的上下文信息，它负责用户认证与资料管理",
            round_goal="上下文理解与基础架构识别"
        )
        
        # 验证结果
        assert answer
        assert isinstance(answer, str)
        assert "用户" in answer
        assert "认证" in answer or "资料" in answer
        assert len(answer) > 50  # 确保答案有足够的长度

@pytest.mark.asyncio
async def test_local_reasoning_summary_updater(mock_llm):
    """测试摘要更新器功能"""
    
    # 模拟当前摘要
    current_summary = {
        "module": "用户认证与资料管理服务",
        "description": "管理用户身份验证和个人资料",
        "components": [],
        "interfaces": [],
        "dependencies": []
    }
    
    # 模拟问答历史
    qa_history = [
        {"question": "这个服务的主要职责是什么?", 
         "answer": "用户服务主要负责用户注册、登录、个人资料管理和认证授权等功能。"},
        {"question": "服务包含哪些主要组件?", 
         "answer": "包括AuthController处理HTTP请求，ProfileService实现业务逻辑，UserRepository进行数据访问。"},
        {"question": "有哪些外部接口?", 
         "answer": "提供REST API接口和Cognito/Auth0集成接口。"}
    ]
    
    # 模拟LLM客户端
    with patch("reasoning.local_reasoning.summary_updaters.run_prompt", side_effect=async_mock_summary_update):
        
        # 执行测试
        updated_summary = await update_entity_summary(
            entity_name="UserService",
            current_summary=current_summary,
            qa_history=qa_history,
            round_goal="上下文理解与基础架构识别",
            round_num=1
        )
        
        # 验证结果
        assert updated_summary
        assert isinstance(updated_summary, dict)
        assert "components" in updated_summary
        assert "interfaces" in updated_summary
        assert len(updated_summary["components"]) >= 2
        assert "AuthController" in str(updated_summary["components"])
        assert "REST API" in str(updated_summary["interfaces"])

@pytest.mark.asyncio
async def test_local_reasoning_chain(mock_llm, mock_entity_storage, sample_global_constraints):
    """测试局部推理链"""
    
    # 模拟初始实体摘要
    entity_name = "UserService"
    initial_summary = {
        "module": "用户认证与资料管理服务",
        "description": "管理用户身份验证和个人资料",
        "components": [],
        "interfaces": [],
        "dependencies": []
    }
    
    # 模拟所有相关函数
    with patch("reasoning.local_reasoning.context_builder.build_context_for_round", 
              return_value="这是针对UserService的推理上下文，包含全局约束和历史决策信息"), \
         patch("reasoning.local_reasoning.question_generators.run_prompt", 
              side_effect=async_mock_question_generation), \
         patch("reasoning.local_reasoning.answer_generators.run_prompt", 
              side_effect=async_mock_answer_generation), \
         patch("reasoning.local_reasoning.summary_updaters.run_prompt", 
              side_effect=async_mock_summary_update), \
         patch("knowledge.entity_storage.retrieve_entity", return_value=initial_summary), \
         patch("knowledge.entity_storage.store_entity_summary", return_value=True):
        
        # 执行测试
        result = await run_local_reasoning(
            entity_name=entity_name,
            global_constraints=sample_global_constraints,
            max_rounds=1
        )
        
        # 验证结果
        assert result
        assert isinstance(result, dict)
        assert "entity_name" in result
        assert "final_summary" in result
        assert result["entity_name"] == entity_name
        assert "components" in result["final_summary"]
        assert "interfaces" in result["final_summary"]
        assert len(result["final_summary"]["components"]) >= 2

# 模拟异步函数

async def async_mock_system_analysis(*args, **kwargs):
    """模拟系统分析结果"""
    return {
        "system_type": "加拿大移民申请SaaS平台",
        "description": "为申请人提供加拿大移民申请流程指导、评估和表格处理的智能平台",
        "architecture_style": "Serverless架构",
        "main_components": [
            "用户认证与资料管理服务",
            "评估与路径建议服务",
            "智能表格生成服务",
            "文档管理与分析服务",
            "顾问匹配与协作服务"
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

async def async_mock_constraints_generation(*args, **kwargs):
    """模拟约束生成结果"""
    return {
        "命名规范": {
            "类命名": "驼峰命名法",
            "方法命名": "小驼峰命名法",
            "常量命名": "全大写下划线分隔"
        },
        "API设计": {
            "REST规范": "遵循RESTful设计原则",
            "版本控制": "URL路径版本控制(如/api/v1/)",
            "响应格式": "统一使用JSON格式",
            "错误处理": "标准化错误响应"
        },
        "安全规范": {
            "认证": "JWT认证",
            "授权": "基于角色的访问控制(RBAC)",
            "数据保护": "所有敏感数据加密存储"
        },
        "云资源命名": {
            "Lambda/Function": "服务名-环境-功能 (例如: user-prod-login)",
            "存储桶": "服务名-环境-类型-区域 (例如: docs-dev-storage-us-east-1)",
            "数据库": "服务名-环境 (例如: thinkforward-prod)"
        }
    }

async def async_mock_question_generation(*args, **kwargs):
    """模拟问题生成结果"""
    context = args[0] if args else kwargs.get("context", "")
    
    if "UserService" in context or "用户服务" in context:
        return [
            "这个服务的主要职责是什么?",
            "服务如何处理用户认证流程?",
            "用户资料管理包括哪些具体功能?",
            "服务包含哪些主要组件?",
            "有哪些外部接口?",
            "与哪些其他服务有依赖关系?",
            "数据存储使用什么技术?",
            "服务是如何进行权限控制的?"
        ]
    elif "AssessmentService" in context or "评估服务" in context:
        return [
            "这个服务的主要评估流程是什么?",
            "如何计算移民路径的匹配分数?",
            "服务包含哪些主要组件?",
            "评估结果如何存储和管理?",
            "使用了哪些AI功能?",
            "与哪些其他服务有依赖关系?"
        ]
    else:
        return [
            "这个服务的主要职责是什么?",
            "服务包含哪些主要组件?",
            "有哪些外部接口?",
            "与哪些其他服务有依赖关系?",
            "数据模型是如何设计的?"
        ]

async def async_mock_answer_generation(*args, **kwargs):
    """模拟回答生成结果"""
    question = args[0] if args else kwargs.get("question", "")
    
    if "主要职责" in question:
        return "用户认证与资料管理服务主要负责用户注册、登录、个人资料管理和认证授权等功能。它处理所有与用户账户相关的操作，确保用户数据的安全性和完整性。同时，它还负责提供用户资料的完整性评估，为评估服务提供必要的用户信息。"
    elif "主要组件" in question:
        return "服务包含三个主要组件：(1) AuthController - 处理所有HTTP认证请求，包括登录、注册和令牌刷新；(2) ProfileService - 实现用户资料管理的业务逻辑，包括资料更新、验证和完整性检查；(3) UserRepository - 负责与数据库交互，执行用户数据的CRUD操作。"
    elif "外部接口" in question:
        return "服务提供以下外部接口：(1) REST API - 供前端和其他服务调用的HTTP接口；(2) Cognito/Auth0集成 - 与第三方认证服务的集成接口，支持社交登录和多因素认证。"
    elif "依赖关系" in question:
        return "该服务与以下服务有依赖关系：(1) 评估服务 - 为其提供用户资料数据，用于移民资格评估；(2) 通知服务 - 用于发送邮件通知，如欢迎邮件、密码重置等。"
    else:
        return "这是一个默认的回答，基于问题'{}'"

async def async_mock_summary_update(*args, **kwargs):
    """模拟摘要更新结果"""
    current_summary = args[0] if args else kwargs.get("current_summary", {})
    qa_history = args[1] if len(args) > 1 else kwargs.get("qa_history", [])
    
    # 基于当前摘要和问答历史，构建更新后的摘要
    updated_summary = current_summary.copy()
    
    if "用户" in str(current_summary.get("module", "")):
        updated_summary.update({
            "components": ["AuthController", "ProfileService", "UserRepository"],
            "interfaces": ["REST API", "Cognito/Auth0集成"],
            "dependencies": ["评估服务", "通知服务"],
            "data_storage": "MongoDB集合: users, profiles",
            "authentication": "JWT令牌 + Cognito/Auth0集成",
            "api_endpoints": [
                "/api/auth/login",
                "/api/auth/register",
                "/api/profile",
                "/api/profile/completeness"
            ]
        })
    elif "评估" in str(current_summary.get("module", "")):
        updated_summary.update({
            "components": ["AssessmentController", "EligibilityService", "PathwayRecommendationEngine"],
            "interfaces": ["REST API", "OpenAI集成"],
            "dependencies": ["用户服务", "表格服务"],
            "data_storage": "MongoDB集合: assessments, programs",
            "ai_features": "移民路径推荐、资格评分计算",
            "api_endpoints": [
                "/api/assessments",
                "/api/assessments/{id}",
                "/api/assessments/{id}/steps/{stepId}",
                "/api/assessments/{id}/result",
                "/api/pathways/compare"
            ]
        })
    else:
        updated_summary.update({
            "components": ["Controller", "Service", "Repository"],
            "interfaces": ["REST API"],
            "dependencies": [],
            "data_storage": "MongoDB",
            "api_endpoints": ["/api/base-endpoint"]
        })
    
    return updated_summary 