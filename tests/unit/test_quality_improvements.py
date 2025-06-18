"""
质量改进功能的单元测试。
测试新的答案生成器和质量验证器。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json

from reasoning.local_reasoning.answer_generators_improved import (
    generate_specific_answer,
    validate_answer_quality,
    generate_structured_json_summary,
    clean_vague_content
)
from common.quality_validator import (
    QualityValidator,
    QualityLevel,
    validate_quality,
    is_high_quality
)

class TestAnswerQualityValidation:
    """测试答案质量验证功能"""
    
    def test_validate_vague_answer(self):
        """测试识别空泛答案"""
        vague_answer = """
        这个模块主要处理用户相关功能，包括一些用户管理的操作。
        可以考虑使用合适的数据库来存储相关数据。
        建议使用一些常见的框架来实现这些功能。
        """
        
        score, issues = validate_answer_quality(vague_answer)
        
        assert score < 70  # 质量分数应该较低
        assert len(issues) > 0
        assert any("空泛词汇" in issue for issue in issues)
    
    def test_validate_specific_answer(self):
        """测试识别具体答案"""
        specific_answer = """
        ### 核心类设计
        
        1. **UserService** - 用户业务逻辑服务
           - createUser(dto: CreateUserDTO): User
           - updateProfile(userId: string, data: UpdateProfileDTO): User
           - authenticate(credentials: LoginDTO): AuthToken
        
        2. **UserRepository** - 用户数据访问层
           - save(user: User): User
           - findById(id: string): User | null
           - findByEmail(email: string): User | null
        
        ### API设计
        - POST /api/v1/users - 创建用户
        - PUT /api/v1/users/{id}/profile - 更新用户资料
        - POST /api/v1/auth/login - 用户登录
        
        ### 技术栈
        - Node.js 18.17.0
        - Express 4.18.2
        - PostgreSQL 14.5
        - Redis 7.0.5 (用于会话缓存)
        """
        
        score, issues = validate_answer_quality(specific_answer)
        
        assert score >= 85  # 质量分数应该较高
        assert len(issues) == 0 or all("空泛词汇" not in issue for issue in issues)
    
    def test_quality_score_calculation(self):
        """测试质量分数计算的准确性"""
        test_cases = [
            # (答案内容, 预期分数范围)
            ("处理一些相关功能", (0, 50)),
            ("UserService包含createUser()方法", (70, 100)),
            ("使用Spring Boot 2.7.0实现RESTful API", (80, 100)),
        ]
        
        for answer, (min_score, max_score) in test_cases:
            score, _ = validate_answer_quality(answer)
            assert min_score <= score <= max_score

class TestQualityValidator:
    """测试质量验证器"""
    
    def test_validate_text_with_vague_terms(self):
        """测试识别空泛词汇"""
        text = "这个功能处理用户管理相关的一些操作"
        report = QualityValidator.validate_text(text)
        
        assert report.level in [QualityLevel.POOR, QualityLevel.FAIR]
        assert report.metrics['vague_terms_count'] > 0
        assert len(report.issues) > 0
    
    def test_validate_api_context(self):
        """测试API上下文的验证"""
        api_text = """
        用户API设计：
        - POST /api/v1/users - 创建用户
        - GET /api/v1/users/{id} - 获取用户信息
        - 404 NOT_FOUND - 用户不存在
        - 400 BAD_REQUEST - 请求参数错误
        """
        
        report = QualityValidator.validate_text(api_text, "api")
        
        assert report.score >= 70
        assert report.metrics['api_endpoints_count'] >= 2
        assert report.metrics['error_codes_count'] >= 2
    
    def test_validate_implementation_context(self):
        """测试实现上下文的验证"""
        impl_text = """
        实现方案：
        
        UserService类实现：
        - createUser(data: CreateUserDTO): User
        - validateEmail(email: string): boolean
        
        UserRepository接口：
        - save(user: User): Promise<User>
        - findByEmail(email: string): Promise<User | null>
        """
        
        report = QualityValidator.validate_text(impl_text, "implementation")
        
        assert report.score >= 75
        assert report.metrics['class_names_count'] >= 2
        assert report.metrics['method_signatures_count'] >= 4
    
    def test_validate_json_summary(self):
        """测试JSON摘要验证"""
        good_summary = {
            "module": "UserManagement",
            "description": "用户管理模块，提供用户注册、认证和资料管理功能",
            "technical_decisions": {
                "language": "TypeScript 5.0",
                "framework": "NestJS 10.0",
                "database": "PostgreSQL 14.5"
            },
            "implementation": {
                "services": ["UserService", "AuthService", "ProfileService"],
                "repositories": ["UserRepository"],
                "controllers": ["UserController", "AuthController"]
            },
            "api_design": {
                "endpoints": [
                    {"method": "POST", "path": "/api/v1/users", "description": "创建用户"},
                    {"method": "GET", "path": "/api/v1/users/{id}", "description": "获取用户"}
                ]
            }
        }
        
        report = QualityValidator.validate_json_summary(good_summary)
        
        assert report.score >= 85
        assert report.level in [QualityLevel.GOOD, QualityLevel.EXCELLENT]
        assert report.metrics['services_count'] == 3
        assert report.metrics['api_endpoints_count'] == 2
    
    def test_validate_poor_json_summary(self):
        """测试低质量JSON摘要验证"""
        poor_summary = {
            "module": "User",
            "description": "处理用户相关功能",
            "technical_decisions": {},
            "implementation": {
                "services": [],
                "repositories": []
            }
        }
        
        report = QualityValidator.validate_json_summary(poor_summary)
        
        assert report.score < 70
        assert report.level in [QualityLevel.POOR, QualityLevel.FAIR]
        assert "未指定编程语言" in report.issues
        assert "缺少服务类定义" in report.issues

class TestAsyncAnswerGeneration:
    """测试异步答案生成"""
    
    @pytest.mark.asyncio
    async def test_generate_specific_answer(self):
        """测试生成具体答案"""
        # Mock LLM response
        mock_response = """
        ### 1. 核心功能清单
        
        1. **创建用户账户**
           - 输入参数：CreateUserDTO (email: string, password: string, name: string)
           - 输出结果：User (id: UUID, email: string, name: string, createdAt: Date)
           - 业务规则：邮箱必须唯一，密码至少8位
        
        2. **用户身份认证**
           - 输入参数：LoginDTO (email: string, password: string)
           - 输出结果：AuthToken (token: string, expiresIn: number)
           - 业务规则：连续5次失败锁定账户30分钟
        
        ### 2. API接口定义
        
        POST /api/v1/users
        请求体：
        {
          "email": "user@example.com",
          "password": "securePass123",
          "name": "John Doe"
        }
        
        响应体（201）：
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "email": "user@example.com",
          "name": "John Doe",
          "createdAt": "2024-01-01T00:00:00Z"
        }
        """
        
        with patch('llm_services.executor.run_prompt', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            
            answer = await generate_specific_answer(
                entity_name="UserManagement",
                question="定义用户管理模块的核心功能和API",
                context="用户管理是系统的核心模块",
                round_goal="功能定义与边界划分"
            )
            
            assert "CreateUserDTO" in answer
            assert "/api/v1/users" in answer
            assert "UUID" in answer
            
            # 验证调用参数
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args
            assert "具体" in call_args.kwargs['system_message']
            assert "禁用词汇" in call_args.kwargs['system_message']
    
    @pytest.mark.asyncio
    async def test_quality_improvement_retry(self):
        """测试质量不合格时的重试机制"""
        # 第一次返回低质量答案
        vague_response = "处理用户相关的一些功能和管理操作"
        
        # 第二次返回改进的答案
        improved_response = """
        UserService 实现：
        - createUser(data: CreateUserDTO): Promise<User>
        - updateUser(id: string, data: UpdateUserDTO): Promise<User>
        - deleteUser(id: string): Promise<void>
        
        使用 PostgreSQL 14.5 存储用户数据
        """
        
        with patch('llm_services.executor.run_prompt', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = [vague_response, improved_response]
            
            answer = await generate_specific_answer(
                entity_name="UserModule",
                question="设计用户模块的实现方案",
                context="",
                round_goal="技术实现与模式选择"
            )
            
            # 应该调用了两次（初始 + 重试）
            assert mock_llm.call_count == 2
            assert "UserService" in answer
            assert "PostgreSQL 14.5" in answer

class TestVagueContentCleaning:
    """测试空泛内容清理"""
    
    def test_clean_vague_content(self):
        """测试清理JSON中的空泛内容"""
        vague_summary = {
            "module": "用户管理模块",
            "description": "处理用户相关功能",
            "services": ["处理用户的服务", "管理认证的服务"],
            "features": ["一些用户功能", "某些管理操作", ""]
        }
        
        cleaned = clean_vague_content(vague_summary)
        
        assert cleaned["module"] == "用户管理模块"  # 保持不变
        assert "处理" not in str(cleaned.get("description", ""))
        assert all("处理" not in s and "管理" not in s for s in cleaned.get("services", []))
        assert "" not in cleaned.get("features", [])  # 空字符串被移除

class TestStructuredJSONGeneration:
    """测试结构化JSON生成"""
    
    @pytest.mark.asyncio
    async def test_generate_structured_json(self):
        """测试生成结构化JSON摘要"""
        qa_pairs = [
            {
                "question": "用户模块需要哪些核心服务？",
                "answer": "需要UserService处理用户逻辑，AuthService处理认证，使用PostgreSQL 14.5存储数据"
            },
            {
                "question": "API如何设计？",
                "answer": "POST /api/v1/users 创建用户，GET /api/v1/users/{id} 获取用户信息"
            }
        ]
        
        mock_json_response = json.dumps({
            "module": "UserManagement",
            "type": "service",
            "description": "用户管理服务模块",
            "technical_decisions": {
                "language": "TypeScript",
                "framework": "NestJS",
                "database": "PostgreSQL 14.5"
            },
            "implementation": {
                "services": ["UserService", "AuthService"],
                "repositories": ["UserRepository"],
                "controllers": ["UserController"]
            },
            "api_design": {
                "endpoints": [
                    {"method": "POST", "path": "/api/v1/users", "description": "创建用户"},
                    {"method": "GET", "path": "/api/v1/users/{id}", "description": "获取用户信息"}
                ]
            }
        })
        
        with patch('llm_services.executor.run_prompt', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = f"```json\n{mock_json_response}\n```"
            
            summary = await generate_structured_json_summary(
                entity_name="UserManagement",
                qa_pairs=qa_pairs,
                entity_type="service"
            )
            
            assert summary["module"] == "UserManagement"
            assert len(summary["implementation"]["services"]) == 2
            assert summary["technical_decisions"]["database"] == "PostgreSQL 14.5"
            assert len(summary["api_design"]["endpoints"]) == 2

class TestIntegrationScenarios:
    """集成测试场景"""
    
    def test_end_to_end_quality_validation(self):
        """端到端质量验证测试"""
        # 1. 生成低质量内容
        poor_content = "这个模块处理一些用户管理相关的功能"
        
        # 2. 验证质量
        report = QualityValidator.validate_text(poor_content)
        assert report.score < 70
        
        # 3. 获取改进建议
        suggestions = QualityValidator.suggest_improvements(poor_content)
        assert len(suggestions) > 0
        
        # 4. 应用改进（模拟）
        improved_content = """
        UserManagementService 实现：
        - createUser(data: CreateUserDTO): Promise<User>
        - updateUserProfile(userId: UUID, data: ProfileDTO): Promise<User>
        - deleteUser(userId: UUID): Promise<void>
        
        技术栈：
        - TypeScript 5.0
        - NestJS 10.0
        - PostgreSQL 14.5
        
        API端点：
        - POST /api/v1/users - 创建新用户
        - PUT /api/v1/users/{id}/profile - 更新用户资料
        - DELETE /api/v1/users/{id} - 删除用户
        """
        
        # 5. 重新验证
        improved_report = QualityValidator.validate_text(improved_content, "implementation")
        assert improved_report.score >= 85
        assert improved_report.level in [QualityLevel.GOOD, QualityLevel.EXCELLENT]

# 性能测试
class TestPerformance:
    """性能相关测试"""
    
    def test_validation_performance(self):
        """测试验证性能"""
        import time
        
        # 准备大文本
        large_text = """
        UserService 实现细节：
        """ + "\n".join([f"- method{i}(param{i}: Type{i}): Result{i}" for i in range(100)])
        
        start_time = time.time()
        report = QualityValidator.validate_text(large_text)
        end_time = time.time()
        
        # 验证应该在合理时间内完成（< 100ms）
        assert (end_time - start_time) < 0.1
        assert report.score > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])