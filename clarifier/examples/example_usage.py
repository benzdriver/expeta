"""
Clarifier系统使用示例
"""

import asyncio
from typing import Dict, Any
import json

from clarifier.core import ClarifierOrchestrator, ClarifierMode
from clarifier.core.clarifier_orchestrator import ClarificationRequest

async def interactive_clarification_example():
    """交互式澄清示例"""
    print("=== 交互式澄清示例 ===\n")
    
    # 创建Clarifier编排器
    orchestrator = ClarifierOrchestrator()
    
    # 示例PRD内容
    sample_prd = """
    ## 项目名称：智能订单管理系统
    
    ### 项目背景
    随着业务增长，现有的订单处理流程已无法满足需求。需要开发一个新的智能订单管理系统。
    
    ### 功能需求
    1. 订单创建和管理
       - 用户可以创建新订单
       - 查看订单历史
       - 修改订单信息
    
    2. 支付集成
       - 支持多种支付方式
       - 处理支付结果
    
    3. 库存管理
       - 实时更新库存
       - 库存预警
    
    4. 用户管理
       - 用户注册和登录
       - 用户信息管理
    
    ### 技术要求
    - 高并发支持
    - 数据安全
    - 系统稳定性
    """
    
    # 启动交互式澄清会话
    session_id, result = await orchestrator.start_clarification_session(
        prd_content=sample_prd,
        mode=ClarifierMode.INTERACTIVE,
        context={
            "project_type": "e-commerce",
            "user_scale": "large"
        }
    )
    
    print(f"会话ID: {session_id}")
    print(f"检测到的盲点数量: {result['total_blind_spots']}")
    print(f"\n盲点摘要:")
    print(json.dumps(result['blind_spots_summary'], ensure_ascii=False, indent=2))
    
    # 获取第一个需要澄清的盲点
    if result['next_action']['type'] == 'clarification_needed':
        blind_spot = result['next_action']['blind_spot']
        print(f"\n需要澄清的盲点: {blind_spot['title']}")
        print(f"描述: {blind_spot['description']}")
        print(f"严重程度: {blind_spot['severity']}")
        print(f"\n问题:")
        for q in blind_spot['questions']:
            print(f"  - {q}")
        
        # 模拟用户回答
        user_response = """
        关于支付失败处理：
        1. 支付失败时系统会自动重试3次，每次间隔30秒
        2. 支付超时时间设置为5分钟，超时后订单状态变为"待支付"
        3. 通过订单号和时间戳生成唯一支付ID来防止重复支付
        4. 退款会在1-3个工作日内原路返回，失败时人工介入
        5. 每日凌晨2点自动与支付平台对账，发现异常发送告警邮件
        """
        
        # 处理澄清
        clarification_result = await orchestrator.process_clarification(
            session_id=session_id,
            clarification=ClarificationRequest(
                blind_spot_id=blind_spot['id'],
                user_response=user_response
            )
        )
        
        print(f"\n澄清处理结果:")
        print(f"状态: {clarification_result['status']}")
        print(f"新版本: {clarification_result['new_version']}")
        print(f"剩余盲点: {clarification_result['blind_spots_remaining']}")
    
    # 获取会话状态
    session_status = orchestrator.get_session_status(session_id)
    print(f"\n会话进度:")
    print(json.dumps(session_status['progress'], ensure_ascii=False, indent=2))

async def prd_analysis_example():
    """PRD自动分析增强示例"""
    print("\n\n=== PRD自动分析增强示例 ===\n")
    
    orchestrator = ClarifierOrchestrator()
    
    sample_prd = """
    ## 社交媒体内容管理平台
    
    ### 功能描述
    1. 内容发布：支持发布文字、图片、视频内容
    2. 内容审核：自动审核违规内容
    3. 数据分析：查看内容表现数据
    4. 用户互动：点赞、评论、分享功能
    """
    
    # 启动PRD分析模式
    session_id, result = await orchestrator.start_clarification_session(
        prd_content=sample_prd,
        mode=ClarifierMode.PRD_ANALYSIS
    )
    
    print(f"自动增强结果:")
    print(f"增强版本ID: {result['next_action']['enhanced_version']}")
    print(f"处理的盲点数: {result['next_action']['blind_spots_addressed']}")
    print(f"\n增强摘要:")
    print(json.dumps(
        result['next_action']['enhancement_summary'], 
        ensure_ascii=False, 
        indent=2
    ))

async def requirement_change_example():
    """需求变更处理示例"""
    print("\n\n=== 需求变更处理示例 ===\n")
    
    orchestrator = ClarifierOrchestrator()
    
    # 先初始化一个项目
    initial_prd = """
    ## 在线教育平台
    
    ### 核心功能
    1. 课程管理：创建、编辑、发布课程
    2. 学习进度：跟踪学生学习进度
    3. 在线考试：支持多种题型的在线考试
    """
    
    initial_summary = {
        "project_name": "在线教育平台",
        "features": ["课程管理", "学习进度", "在线考试"],
        "technical_requirements": {
            "database": "MySQL",
            "framework": "Spring Boot"
        }
    }
    
    # 初始化版本
    version_id = orchestrator.version_manager.initialize_with_prd(
        initial_prd,
        initial_summary
    )
    print(f"初始版本: {version_id}")
    
    # 模拟需求变更
    change_request = {
        "type": "feature_addition",
        "description": "添加实时互动直播功能",
        "details": {
            "feature_name": "直播课堂",
            "requirements": [
                "支持1对多实时视频直播",
                "支持屏幕共享",
                "支持实时聊天互动",
                "支持直播录制和回放"
            ]
        }
    }
    
    # 处理需求变更（分析影响）
    impact_result = await orchestrator.handle_requirement_change(
        change_request=change_request,
        auto_execute=False
    )
    
    print(f"\n变更影响分析:")
    print(f"预计工作量: {impact_result['estimated_effort']}")
    print(f"影响分析:")
    print(json.dumps(
        impact_result['impact_analysis'], 
        ensure_ascii=False, 
        indent=2
    ))
    
    # 如果用户确认，执行重构
    if impact_result['status'] == 'pending_confirmation':
        print("\n执行重构...")
        refactoring_result = await orchestrator.execute_refactoring(
            impact_result['refactoring_plan']
        )
        
        print(f"重构结果:")
        print(f"成功: {refactoring_result['success']}")
        print(f"新版本: {refactoring_result['version_id']}")
        print(f"变更内容:")
        for change in refactoring_result['changes_made']:
            print(f"  - {change}")

async def generate_final_summary_example():
    """生成最终结构化摘要示例"""
    print("\n\n=== 生成最终结构化摘要示例 ===\n")
    
    orchestrator = ClarifierOrchestrator()
    
    # 使用一个完整的PRD
    complete_prd = """
    ## 智能客服系统
    
    ### 项目概述
    开发一个基于AI的智能客服系统，支持多渠道接入，自动回答常见问题，并能够智能转接人工客服。
    
    ### 功能需求
    
    1. 多渠道接入
       - 网页聊天窗口
       - 微信公众号
       - APP内聊天
       - 电话语音接入
    
    2. 智能问答
       - 基于知识库的自动回答
       - 支持上下文理解
       - 意图识别准确率>90%
       - 支持多轮对话
    
    3. 人工转接
       - 智能判断转接时机
       - 保留对话上下文
       - 客服分组和技能匹配
       - 排队管理
    
    4. 知识库管理
       - FAQ导入和编辑
       - 自动学习和优化
       - 版本管理
       - 效果统计
    
    ### 性能要求
    - 并发用户数：10000
    - 响应时间：<500ms
    - 可用性：99.9%
    
    ### 安全要求
    - 数据加密传输
    - 用户隐私保护
    - 访问权限控制
    """
    
    # 初始化并生成摘要
    version_id = orchestrator.version_manager.initialize_with_prd(
        complete_prd,
        {"project_name": "智能客服系统"}
    )
    
    # 生成结构化摘要
    final_summary = await orchestrator.generate_structured_summary(complete_prd)
    
    print(f"质量分数: {final_summary['quality_score']}")
    print(f"\n生成的结构化摘要:")
    print(json.dumps(
        final_summary['summary'], 
        ensure_ascii=False, 
        indent=2
    ))

async def main():
    """运行所有示例"""
    # 1. 交互式澄清
    await interactive_clarification_example()
    
    # 2. PRD自动分析
    await prd_analysis_example()
    
    # 3. 需求变更处理
    await requirement_change_example()
    
    # 4. 生成最终摘要
    await generate_final_summary_example()

if __name__ == "__main__":
    asyncio.run(main())