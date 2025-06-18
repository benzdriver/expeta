"""
Clarifier系统集成测试
"""

import pytest
import asyncio
import json
from typing import Dict, Any

from clarifier.core import (
    ClarifierOrchestrator, 
    BlindSpotDetector,
    VersionManager,
    ImpactAnalyzer,
    SmartRefactoring
)
from clarifier.core.clarifier_orchestrator import (
    ClarifierMode,
    ClarificationRequest
)

class TestClarifierIntegration:
    """Clarifier系统集成测试"""
    
    @pytest.fixture
    def orchestrator(self):
        """创建编排器实例"""
        return ClarifierOrchestrator()
    
    @pytest.fixture
    def sample_prd(self):
        """示例PRD内容"""
        return """
        ## 电商平台订单系统
        
        ### 功能需求
        1. 订单管理
           - 创建订单
           - 查询订单
           - 取消订单
        
        2. 支付功能
           - 支持支付宝和微信支付
           - 支付状态查询
        
        3. 物流跟踪
           - 实时查询物流信息
           - 物流异常处理
        """
    
    @pytest.mark.asyncio
    async def test_interactive_clarification_flow(self, orchestrator, sample_prd):
        """测试交互式澄清流程"""
        # 启动会话
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=sample_prd,
            mode=ClarifierMode.INTERACTIVE,
            context={"project_type": "e-commerce"}
        )
        
        assert session_id is not None
        assert result['total_blind_spots'] > 0
        assert result['next_action']['type'] == 'clarification_needed'
        
        # 获取第一个盲点
        blind_spot = result['next_action']['blind_spot']
        assert blind_spot['id'] is not None
        assert len(blind_spot['questions']) > 0
        
        # 模拟用户澄清
        clarification = ClarificationRequest(
            blind_spot_id=blind_spot['id'],
            user_response="支付失败时自动重试3次，每次间隔1分钟"
        )
        
        clarification_result = await orchestrator.process_clarification(
            session_id, clarification
        )
        
        assert clarification_result['status'] == 'processed'
        assert clarification_result['new_version'] is not None
        
        # 验证会话状态更新
        session_status = orchestrator.get_session_status(session_id)
        assert session_status['progress']['addressed'] == 1
    
    @pytest.mark.asyncio
    async def test_prd_auto_enhancement(self, orchestrator, sample_prd):
        """测试PRD自动增强"""
        session_id, result = await orchestrator.start_clarification_session(
            prd_content=sample_prd,
            mode=ClarifierMode.PRD_ANALYSIS
        )
        
        assert result['next_action']['type'] == 'auto_enhanced'
        assert result['next_action']['blind_spots_addressed'] > 0
        assert 'enhanced_version' in result['next_action']
    
    @pytest.mark.asyncio
    async def test_requirement_change_handling(self, orchestrator):
        """测试需求变更处理"""
        # 初始化项目
        initial_prd = "## 项目：用户管理系统\n功能：用户注册、登录"
        initial_summary = {
            "project_name": "用户管理系统",
            "features": ["用户注册", "用户登录"]
        }
        
        version_id = orchestrator.version_manager.initialize_with_prd(
            initial_prd, initial_summary
        )
        
        # 创建变更请求
        change_request = {
            "type": "feature_addition",
            "description": "添加密码重置功能",
            "details": {
                "feature": "密码重置",
                "method": "邮件验证"
            }
        }
        
        # 分析变更影响
        impact_result = await orchestrator.handle_requirement_change(
            change_request, auto_execute=False
        )
        
        assert impact_result['status'] == 'pending_confirmation'
        assert 'impact_analysis' in impact_result
        assert 'refactoring_plan' in impact_result
        
        # 执行重构
        refactoring_result = await orchestrator.execute_refactoring(
            impact_result['refactoring_plan']
        )
        
        assert refactoring_result['success'] == True
        assert refactoring_result['version_id'] is not None
    
    @pytest.mark.asyncio
    async def test_version_management(self, orchestrator, sample_prd):
        """测试版本管理功能"""
        # 创建初始版本
        v1 = orchestrator.version_manager.initialize_with_prd(
            sample_prd, {"project": "test"}
        )
        
        # 创建几个变更版本
        v2 = orchestrator.version_manager.save_blind_spot_clarification(
            sample_prd + "\n## 新增：库存管理",
            {"project": "test", "features": ["库存管理"]},
            "BS_001",
            "添加库存管理功能"
        )
        
        # 获取版本历史
        history = orchestrator.get_version_history(limit=5)
        assert len(history) >= 2
        assert history[0]['id'] == v2  # 最新版本在前
        
        # 测试版本对比
        diff = orchestrator.version_manager.requirement_version.get_version_diff(
            v1, v2
        )
        assert 'changes' in diff
        assert len(diff['changes']['added']) > 0
    
    @pytest.mark.asyncio
    async def test_blind_spot_detection_quality(self, orchestrator):
        """测试盲点检测质量"""
        detector = BlindSpotDetector()
        
        # 测试不同类型的PRD
        test_cases = [
            {
                "prd": "实现用户上传文件功能",
                "expected_types": ["edge_case", "security"]
            },
            {
                "prd": "支持在线支付功能，集成支付宝",
                "expected_types": ["error_handling", "security"]
            },
            {
                "prd": "开发移动端APP，支持iOS和Android",
                "expected_types": ["user_experience"]
            }
        ]
        
        for case in test_cases:
            blind_spots = await detector.detect_blind_spots(case["prd"])
            detected_types = [bs.type.value for bs in blind_spots]
            
            # 验证是否检测到预期的盲点类型
            for expected_type in case["expected_types"]:
                assert any(expected_type in t for t in detected_types), \
                    f"未检测到预期的盲点类型: {expected_type}"
    
    @pytest.mark.asyncio
    async def test_structured_summary_generation(self, orchestrator):
        """测试结构化摘要生成"""
        detailed_prd = """
        ## 在线教育平台
        
        ### 功能需求
        1. 课程管理
           - 教师创建课程，包括视频、文档、作业
           - 课程分类和搜索
           - 课程评价系统
        
        2. 学习管理
           - 学习进度跟踪
           - 作业提交和批改
           - 在线考试系统
        
        3. 互动功能
           - 讨论区
           - 实时问答
           - 学习小组
        
        ### 技术要求
        - 支持10万并发用户
        - 视频流畅播放
        - 数据安全保护
        """
        
        # 初始化
        version_id = orchestrator.version_manager.initialize_with_prd(
            detailed_prd, {"project": "在线教育平台"}
        )
        
        # 生成结构化摘要
        summary_result = await orchestrator.generate_structured_summary(
            detailed_prd
        )
        
        assert summary_result['quality_score'] >= 70
        assert 'summary' in summary_result
        
        summary = summary_result['summary']
        assert 'technical_architecture' in summary
        assert 'functional_modules' in summary
        assert 'non_functional_requirements' in summary
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, orchestrator):
        """测试并发会话处理"""
        # 创建多个会话
        sessions = []
        for i in range(3):
            session_id, _ = await orchestrator.start_clarification_session(
                prd_content=f"项目{i}: 测试系统",
                mode=ClarifierMode.QUICK_CHECK
            )
            sessions.append(session_id)
        
        # 验证所有会话都被正确创建
        assert len(sessions) == 3
        assert len(set(sessions)) == 3  # 所有ID都是唯一的
        
        # 验证每个会话的状态
        for session_id in sessions:
            status = orchestrator.get_session_status(session_id)
            assert status['session_id'] == session_id
            assert 'progress' in status
    
    @pytest.mark.asyncio
    async def test_error_handling(self, orchestrator):
        """测试错误处理"""
        # 测试无效会话ID
        with pytest.raises(ValueError):
            await orchestrator.process_clarification(
                "invalid_session_id",
                ClarificationRequest("BS_001", "test")
            )
        
        # 测试无效的导出格式
        session_id, _ = await orchestrator.start_clarification_session(
            "测试PRD", mode=ClarifierMode.QUICK_CHECK
        )
        
        with pytest.raises(ValueError):
            orchestrator.export_session_report(session_id, format="invalid")
    
    def test_export_functionality(self, orchestrator):
        """测试导出功能"""
        # 创建一些版本历史
        orchestrator.version_manager.initialize_with_prd(
            "初始PRD", {"version": 1}
        )
        orchestrator.version_manager.save_blind_spot_clarification(
            "更新的PRD", {"version": 2}, "BS_001", "测试澄清"
        )
        
        # 测试版本历史导出
        json_export = orchestrator.version_manager.requirement_version.export_version_history("json")
        assert json.loads(json_export)  # 验证是有效的JSON
        
        md_export = orchestrator.version_manager.requirement_version.export_version_history("markdown")
        assert "# 版本历史" in md_export

# 运行测试的辅助函数
async def run_integration_tests():
    """运行所有集成测试"""
    test_instance = TestClarifierIntegration()
    orchestrator = ClarifierOrchestrator()
    
    print("运行集成测试...")
    
    try:
        # 测试交互式流程
        print("1. 测试交互式澄清流程")
        await test_instance.test_interactive_clarification_flow(
            orchestrator, 
            test_instance.sample_prd()
        )
        print("✓ 通过")
        
        # 测试自动增强
        print("2. 测试PRD自动增强")
        await test_instance.test_prd_auto_enhancement(
            orchestrator,
            test_instance.sample_prd()
        )
        print("✓ 通过")
        
        # 测试需求变更
        print("3. 测试需求变更处理")
        await test_instance.test_requirement_change_handling(orchestrator)
        print("✓ 通过")
        
        # 测试结构化摘要生成
        print("4. 测试结构化摘要生成")
        await test_instance.test_structured_summary_generation(orchestrator)
        print("✓ 通过")
        
        print("\n所有集成测试通过！")
        
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_integration_tests())