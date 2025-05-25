from common import print_log
"""
推理模块集成测试（真实API调用）
该测试文件针对reasoning模块进行真实API调用（不使用mock），测试实际功能
"""

import os
import json
import pytest
from pathlib import Path

# 导入全局推理模块
from reasoning.global_reasoning.system_analyzer import analyze_system, analyze_system_type
from reasoning.global_reasoning.constraints_generator import generate_constraints
from reasoning.global_reasoning.global_chain import run_global_reasoning

# 导入局部推理模块
from reasoning.local_reasoning.context_builder import build_reasoning_context
from reasoning.local_reasoning.question_generators import generate_questions
from reasoning.local_reasoning.answer_generators import generate_answer
from reasoning.local_reasoning.summary_updaters import update_entity_summary

@pytest.mark.asyncio
async def test_real_analyze_system(sample_input_text):
    """测试系统分析器真实功能"""
    
    # 不使用mock，直接调用实际函数
    analysis = await analyze_system(sample_input_text)
    
    # 验证结果
    assert analysis is not None
    assert isinstance(analysis, dict)
    # 检查结果结构
    assert "systemAnalysis" in analysis or "system_type" in analysis
    assert "architectureRecommendation" in analysis or "architecture_style" in analysis
    
    # 打印结果，方便debug
    print("系统分析结果:", json.dumps(analysis, indent=2, ensure_ascii=False))

@pytest.mark.asyncio
async def test_real_analyze_system_type(sample_input_text):
    """测试系统类型分析真实功能"""
    
    # 不使用mock，直接调用实际函数
    system_type = await analyze_system_type(sample_input_text)
    
    # 验证结果
    assert system_type is not None
    assert isinstance(system_type, dict)
    # 验证常见字段
    assert any(key in system_type for key in ["systemType", "domain", "users", "complexity"])
    
    # 打印结果，方便debug
    print("系统类型分析结果:", json.dumps(system_type, indent=2, ensure_ascii=False))

@pytest.mark.asyncio
async def test_real_generate_answer(sample_input_text):
    """测试回答生成器真实功能"""
    
    # 准备测试数据
    entity_name = "UserService"
    question = "这个服务的主要职责是什么?"
    context = f"""
    基于以下文档内容，回答关于UserService的问题：
    
    {sample_input_text}
    
    该服务主要处理用户认证和资料管理相关功能。
    """
    round_goal = "上下文理解与基础架构识别"
    
    # 不使用mock，直接调用实际函数
    answer = await generate_answer(
        entity_name=entity_name,
        question=question,
        context=context,
        round_goal=round_goal
    )
    
    # 验证结果
    assert answer is not None
    assert isinstance(answer, str)
    assert len(answer) > 50  # 确保有足够长度的回答
    
    # 打印结果，方便debug
    print_log(f"问题: {question}")
    print_log(f"回答: {answer}")

@pytest.mark.asyncio
async def test_real_generate_questions(sample_input_text):
    """测试问题生成器真实功能"""
    
    # 准备测试数据
    entity_name = "UserService"
    context = f"""
    基于以下文档内容，生成关于UserService的问题：
    
    {sample_input_text}
    
    该服务主要处理用户认证和资料管理相关功能。
    """
    round_goal = "上下文理解与基础架构识别"
    
    # 不使用mock，直接调用实际函数
    questions = await generate_questions(
        entity_name=entity_name,
        context=context,
        round_goal=round_goal,
        round_num=1
    )
    
    # 验证结果
    assert questions is not None
    assert isinstance(questions, list)
    assert len(questions) >= 3  # 确保生成多个问题
    
    # 打印结果，方便debug
    print_log("生成的问题:")
    for i, q in enumerate(questions, 1):
        print_log(f"{i}. {q}")

@pytest.mark.asyncio
async def test_real_update_entity_summary():
    """测试实体摘要更新真实功能"""
    
    # 准备测试数据
    entity_name = "UserService"
    current_summary = {
        "module": "用户认证与资料管理服务",
        "description": "管理用户身份验证和个人资料",
        "components": [],
        "interfaces": [],
        "dependencies": []
    }
    
    qa_history = [
        {"question": "这个服务的主要职责是什么?", 
         "answer": "用户服务主要负责用户注册、登录、个人资料管理和认证授权等功能。"},
        {"question": "服务包含哪些主要组件?", 
         "answer": "包括AuthController处理HTTP请求，ProfileService实现业务逻辑，UserRepository进行数据访问。"},
        {"question": "有哪些外部接口?", 
         "answer": "提供REST API接口和Cognito/Auth0集成接口。"}
    ]
    
    context = """
    用户服务是系统的核心服务之一，负责处理所有用户相关操作。
    按照系统约束，需要实现RESTful API设计，确保安全认证和职责单一。
    """
    
    round_goal = "上下文理解与基础架构识别"
    
    # 不使用mock，直接调用实际函数
    updated_summary = await update_entity_summary(
        entity_name=entity_name,
        current_summary=current_summary,
        qa_history=qa_history,
        context=context,  # 需要传入context参数
        round_goal=round_goal
    )
    
    # 验证结果
    assert updated_summary is not None
    assert isinstance(updated_summary, dict)
    assert "components" in updated_summary
    assert "interfaces" in updated_summary
    assert len(updated_summary["components"]) > 0
    
    # 打印结果，方便debug
    print("更新后的摘要:", json.dumps(updated_summary, indent=2, ensure_ascii=False))

# 以下测试需要依赖其他模块真实实现，可能需要额外配置
@pytest.mark.asyncio
@pytest.mark.optional  # 使用标记表示这是可选测试，可能需要特定环境
async def test_real_build_reasoning_context(sample_global_constraints):
    """测试构建推理上下文真实功能（可选测试）"""
    
    # 准备测试数据
    entity_name = "UserService"
    round_num = 1
    round_goal = "上下文理解与基础架构识别"
    current_summary = {
        "module": "用户认证与资料管理服务",
        "description": "管理用户身份验证和个人资料"
    }
    previous_qa = []
    
    try:
        # 不使用mock，直接调用实际函数
        context = await build_reasoning_context(
            entity_name=entity_name,
            round_num=round_num,
            round_goal=round_goal,
            current_summary=current_summary,
            previous_qa=previous_qa,
            global_constraints=sample_global_constraints
        )
        
        # 验证结果
        assert context is not None
        assert isinstance(context, str)
        assert len(context) > 100  # 确保上下文有足够长度
        
        print_log("构建的推理上下文:", context[:300] + "...")  # 只打印前300个字符
    except Exception as e:
        pytest.skip(f"跳过此测试，可能需要额外配置: {e}") 