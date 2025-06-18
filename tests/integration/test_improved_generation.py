"""
改进后的生成质量集成测试。
端到端测试新的推理链、答案生成和质量控制系统。
"""

import pytest
import asyncio
import json
from typing import Dict, Any

from reasoning.local_reasoning.local_chain_improved import (
    run_full_improved_reasoning,
    ReasoningPhase,
    run_improved_reasoning_phase
)
from common.quality_validator import QualityValidator, QualityLevel
from knowledge.context_retrieval_improved import build_improved_context

# 测试用例
TEST_ENTITIES = [
    {
        "name": "UserManagementService",
        "initial_summary": {
            "module": "UserManagementService",
            "type": "service",
            "description": "用户管理核心服务模块"
        },
        "expected_outputs": {
            "services": ["UserService", "AuthService", "ProfileService"],
            "has_api_endpoints": True,
            "has_technical_stack": True,
            "min_quality_score": 75
        }
    },
    {
        "name": "OrderProcessingSystem",
        "initial_summary": {
            "module": "OrderProcessingSystem",
            "type": "system",
            "description": "订单处理系统"
        },
        "expected_outputs": {
            "services": ["OrderService", "PaymentService"],
            "has_state_machine": True,
            "has_integration_design": True,
            "min_quality_score": 70
        }
    },
    {
        "name": "NotificationAPI",
        "initial_summary": {
            "module": "NotificationAPI",
            "type": "api",
            "description": "通知服务API"
        },
        "expected_outputs": {
            "has_endpoints": True,
            "has_async_pattern": True,
            "min_quality_score": 70
        }
    }
]

class TestImprovedGeneration:
    """测试改进后的生成质量"""
    
    @pytest.mark.asyncio
    async def test_full_improved_reasoning_quality(self):
        """测试完整改进推理流程的输出质量"""
        for test_case in TEST_ENTITIES:
            print(f"\n测试实体: {test_case['name']}")
            
            # 运行改进的推理
            result = await run_full_improved_reasoning(
                entity_name=test_case['name'],
                initial_summary=test_case['initial_summary'],
                phases=[ReasoningPhase.FUNCTION_DEFINITION, ReasoningPhase.TECHNICAL_IMPLEMENTATION],
                min_quality_threshold=test_case['expected_outputs']['min_quality_score']
            )
            
            # 验证基本结构
            assert result is not None
            assert result.get('module') == test_case['name']
            assert '_metadata' in result
            assert result['_metadata']['overall_quality_score'] >= test_case['expected_outputs']['min_quality_score']
            
            # 验证具体内容
            if 'services' in test_case['expected_outputs']:
                assert 'implementation' in result
                assert 'services' in result['implementation']
                services = result['implementation']['services']
                assert len(services) > 0
                # 验证服务命名规范
                for service in services:
                    assert service.endswith('Service') or service.endswith('Handler')
            
            # 验证API设计
            if test_case['expected_outputs'].get('has_api_endpoints'):
                assert 'api_design' in result
                assert 'endpoints' in result['api_design']
                endpoints = result['api_design']['endpoints']
                assert len(endpoints) > 0
                # 验证端点格式
                for endpoint in endpoints:
                    if isinstance(endpoint, dict):
                        assert 'method' in endpoint
                        assert 'path' in endpoint
                        assert endpoint['path'].startswith('/')
            
            # 验证技术栈
            if test_case['expected_outputs'].get('has_technical_stack'):
                assert 'technical_decisions' in result
                tech = result['technical_decisions']
                assert tech.get('language') is not None
                assert tech.get('framework') is not None
                # 验证包含版本号
                assert any(char.isdigit() for char in str(tech.get('framework', '')))
            
            print(f"✅ {test_case['name']} 通过质量测试")
            print(f"   质量分数: {result['_metadata']['overall_quality_score']}")
    
    @pytest.mark.asyncio
    async def test_context_quality_by_phase(self):
        """测试不同阶段的上下文质量"""
        entity_name = "TestService"
        summary = {"module": entity_name, "type": "service"}
        
        phases = [
            ReasoningPhase.FUNCTION_DEFINITION,
            ReasoningPhase.TECHNICAL_IMPLEMENTATION,
            ReasoningPhase.INTEGRATION_DESIGN,
            ReasoningPhase.QUALITY_ASSURANCE
        ]
        
        for phase in phases:
            context = await build_improved_context(
                entity_name=entity_name,
                phase=phase.value,
                current_summary=summary
            )
            
            # 验证上下文结构
            assert len(context) > 0
            assert f"# 架构设计上下文 - {phase.value}" in context
            
            # 验证包含相关节
            if phase == ReasoningPhase.FUNCTION_DEFINITION:
                assert "实体信息" in context or "领域知识" in context
            elif phase == ReasoningPhase.TECHNICAL_IMPLEMENTATION:
                assert "设计模式" in context or "技术栈" in context
            elif phase == ReasoningPhase.INTEGRATION_DESIGN:
                assert "依赖" in context or "集成模式" in context
            elif phase == ReasoningPhase.QUALITY_ASSURANCE:
                assert "性能" in context or "安全" in context
            
            print(f"✅ {phase.value} 上下文验证通过")
    
    @pytest.mark.asyncio
    async def test_answer_specificity(self):
        """测试答案的具体性"""
        from reasoning.local_reasoning.answer_generators_improved import generate_specific_answer
        
        test_questions = [
            {
                "question": "UserService需要哪些核心方法？",
                "expected_patterns": ["create", "update", "delete", "(", ")"],
                "forbidden_terms": ["处理", "管理", "相关"]
            },
            {
                "question": "应该使用什么技术栈实现？",
                "expected_patterns": [r"\d+\.\d+", "框架名称"],  # 版本号
                "forbidden_terms": ["合适的", "一些", "某些"]
            }
        ]
        
        for test in test_questions:
            answer = await generate_specific_answer(
                entity_name="UserService",
                question=test['question'],
                context="用户服务的设计",
                round_goal="技术实现与模式选择"
            )
            
            # 验证包含期望的模式
            for pattern in test['expected_patterns']:
                if not pattern.startswith('\\'):  # 非正则表达式
                    assert pattern in answer, f"答案应包含 '{pattern}'"
            
            # 验证不包含禁用词
            for term in test['forbidden_terms']:
                assert term not in answer, f"答案不应包含空泛词汇 '{term}'"
            
            print(f"✅ 问题 '{test['question'][:30]}...' 答案具体性验证通过")
    
    @pytest.mark.asyncio
    async def test_json_summary_structure(self):
        """测试JSON摘要的结构完整性"""
        from reasoning.local_reasoning.answer_generators_improved import generate_structured_json_summary
        
        qa_pairs = [
            {
                "question": "核心功能有哪些？",
                "answer": "1. 用户注册 - createUser(data: CreateUserDTO): User\n2. 用户登录 - authenticate(credentials: LoginDTO): AuthToken"
            },
            {
                "question": "使用什么技术栈？",
                "answer": "使用Node.js 18.0 + Express 4.18.2 + TypeScript 5.0，数据库使用PostgreSQL 14.5"
            }
        ]
        
        summary = await generate_structured_json_summary(
            entity_name="UserService",
            qa_pairs=qa_pairs,
            entity_type="service"
        )
        
        # 验证JSON结构
        assert isinstance(summary, dict)
        assert summary.get('module') == "UserService"
        assert summary.get('type') == "service"
        
        # 验证技术决策
        tech = summary.get('technical_decisions', {})
        assert tech.get('language') is not None
        assert tech.get('framework') is not None
        
        # 验证实现细节
        impl = summary.get('implementation', {})
        if impl.get('services'):
            for service in impl['services']:
                assert isinstance(service, str)
                assert len(service) > 0
        
        print("✅ JSON摘要结构验证通过")
    
    @pytest.mark.asyncio
    async def test_quality_validator_accuracy(self):
        """测试质量验证器的准确性"""
        test_texts = [
            {
                "text": "这个模块处理用户相关功能，管理一些用户数据。",
                "expected_level": QualityLevel.POOR,
                "context": "general"
            },
            {
                "text": """
                UserService 实现:
                - createUser(dto: CreateUserDTO): Promise<User>
                - updateProfile(userId: string, data: ProfileDTO): Promise<User>
                - deleteUser(userId: string): Promise<void>
                
                使用 PostgreSQL 14.5 存储用户数据
                使用 Redis 7.0 缓存会话信息
                """,
                "expected_level": QualityLevel.EXCELLENT,
                "context": "implementation"
            },
            {
                "text": """
                API端点设计:
                - POST /api/v1/users - 创建用户
                - GET /api/v1/users/{id} - 获取用户信息
                - PUT /api/v1/users/{id} - 更新用户
                
                错误码:
                - 400 BAD_REQUEST
                - 404 NOT_FOUND
                - 500 INTERNAL_SERVER_ERROR
                """,
                "expected_level": QualityLevel.GOOD,
                "context": "api"
            }
        ]
        
        for test in test_texts:
            report = QualityValidator.validate_text(test['text'], test['context'])
            
            # 验证质量等级
            assert report.level == test['expected_level'], \
                f"期望 {test['expected_level']}, 实际 {report.level}"
            
            # 验证有合理的建议
            if report.level != QualityLevel.EXCELLENT:
                assert len(report.suggestions) > 0
            
            print(f"✅ 质量等级 {test['expected_level']} 验证通过")
    
    @pytest.mark.asyncio
    async def test_phase_specific_improvements(self):
        """测试阶段特定的改进效果"""
        entity_name = "PaymentService"
        initial_summary = {
            "module": entity_name,
            "type": "service",
            "description": "支付服务模块"
        }
        
        # 测试每个阶段
        for phase in list(ReasoningPhase)[:2]:  # 只测试前两个阶段以节省时间
            result, qa_history, avg_quality = await run_improved_reasoning_phase(
                entity_name=entity_name,
                phase=phase,
                current_summary=initial_summary,
                previous_phases_output={}
            )
            
            # 验证质量分数
            assert avg_quality >= 70, f"{phase.value} 阶段质量分数过低: {avg_quality}"
            
            # 验证QA历史
            assert len(qa_history) > 0
            for qa in qa_history:
                assert 'quality_score' in qa
                assert qa['quality_score'] >= 60  # 每个答案的最低质量
            
            # 验证阶段特定的输出
            if phase == ReasoningPhase.FUNCTION_DEFINITION:
                # 应该有功能定义
                assert 'core_functionality' in result or 'api_design' in result
            elif phase == ReasoningPhase.TECHNICAL_IMPLEMENTATION:
                # 应该有技术决策
                assert 'technical_decisions' in result
                assert result['technical_decisions'].get('framework') is not None
            
            print(f"✅ {phase.value} 阶段改进验证通过 (平均质量: {avg_quality:.1f})")

# 性能基准测试
class TestPerformanceBenchmark:
    """性能基准测试"""
    
    @pytest.mark.asyncio
    async def test_generation_performance(self):
        """测试生成性能"""
        import time
        
        entity_name = "PerformanceTestService"
        summary = {"module": entity_name, "type": "service"}
        
        # 测试单个阶段的性能
        start_time = time.time()
        
        result, _, _ = await run_improved_reasoning_phase(
            entity_name=entity_name,
            phase=ReasoningPhase.FUNCTION_DEFINITION,
            current_summary=summary,
            previous_phases_output={}
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # 验证性能（应该在合理时间内完成）
        assert elapsed < 60, f"生成时间过长: {elapsed}秒"
        print(f"✅ 单阶段生成性能测试通过 (耗时: {elapsed:.2f}秒)")
    
    def test_quality_validation_performance(self):
        """测试质量验证性能"""
        import time
        
        # 准备大量文本
        large_text = """
        UserService 实现细节:
        """ + "\n".join([f"- method{i}(param{i}: Type{i}): Result{i}" for i in range(100)])
        
        # 测试验证性能
        start_time = time.time()
        
        for _ in range(10):  # 运行10次
            report = QualityValidator.validate_text(large_text, "implementation")
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        # 验证性能
        assert avg_time < 0.1, f"验证时间过长: {avg_time}秒"
        print(f"✅ 质量验证性能测试通过 (平均耗时: {avg_time*1000:.2f}ms)")

# 回归测试
class TestRegression:
    """确保改进不会破坏现有功能"""
    
    @pytest.mark.asyncio
    async def test_backward_compatibility(self):
        """测试向后兼容性"""
        from reasoning.local_reasoning.local_chain_improved import run_local_reasoning_with_quality
        
        # 测试兼容接口
        entity_name = "BackwardCompatTest"
        summary = {"module": entity_name, "type": "service"}
        
        result, qa_history = await run_local_reasoning_with_quality(
            entity_name=entity_name,
            entity_summary=summary,
            round_goal="上下文理解与基础架构识别"
        )
        
        # 验证返回格式
        assert isinstance(result, dict)
        assert isinstance(qa_history, list)
        for qa in qa_history:
            assert 'question' in qa
            assert 'answer' in qa
        
        print("✅ 向后兼容性测试通过")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])