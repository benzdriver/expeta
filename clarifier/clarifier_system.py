"""
Clarifier 系统 - 面向非技术用户的需求澄清系统。
通过友好的对话引导 Business Owner/PM 澄清业务需求。
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import json

class ClarificationStage(Enum):
    """澄清阶段"""
    INITIAL_IDEA = "initial_idea"  # 初始想法收集
    BUSINESS_GOALS = "business_goals"  # 业务目标澄清
    TARGET_USERS = "target_users"  # 目标用户定义
    CORE_FEATURES = "core_features"  # 核心功能澄清
    USER_JOURNEY = "user_journey"  # 用户旅程
    CONSTRAINTS = "constraints"  # 约束和限制
    SUCCESS_METRICS = "success_metrics"  # 成功指标

@dataclass
class ClarifierQuestion:
    """澄清问题"""
    stage: ClarificationStage
    question: str
    follow_ups: List[str]  # 可能的追问
    examples: List[str]  # 帮助用户理解的例子
    validation_hints: List[str]  # 验证答案完整性的提示

class BusinessClarifier:
    """业务需求澄清器"""
    
    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        self.clarified_requirements: Dict[str, Any] = {
            "project_name": "",
            "description": "",
            "business_goals": [],
            "target_users": [],
            "core_features": [],
            "user_stories": [],
            "constraints": {},
            "success_metrics": []
        }
        self.current_stage = ClarificationStage.INITIAL_IDEA
        
    def get_stage_questions(self, stage: ClarificationStage) -> List[ClarifierQuestion]:
        """获取特定阶段的澄清问题"""
        
        questions_map = {
            ClarificationStage.INITIAL_IDEA: [
                ClarifierQuestion(
                    stage=stage,
                    question="您好！我来帮您理清项目需求。首先，能简单描述一下您想要构建什么样的产品或系统吗？",
                    follow_ups=[
                        "这个产品主要解决什么问题？",
                        "您是如何想到这个想法的？",
                        "有没有类似的产品可以参考？"
                    ],
                    examples=[
                        "比如：我想做一个帮助餐厅管理订单的系统",
                        "比如：我需要一个员工考勤管理平台",
                        "比如：我想建立一个连接律师和客户的平台"
                    ],
                    validation_hints=[
                        "确保描述了产品的核心价值",
                        "明确了要解决的问题"
                    ]
                )
            ],
            
            ClarificationStage.BUSINESS_GOALS: [
                ClarifierQuestion(
                    stage=stage,
                    question="很好！现在让我们明确一下业务目标。您希望这个系统达到什么样的业务效果？",
                    follow_ups=[
                        "最重要的3个目标是什么？",
                        "如何衡量这些目标是否达成？",
                        "预期多久能看到效果？"
                    ],
                    examples=[
                        "提高运营效率30%",
                        "减少人工处理时间",
                        "提升客户满意度",
                        "增加20%的销售额"
                    ],
                    validation_hints=[
                        "目标应该是可衡量的",
                        "目标应该与业务价值相关"
                    ]
                )
            ],
            
            ClarificationStage.TARGET_USERS: [
                ClarifierQuestion(
                    stage=stage,
                    question="谁会使用这个系统？能描述一下您的目标用户吗？",
                    follow_ups=[
                        "他们的年龄范围是？",
                        "他们的技术水平如何？",
                        "他们现在是如何解决这个问题的？",
                        "大概会有多少用户？"
                    ],
                    examples=[
                        "餐厅老板，35-55岁，不太懂技术",
                        "HR人员，需要管理50-500名员工",
                        "需要法律服务的个人，各年龄段都有"
                    ],
                    validation_hints=[
                        "用户画像要具体",
                        "考虑不同类型的用户角色"
                    ]
                )
            ],
            
            ClarificationStage.CORE_FEATURES: [
                ClarifierQuestion(
                    stage=stage,
                    question="基于您的目标用户，系统需要哪些核心功能？请列出最重要的3-5个功能。",
                    follow_ups=[
                        "哪个功能是最最重要的？",
                        "用户会如何使用这个功能？",
                        "这个功能解决什么具体问题？"
                    ],
                    examples=[
                        "在线下单和支付",
                        "实时订单跟踪",
                        "库存管理",
                        "数据报表和分析"
                    ],
                    validation_hints=[
                        "功能要与用户需求对应",
                        "避免功能过多，聚焦核心"
                    ]
                )
            ],
            
            ClarificationStage.USER_JOURNEY: [
                ClarifierQuestion(
                    stage=stage,
                    question="让我们想象一个典型用户使用您系统的场景。能描述一下从开始到结束的完整流程吗？",
                    follow_ups=[
                        "用户如何发现/进入系统？",
                        "第一次使用需要做什么？",
                        "日常使用的典型流程是？",
                        "遇到问题时如何处理？"
                    ],
                    examples=[
                        "用户通过手机号注册 -> 浏览商品 -> 加入购物车 -> 下单支付 -> 查看订单状态",
                        "HR登录系统 -> 查看考勤异常 -> 处理请假申请 -> 生成月度报表"
                    ],
                    validation_hints=[
                        "流程要完整连贯",
                        "考虑异常情况处理"
                    ]
                )
            ],
            
            ClarificationStage.CONSTRAINTS: [
                ClarifierQuestion(
                    stage=stage,
                    question="在实施这个项目时，有什么限制或约束条件需要考虑吗？",
                    follow_ups=[
                        "预算范围大概是多少？",
                        "希望什么时候上线？",
                        "有特定的技术要求吗？",
                        "需要遵守什么法规吗？"
                    ],
                    examples=[
                        "预算10-50万",
                        "必须在3个月内上线MVP",
                        "需要支持手机和电脑访问",
                        "需要符合个人信息保护法"
                    ],
                    validation_hints=[
                        "约束要现实可行",
                        "考虑技术和非技术约束"
                    ]
                )
            ],
            
            ClarificationStage.SUCCESS_METRICS: [
                ClarifierQuestion(
                    stage=stage,
                    question="最后，如何判断这个项目是成功的？有哪些具体的衡量指标？",
                    follow_ups=[
                        "上线后第一个月的目标？",
                        "一年后希望达到什么规模？",
                        "最关注哪个指标？"
                    ],
                    examples=[
                        "日活跃用户达到1000",
                        "每月处理订单超过10000单",
                        "客户满意度达到90%",
                        "系统可用性达到99.9%"
                    ],
                    validation_hints=[
                        "指标要可量化",
                        "设定合理的时间范围"
                    ]
                )
            ]
        }
        
        return questions_map.get(stage, [])
    
    async def process_user_response(self, user_response: str) -> Dict[str, Any]:
        """处理用户回复并生成下一个问题或澄清"""
        
        # 记录对话历史
        self.conversation_history.append({
            "stage": self.current_stage.value,
            "user": user_response,
            "assistant": ""  # 将在后面填充
        })
        
        # 更新需求信息
        self._update_requirements(user_response)
        
        # 检查当前阶段是否完成
        if self._is_stage_complete():
            # 进入下一阶段
            next_stage = self._get_next_stage()
            if next_stage:
                self.current_stage = next_stage
                return self._generate_next_question()
            else:
                # 所有阶段完成，生成最终摘要
                return self._generate_final_summary()
        else:
            # 生成追问
            return self._generate_follow_up()
    
    def _update_requirements(self, response: str):
        """根据用户回复更新需求信息"""
        stage = self.current_stage
        
        if stage == ClarificationStage.INITIAL_IDEA:
            if not self.clarified_requirements["description"]:
                self.clarified_requirements["description"] = response
                # 尝试提取项目名称
                if "做一个" in response or "需要一个" in response:
                    # 简单的名称提取逻辑
                    self.clarified_requirements["project_name"] = "待定项目"
                    
        elif stage == ClarificationStage.BUSINESS_GOALS:
            # 提取业务目标
            goals = [g.strip() for g in response.split(",") if g.strip()]
            self.clarified_requirements["business_goals"].extend(goals)
            
        elif stage == ClarificationStage.TARGET_USERS:
            # 提取用户信息
            self.clarified_requirements["target_users"].append({
                "description": response,
                "extracted_info": self._extract_user_info(response)
            })
            
        # ... 其他阶段的处理
    
    def _is_stage_complete(self) -> bool:
        """检查当前阶段是否收集了足够信息"""
        stage = self.current_stage
        
        if stage == ClarificationStage.INITIAL_IDEA:
            return bool(self.clarified_requirements["description"])
        elif stage == ClarificationStage.BUSINESS_GOALS:
            return len(self.clarified_requirements["business_goals"]) >= 2
        elif stage == ClarificationStage.TARGET_USERS:
            return len(self.clarified_requirements["target_users"]) >= 1
        elif stage == ClarificationStage.CORE_FEATURES:
            return len(self.clarified_requirements["core_features"]) >= 3
        # ... 其他阶段
        
        return False
    
    def _generate_next_question(self) -> Dict[str, Any]:
        """生成下一个主要问题"""
        questions = self.get_stage_questions(self.current_stage)
        if questions:
            question = questions[0]
            
            response = {
                "type": "question",
                "stage": self.current_stage.value,
                "question": question.question,
                "examples": question.examples,
                "hints": f"提示：{', '.join(question.validation_hints)}"
            }
            
            # 更新对话历史
            if self.conversation_history:
                self.conversation_history[-1]["assistant"] = question.question
                
            return response
        
        return {"type": "error", "message": "没有更多问题"}
    
    def _generate_follow_up(self) -> Dict[str, Any]:
        """生成追问"""
        questions = self.get_stage_questions(self.current_stage)
        if questions and questions[0].follow_ups:
            # 选择合适的追问
            follow_up = questions[0].follow_ups[0]  # 简化逻辑，实际应该更智能
            
            return {
                "type": "follow_up",
                "stage": self.current_stage.value,
                "question": follow_up,
                "hint": "请提供更多细节"
            }
        
        return self._generate_next_question()
    
    def _generate_final_summary(self) -> Dict[str, Any]:
        """生成最终的需求摘要"""
        summary = {
            "type": "summary",
            "status": "complete",
            "clarified_requirements": self.clarified_requirements,
            "conversation_summary": {
                "total_exchanges": len(self.conversation_history),
                "stages_completed": [s.value for s in ClarificationStage]
            },
            "next_steps": [
                "需求已澄清完毕",
                "可以开始技术方案设计",
                "建议与技术团队评审"
            ],
            "structured_output": self._generate_structured_json()
        }
        
        return summary
    
    def _generate_structured_json(self) -> Dict[str, Any]:
        """生成结构化的JSON输出"""
        return {
            "project": {
                "name": self.clarified_requirements["project_name"],
                "description": self.clarified_requirements["description"],
                "type": self._infer_project_type()
            },
            "business": {
                "goals": self.clarified_requirements["business_goals"],
                "success_metrics": self.clarified_requirements["success_metrics"],
                "target_scale": self._extract_scale_info()
            },
            "users": {
                "primary": self.clarified_requirements["target_users"],
                "estimated_count": self._estimate_user_count()
            },
            "features": {
                "core": self.clarified_requirements["core_features"],
                "user_stories": self.clarified_requirements["user_stories"]
            },
            "constraints": self.clarified_requirements["constraints"],
            "metadata": {
                "clarification_version": "1.0",
                "completed_at": "2024-01-01",  # 实际应该是当前时间
                "conversation_length": len(self.conversation_history)
            }
        }
    
    def _infer_project_type(self) -> str:
        """推断项目类型"""
        desc = self.clarified_requirements["description"].lower()
        if "平台" in desc:
            return "platform"
        elif "系统" in desc:
            return "system"
        elif "应用" in desc or "app" in desc:
            return "application"
        elif "网站" in desc:
            return "website"
        return "unknown"
    
    def _extract_user_info(self, response: str) -> Dict[str, Any]:
        """从用户描述中提取信息"""
        # 简化的提取逻辑
        info = {
            "age_range": "未指定",
            "tech_level": "未指定",
            "count": "未指定"
        }
        
        # 实际应该使用NLP或正则表达式提取
        if "岁" in response:
            # 提取年龄信息
            pass
        
        return info
    
    def _extract_scale_info(self) -> Dict[str, Any]:
        """提取规模信息"""
        return {
            "initial": "MVP",
            "target": "根据对话内容推断"
        }
    
    def _estimate_user_count(self) -> str:
        """估算用户数量"""
        # 基于对话内容估算
        return "1000-10000"
    
    def _get_next_stage(self) -> Optional[ClarificationStage]:
        """获取下一个阶段"""
        stages = list(ClarificationStage)
        current_index = stages.index(self.current_stage)
        
        if current_index < len(stages) - 1:
            return stages[current_index + 1]
        
        return None

# 使用示例
async def clarify_requirements():
    """需求澄清的完整流程示例"""
    clarifier = BusinessClarifier()
    
    # 开始对话
    initial_question = clarifier._generate_next_question()
    print(f"助手: {initial_question['question']}")
    
    # 模拟用户回复
    user_response = "我想做一个帮助移民顾问管理客户申请的系统"
    
    # 处理回复
    next_response = await clarifier.process_user_response(user_response)
    
    # 继续对话直到完成...
    
    return clarifier._generate_structured_json()