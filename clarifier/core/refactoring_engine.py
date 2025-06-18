"""
智能重构引擎的完整实现
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json
import copy
from datetime import datetime

from llm_services.executor import run_prompt
from common.logger import Logger

logger = Logger.get_instance('clarifier')

from .version_manager import VersionManager, ChangeType
from .impact_analyzer import ImpactAnalyzer

class RefactoringStrategy(Enum):
    """重构策略"""
    INCREMENTAL = "incremental"  # 增量式重构
    BIG_BANG = "big_bang"      # 一次性重构
    PARALLEL = "parallel"       # 并行重构
    FEATURE_TOGGLE = "feature_toggle"  # 特性开关

@dataclass
class RefactoringStep:
    """重构步骤"""
    step_number: int
    action: str
    target_component: str
    description: str
    prerequisites: List[str]
    estimated_time: str
    validation_criteria: str
    rollback_procedure: str

@dataclass
class RefactoringResult:
    """重构结果"""
    success: bool
    updated_prd: str
    updated_json_summary: Dict[str, Any]
    changes_made: List[str]
    validation_results: Dict[str, bool]
    new_version_id: str

class SmartRefactoring:
    """智能重构执行器"""
    
    def __init__(
        self,
        version_manager: VersionManager,
        impact_analyzer: ImpactAnalyzer
    ):
        self.version_manager = version_manager
        self.impact_analyzer = impact_analyzer
        self.refactoring_history = []
        
    async def handle_requirement_change(
        self,
        current_prd: str,
        current_summary: Dict[str, Any],
        change_request: Dict[str, Any],
        auto_execute: bool = False
    ) -> Dict[str, Any]:
        """处理需求变更"""
        logger.log(f"🔧 处理需求变更: {change_request.get('description', 'Unknown')}", level="info")
        
        # 1. 分析变更影响
        impact_analysis = await self.impact_analyzer.analyze_requirement_change(
            change_request,
            current_summary
        )
        
        # 2. 生成重构计划
        refactoring_plan = await self._create_refactoring_plan(
            change_request,
            impact_analysis,
            current_summary
        )
        
        # 3. 验证计划可行性
        feasibility_check = self._check_feasibility(
            refactoring_plan,
            impact_analysis
        )
        
        # 4. 如果不自动执行，返回计划供确认
        if not auto_execute:
            return {
                "status": "pending_confirmation",
                "change_request": change_request,
                "impact_analysis": impact_analysis,
                "refactoring_plan": refactoring_plan,
                "feasibility": feasibility_check,
                "estimated_effort": impact_analysis["effort_estimation"],
                "confirmation_required": True
            }
        
        # 5. 执行重构
        result = await self._execute_refactoring(
            current_prd,
            current_summary,
            change_request,
            refactoring_plan
        )
        
        # 6. 记录历史
        self._record_refactoring(
            change_request,
            impact_analysis,
            refactoring_plan,
            result
        )
        
        return {
            "status": "completed",
            "result": result,
            "impact_analysis": impact_analysis,
            "refactoring_plan": refactoring_plan
        }
    
    async def _create_refactoring_plan(
        self,
        change_request: Dict[str, Any],
        impact_analysis: Dict[str, Any],
        current_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建重构计划"""
        # 1. 选择重构策略
        strategy = self._select_refactoring_strategy(
            change_request,
            impact_analysis
        )
        
        # 2. 生成重构步骤
        steps = await self._generate_refactoring_steps(
            change_request,
            impact_analysis,
            strategy
        )
        
        # 3. 创建验证计划
        validation_plan = self._create_validation_plan(
            steps,
            impact_analysis
        )
        
        # 4. 评估风险和制定应急计划
        contingency_plan = self._create_contingency_plan(
            impact_analysis["risk_assessment"]
        )
        
        return {
            "strategy": strategy.value,
            "steps": steps,
            "validation_plan": validation_plan,
            "contingency_plan": contingency_plan,
            "estimated_duration": self._estimate_duration(steps),
            "parallelizable_steps": self._identify_parallel_steps(steps)
        }
    
    def _select_refactoring_strategy(
        self,
        change_request: Dict[str, Any],
        impact_analysis: Dict[str, Any]
    ) -> RefactoringStrategy:
        """选择重构策略"""
        risk_level = impact_analysis["risk_assessment"].risk_level
        total_components = impact_analysis["impact_analysis"]["total_affected_components"]
        
        # 基于风险和影响范围选择策略
        if risk_level == "high" or total_components > 10:
            # 高风险或大范围影响，使用增量式
            return RefactoringStrategy.INCREMENTAL
        elif change_request.get("urgent", False):
            # 紧急变更，一次性完成
            return RefactoringStrategy.BIG_BANG
        elif total_components > 5:
            # 中等范围，可以并行
            return RefactoringStrategy.PARALLEL
        else:
            # 使用特性开关逐步切换
            return RefactoringStrategy.FEATURE_TOGGLE
    
    async def _generate_refactoring_steps(
        self,
        change_request: Dict[str, Any],
        impact_analysis: Dict[str, Any],
        strategy: RefactoringStrategy
    ) -> List[RefactoringStep]:
        """生成重构步骤"""
        steps = []
        step_number = 1
        
        # 根据策略生成不同的步骤序列
        if strategy == RefactoringStrategy.INCREMENTAL:
            # 增量式：按优先级逐步处理
            for action in impact_analysis["refactoring_plan"].immediate_actions:
                steps.append(self._create_step(
                    step_number,
                    action,
                    priority="immediate"
                ))
                step_number += 1
                
            for action in impact_analysis["refactoring_plan"].short_term_actions:
                steps.append(self._create_step(
                    step_number,
                    action,
                    priority="short_term"
                ))
                step_number += 1
                
        elif strategy == RefactoringStrategy.PARALLEL:
            # 并行：识别可并行的步骤
            parallel_groups = self._group_parallel_actions(
                impact_analysis["refactoring_plan"]
            )
            
            for group in parallel_groups:
                for action in group:
                    steps.append(self._create_step(
                        step_number,
                        action,
                        parallel_group=group
                    ))
                step_number += 1
        
        else:
            # 其他策略的步骤生成
            all_actions = (
                impact_analysis["refactoring_plan"].immediate_actions +
                impact_analysis["refactoring_plan"].short_term_actions
            )
            
            for action in all_actions:
                steps.append(self._create_step(step_number, action))
                step_number += 1
        
        return steps
    
    def _create_step(
        self,
        step_number: int,
        action: Dict[str, Any],
        priority: str = "normal",
        parallel_group: Optional[List] = None
    ) -> RefactoringStep:
        """创建单个重构步骤"""
        return RefactoringStep(
            step_number=step_number,
            action=action["action"],
            target_component=action["component"],
            description=f"{action['action']} (优先级: {action.get('priority', priority)})",
            prerequisites=self._identify_prerequisites(action, step_number),
            estimated_time=action["estimated_time"],
            validation_criteria=self._define_validation_criteria(action),
            rollback_procedure=self._define_rollback_procedure(action)
        )
    
    def _identify_prerequisites(
        self,
        action: Dict[str, Any],
        step_number: int
    ) -> List[str]:
        """识别步骤的前置条件"""
        prerequisites = []
        
        # 基本前置条件
        if step_number > 1:
            prerequisites.append(f"步骤{step_number-1}完成")
        
        # 组件特定的前置条件
        if action["component"] == "database":
            prerequisites.append("数据库备份完成")
        elif action["component"] == "api":
            prerequisites.append("API版本策略确定")
        elif "deployment" in action["action"].lower():
            prerequisites.append("所有测试通过")
        
        return prerequisites
    
    def _define_validation_criteria(self, action: Dict[str, Any]) -> str:
        """定义验证标准"""
        component = action["component"]
        
        validation_map = {
            "database": "数据迁移脚本执行成功，数据完整性检查通过",
            "api": "API测试套件全部通过，向后兼容性确认",
            "frontend": "UI测试通过，用户体验验证完成",
            "backend": "单元测试和集成测试通过",
            "testing": "测试覆盖率达标，所有测试用例更新"
        }
        
        return validation_map.get(component, "相关测试通过，功能正常")
    
    def _define_rollback_procedure(self, action: Dict[str, Any]) -> str:
        """定义回滚步骤"""
        component = action["component"]
        
        rollback_map = {
            "database": "执行数据库回滚脚本，恢复备份",
            "api": "切换到旧版本API，更新路由配置",
            "frontend": "部署前一版本的前端代码",
            "backend": "回滚到前一版本的后端服务",
            "testing": "恢复原有测试配置"
        }
        
        return rollback_map.get(component, "恢复到变更前的版本")
    
    def _group_parallel_actions(
        self,
        refactoring_plan: Any
    ) -> List[List[Dict[str, Any]]]:
        """将可并行的动作分组"""
        # 简化实现：将没有依赖关系的动作分为一组
        all_actions = (
            refactoring_plan.immediate_actions +
            refactoring_plan.short_term_actions
        )
        
        # 这里应该基于依赖关系图进行更智能的分组
        # 现在简单地将相同优先级的分为一组
        groups = {}
        for action in all_actions:
            priority = action.get("priority", "P2")
            if priority not in groups:
                groups[priority] = []
            groups[priority].append(action)
        
        return list(groups.values())
    
    def _create_validation_plan(
        self,
        steps: List[RefactoringStep],
        impact_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建验证计划"""
        return {
            "validation_stages": [
                {
                    "stage": "pre_refactoring",
                    "tasks": [
                        "备份当前版本",
                        "记录当前性能基准",
                        "确认回滚方案"
                    ]
                },
                {
                    "stage": "during_refactoring",
                    "tasks": [
                        "每步骤后验证",
                        "监控系统状态",
                        "检查错误日志"
                    ]
                },
                {
                    "stage": "post_refactoring",
                    "tasks": [
                        "完整功能测试",
                        "性能对比测试",
                        "安全扫描",
                        "用户验收测试"
                    ]
                }
            ],
            "success_criteria": {
                "functional": "所有功能测试通过",
                "performance": "性能不低于基准线",
                "security": "无新增安全漏洞",
                "compatibility": "向后兼容性保持"
            },
            "validation_tools": [
                "自动化测试套件",
                "性能监控工具",
                "安全扫描工具",
                "用户反馈系统"
            ]
        }
    
    def _create_contingency_plan(self, risk_assessment: Any) -> Dict[str, Any]:
        """创建应急计划"""
        return {
            "risk_level": risk_assessment.risk_level,
            "trigger_conditions": [
                "关键功能失败",
                "性能严重下降",
                "数据一致性问题",
                "安全漏洞发现"
            ],
            "immediate_actions": [
                "停止后续重构步骤",
                "评估当前状态",
                "决定是修复还是回滚"
            ],
            "rollback_strategy": risk_assessment.rollback_plan,
            "communication_plan": {
                "internal": "通知开发团队和管理层",
                "external": "准备用户通知模板",
                "stakeholders": "更新项目干系人"
            },
            "post_incident": [
                "根因分析",
                "更新重构计划",
                "改进测试覆盖"
            ]
        }
    
    def _estimate_duration(self, steps: List[RefactoringStep]) -> str:
        """估算重构持续时间"""
        total_hours = 0
        
        for step in steps:
            # 解析时间字符串
            time_str = step.estimated_time
            if "小时" in time_str:
                hours = int(time_str.replace("小时", "").strip())
            elif "天" in time_str:
                days = int(time_str.replace("天", "").strip())
                hours = days * 8
            else:
                hours = 4  # 默认4小时
                
            total_hours += hours
        
        if total_hours <= 8:
            return "1天"
        elif total_hours <= 40:
            return f"{(total_hours + 7) // 8}天"
        else:
            return f"{(total_hours + 39) // 40}周"
    
    def _identify_parallel_steps(
        self,
        steps: List[RefactoringStep]
    ) -> List[List[int]]:
        """识别可并行执行的步骤"""
        parallel_groups = []
        
        # 简化逻辑：没有相互依赖的步骤可以并行
        independent_steps = []
        for i, step in enumerate(steps):
            # 如果没有依赖其他步骤（除了基本的顺序依赖）
            if len(step.prerequisites) <= 1:
                independent_steps.append(i + 1)  # 步骤号从1开始
        
        if len(independent_steps) > 1:
            parallel_groups.append(independent_steps)
        
        return parallel_groups
    
    def _check_feasibility(
        self,
        refactoring_plan: Dict[str, Any],
        impact_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查重构计划的可行性"""
        feasibility_score = 100
        issues = []
        recommendations = []
        
        # 检查工作量
        total_effort = impact_analysis["effort_estimation"]["total_effort_hours"]
        if total_effort > 160:  # 超过一个月
            feasibility_score -= 20
            issues.append("工作量较大，需要较长时间完成")
            recommendations.append("考虑分阶段实施")
        
        # 检查风险
        risk_level = impact_analysis["risk_assessment"].risk_level
        if risk_level == "high":
            feasibility_score -= 30
            issues.append("风险级别高")
            recommendations.append("增加测试投入，准备充分的回滚方案")
        
        # 检查资源
        recommended_team_size = impact_analysis["effort_estimation"]["recommended_team_size"]
        if recommended_team_size > 5:
            feasibility_score -= 10
            issues.append(f"需要{recommended_team_size}人的团队")
            recommendations.append("确保有足够的人力资源")
        
        # 检查依赖
        if len(refactoring_plan["steps"]) > 20:
            feasibility_score -= 15
            issues.append("重构步骤过多，复杂度高")
            recommendations.append("考虑简化重构方案")
        
        return {
            "feasibility_score": max(0, feasibility_score),
            "is_feasible": feasibility_score >= 60,
            "issues": issues,
            "recommendations": recommendations,
            "confidence_level": "high" if feasibility_score >= 80 else "medium" if feasibility_score >= 60 else "low"
        }
    
    async def _execute_refactoring(
        self,
        current_prd: str,
        current_summary: Dict[str, Any],
        change_request: Dict[str, Any],
        refactoring_plan: Dict[str, Any]
    ) -> RefactoringResult:
        """执行重构"""
        logger.log("🚀 开始执行重构", level="info")
        
        # 1. 执行PRD更新
        updated_prd = await self._update_prd(
            current_prd,
            change_request,
            refactoring_plan
        )
        
        # 2. 执行JSON Summary更新
        updated_summary = await self._update_json_summary(
            current_summary,
            change_request,
            refactoring_plan
        )
        
        # 3. 验证更新
        validation_results = await self._validate_updates(
            updated_prd,
            updated_summary,
            refactoring_plan["validation_plan"]
        )
        
        # 4. 创建新版本
        new_version_id = self.version_manager.save_requirement_change(
            updated_prd,
            updated_summary,
            change_request
        )
        
        # 5. 记录变更
        changes_made = self._summarize_changes(
            current_summary,
            updated_summary
        )
        
        return RefactoringResult(
            success=all(validation_results.values()),
            updated_prd=updated_prd,
            updated_json_summary=updated_summary,
            changes_made=changes_made,
            validation_results=validation_results,
            new_version_id=new_version_id
        )
    
    async def _update_prd(
        self,
        current_prd: str,
        change_request: Dict[str, Any],
        refactoring_plan: Dict[str, Any]
    ) -> str:
        """更新PRD文档"""
        update_prompt = f"""
        根据以下变更请求更新PRD文档：
        
        变更请求：
        {json.dumps(change_request, ensure_ascii=False, indent=2)}
        
        重构计划摘要：
        - 策略: {refactoring_plan['strategy']}
        - 主要步骤: {len(refactoring_plan['steps'])}个
        
        当前PRD：
        {current_prd}
        
        请更新PRD文档，确保：
        1. 准确反映变更内容
        2. 保持文档结构的一致性
        3. 在变更部分添加 [Updated: {datetime.now().strftime('%Y-%m-%d')}] 标记
        4. 更新相关的章节和引用
        
        返回更新后的完整PRD。
        """
        
        updated_prd = await run_prompt(
            system_message="你是一个专业的技术文档编写专家",
            user_message=update_prompt,
            temperature=0.3
        )
        
        return updated_prd
    
    async def _update_json_summary(
        self,
        current_summary: Dict[str, Any],
        change_request: Dict[str, Any],
        refactoring_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新JSON摘要"""
        # 深拷贝当前摘要
        updated_summary = copy.deepcopy(current_summary)
        
        # 根据变更类型更新相应部分
        change_type = change_request.get("type", "").lower()
        
        if "feature" in change_type:
            await self._update_feature_in_summary(
                updated_summary,
                change_request
            )
        elif "api" in change_type:
            await self._update_api_in_summary(
                updated_summary,
                change_request
            )
        elif "technical" in change_type:
            await self._update_technical_in_summary(
                updated_summary,
                change_request
            )
        else:
            # 通用更新逻辑
            await self._generic_update_summary(
                updated_summary,
                change_request
            )
        
        # 更新元数据
        if "metadata" not in updated_summary:
            updated_summary["metadata"] = {}
            
        updated_summary["metadata"].update({
            "last_updated": datetime.now().isoformat(),
            "last_change_type": change_type,
            "version": updated_summary["metadata"].get("version", "1.0.0"),
            "refactoring_strategy": refactoring_plan["strategy"]
        })
        
        return updated_summary
    
    async def _update_feature_in_summary(
        self,
        summary: Dict[str, Any],
        change_request: Dict[str, Any]
    ):
        """更新功能相关的摘要内容"""
        feature_name = change_request.get("feature", "")
        action = change_request.get("action", "modify")
        details = change_request.get("details", {})
        
        if "functional_requirements" not in summary:
            summary["functional_requirements"] = {"core_features": []}
        
        features = summary["functional_requirements"]["core_features"]
        
        if action == "add":
            # 添加新功能
            new_feature = {
                "name": feature_name,
                "description": details.get("description", ""),
                "priority": details.get("priority", "medium"),
                "acceptance_criteria": details.get("acceptance_criteria", []),
                "dependencies": details.get("dependencies", [])
            }
            features.append(new_feature)
            
        elif action == "modify":
            # 修改现有功能
            for i, feature in enumerate(features):
                if feature.get("name") == feature_name:
                    features[i].update(details)
                    break
            else:
                # 如果没找到，作为新功能添加
                features.append({
                    "name": feature_name,
                    **details
                })
                
        elif action == "remove":
            # 删除功能
            features[:] = [f for f in features if f.get("name") != feature_name]
    
    async def _update_api_in_summary(
        self,
        summary: Dict[str, Any],
        change_request: Dict[str, Any]
    ):
        """更新API相关的摘要内容"""
        if "api_design" not in summary:
            summary["api_design"] = {"endpoints": []}
        
        # API更新逻辑
        api_changes = change_request.get("details", {}).get("api_changes", [])
        
        for change in api_changes:
            action = change.get("action", "modify")
            endpoint = change.get("endpoint", {})
            
            if action == "add":
                summary["api_design"]["endpoints"].append(endpoint)
            elif action == "modify":
                # 查找并更新
                for i, ep in enumerate(summary["api_design"]["endpoints"]):
                    if ep.get("path") == endpoint.get("path"):
                        summary["api_design"]["endpoints"][i].update(endpoint)
                        break
            elif action == "remove":
                summary["api_design"]["endpoints"] = [
                    ep for ep in summary["api_design"]["endpoints"]
                    if ep.get("path") != endpoint.get("path")
                ]
    
    async def _update_technical_in_summary(
        self,
        summary: Dict[str, Any],
        change_request: Dict[str, Any]
    ):
        """更新技术决策相关的摘要内容"""
        if "technical_decisions" not in summary:
            summary["technical_decisions"] = {}
        
        tech_updates = change_request.get("details", {})
        summary["technical_decisions"].update(tech_updates)
    
    async def _generic_update_summary(
        self,
        summary: Dict[str, Any],
        change_request: Dict[str, Any]
    ):
        """通用的摘要更新逻辑"""
        # 使用LLM智能更新
        update_prompt = f"""
        更新JSON摘要以反映以下变更：
        
        变更请求：
        {json.dumps(change_request, ensure_ascii=False, indent=2)}
        
        当前摘要：
        {json.dumps(summary, ensure_ascii=False, indent=2)}
        
        请返回更新后的JSON摘要，确保：
        1. 准确反映变更内容
        2. 保持JSON结构完整性
        3. 不要删除未涉及的内容
        """
        
        response = await run_prompt(
            system_message="你是一个JSON数据处理专家",
            user_message=update_prompt,
            temperature=0.2
        )
        
        try:
            updated = json.loads(response)
            summary.update(updated)
        except json.JSONDecodeError:
            logger.log("⚠️ JSON解析失败，保持原有摘要", level="warning")
    
    async def _validate_updates(
        self,
        updated_prd: str,
        updated_summary: Dict[str, Any],
        validation_plan: Dict[str, Any]
    ) -> Dict[str, bool]:
        """验证更新结果"""
        validation_results = {}
        
        # 1. 结构完整性验证
        validation_results["structure_integrity"] = self._validate_structure(
            updated_prd,
            updated_summary
        )
        
        # 2. 内容一致性验证
        validation_results["content_consistency"] = await self._validate_consistency(
            updated_prd,
            updated_summary
        )
        
        # 3. 业务规则验证
        validation_results["business_rules"] = self._validate_business_rules(
            updated_summary
        )
        
        # 4. 技术可行性验证
        validation_results["technical_feasibility"] = self._validate_technical_feasibility(
            updated_summary
        )
        
        return validation_results
    
    def _validate_structure(
        self,
        prd: str,
        summary: Dict[str, Any]
    ) -> bool:
        """验证结构完整性"""
        # 检查PRD是否包含必要章节
        required_sections = ["项目概述", "功能需求", "非功能需求"]
        prd_valid = all(section in prd for section in required_sections)
        
        # 检查JSON摘要必要字段
        required_fields = ["project", "functional_requirements"]
        summary_valid = all(field in summary for field in required_fields)
        
        return prd_valid and summary_valid
    
    async def _validate_consistency(
        self,
        prd: str,
        summary: Dict[str, Any]
    ) -> bool:
        """验证PRD和JSON摘要的一致性"""
        # 使用LLM检查一致性
        consistency_prompt = f"""
        检查PRD文档和JSON摘要是否一致。
        
        PRD片段（前1000字）：
        {prd[:1000]}
        
        JSON摘要：
        {json.dumps(summary, ensure_ascii=False, indent=2)[:1000]}
        
        请回答：
        1. 主要功能是否一致？
        2. 技术决策是否一致？
        3. 是否有明显的矛盾？
        
        如果完全一致，返回"CONSISTENT"，否则返回"INCONSISTENT"。
        """
        
        response = await run_prompt(
            system_message="你是一个文档一致性检查专家",
            user_message=consistency_prompt,
            temperature=0.1
        )
        
        return "CONSISTENT" in response.upper()
    
    def _validate_business_rules(self, summary: Dict[str, Any]) -> bool:
        """验证业务规则"""
        # 检查是否有冲突的业务规则
        features = summary.get("functional_requirements", {}).get("core_features", [])
        
        # 简单的规则检查示例
        for feature in features:
            # 检查优先级是否有效
            if feature.get("priority") not in ["must-have", "should-have", "nice-to-have", None]:
                return False
                
            # 检查依赖是否存在
            dependencies = feature.get("dependencies", [])
            feature_names = [f.get("name") for f in features]
            
            for dep in dependencies:
                if dep not in feature_names and dep not in ["external_api", "third_party"]:
                    logger.log(f"⚠️ 依赖 {dep} 不存在", level="warning")
                    # 这里可以选择返回False或继续
        
        return True
    
    def _validate_technical_feasibility(self, summary: Dict[str, Any]) -> bool:
        """验证技术可行性"""
        tech = summary.get("technical_decisions", {})
        
        # 检查技术栈兼容性
        incompatible_combinations = [
            ("React", "Angular"),  # 前端框架冲突
            ("MySQL", "PostgreSQL"),  # 数据库冲突（除非明确说明）
        ]
        
        tech_stack = str(tech).lower()
        
        for combo in incompatible_combinations:
            if all(tech.lower() in tech_stack for tech in combo):
                logger.log(f"⚠️ 检测到不兼容的技术组合: {combo}", level="warning")
                return False
        
        return True
    
    def _summarize_changes(
        self,
        old_summary: Dict[str, Any],
        new_summary: Dict[str, Any]
    ) -> List[str]:
        """总结所做的变更"""
        changes = []
        
        # 比较顶层键
        old_keys = set(old_summary.keys())
        new_keys = set(new_summary.keys())
        
        # 新增的键
        for key in new_keys - old_keys:
            changes.append(f"新增: {key}")
        
        # 删除的键
        for key in old_keys - new_keys:
            changes.append(f"删除: {key}")
        
        # 修改的键
        for key in old_keys & new_keys:
            if old_summary[key] != new_summary[key]:
                if isinstance(old_summary[key], list) and isinstance(new_summary[key], list):
                    old_len = len(old_summary[key])
                    new_len = len(new_summary[key])
                    if old_len != new_len:
                        changes.append(f"修改: {key} (项目数: {old_len} -> {new_len})")
                    else:
                        changes.append(f"修改: {key} 内容")
                else:
                    changes.append(f"修改: {key}")
        
        return changes
    
    def _record_refactoring(
        self,
        change_request: Dict[str, Any],
        impact_analysis: Dict[str, Any],
        refactoring_plan: Dict[str, Any],
        result: RefactoringResult
    ):
        """记录重构历史"""
        self.refactoring_history.append({
            "timestamp": datetime.now().isoformat(),
            "change_request": change_request,
            "impact_summary": {
                "total_components": impact_analysis["impact_analysis"]["total_affected_components"],
                "risk_level": impact_analysis["risk_assessment"].risk_level,
                "estimated_effort": impact_analysis["effort_estimation"]["total_effort_hours"]
            },
            "strategy": refactoring_plan["strategy"],
            "success": result.success,
            "new_version": result.new_version_id,
            "changes_made": result.changes_made
        })
    
    async def simulate_refactoring(
        self,
        current_prd: str,
        current_summary: Dict[str, Any],
        change_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """模拟重构（不实际执行）"""
        # 分析影响
        impact_analysis = await self.impact_analyzer.analyze_requirement_change(
            change_request,
            current_summary
        )
        
        # 生成计划
        refactoring_plan = await self._create_refactoring_plan(
            change_request,
            impact_analysis,
            current_summary
        )
        
        # 预测结果
        predicted_changes = self._predict_changes(
            change_request,
            current_summary
        )
        
        return {
            "simulation": True,
            "change_request": change_request,
            "impact_analysis": impact_analysis,
            "refactoring_plan": refactoring_plan,
            "predicted_changes": predicted_changes,
            "estimated_success_rate": self._estimate_success_rate(
                impact_analysis,
                refactoring_plan
            )
        }
    
    def _predict_changes(
        self,
        change_request: Dict[str, Any],
        current_summary: Dict[str, Any]
    ) -> List[str]:
        """预测将会发生的变更"""
        predictions = []
        
        change_type = change_request.get("type", "").lower()
        feature = change_request.get("feature", "")
        
        if "add" in change_type:
            predictions.append(f"将添加新功能: {feature}")
            predictions.append("相关API端点将被创建")
            predictions.append("测试用例将增加")
        elif "modify" in change_type:
            predictions.append(f"将修改功能: {feature}")
            predictions.append("可能影响依赖该功能的其他模块")
        elif "remove" in change_type:
            predictions.append(f"将删除功能: {feature}")
            predictions.append("需要处理依赖关系")
        
        # 基于影响范围预测
        if change_request.get("details", {}).get("breaking_change"):
            predictions.append("⚠️ 这是一个破坏性变更，需要版本管理")
        
        return predictions
    
    def _estimate_success_rate(
        self,
        impact_analysis: Dict[str, Any],
        refactoring_plan: Dict[str, Any]
    ) -> float:
        """估算成功率"""
        base_rate = 0.9
        
        # 根据风险级别调整
        risk_level = impact_analysis["risk_assessment"].risk_level
        if risk_level == "high":
            base_rate -= 0.2
        elif risk_level == "medium":
            base_rate -= 0.1
        
        # 根据影响范围调整
        total_components = impact_analysis["impact_analysis"]["total_affected_components"]
        if total_components > 10:
            base_rate -= 0.15
        elif total_components > 5:
            base_rate -= 0.05
        
        # 根据策略调整
        if refactoring_plan["strategy"] == RefactoringStrategy.INCREMENTAL.value:
            base_rate += 0.1  # 增量式更安全
        
        return max(0.3, min(1.0, base_rate))
    
    def get_refactoring_history(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取重构历史"""
        return self.refactoring_history[-limit:]
    
    def get_refactoring_statistics(self) -> Dict[str, Any]:
        """获取重构统计信息"""
        if not self.refactoring_history:
            return {"message": "暂无重构历史"}
        
        total = len(self.refactoring_history)
        successful = sum(1 for r in self.refactoring_history if r["success"])
        
        strategies = {}
        for record in self.refactoring_history:
            strategy = record["strategy"]
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        total_effort = sum(
            record["impact_summary"]["estimated_effort"]
            for record in self.refactoring_history
        )
        
        return {
            "total_refactorings": total,
            "successful_refactorings": successful,
            "success_rate": successful / total if total > 0 else 0,
            "strategies_used": strategies,
            "total_effort_hours": total_effort,
            "average_effort_hours": total_effort / total if total > 0 else 0
        }

class RefactoringEngine:
    """重构引擎门面"""
    
    def __init__(self):
        self.version_manager = VersionManager()
        self.impact_analyzer = ImpactAnalyzer()
        self.smart_refactoring = SmartRefactoring(
            self.version_manager,
            self.impact_analyzer
        )
    
    async def process_change_request(
        self,
        current_prd: str,
        current_summary: Dict[str, Any],
        change_request: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """处理变更请求"""
        options = options or {}
        
        # 如果是模拟模式
        if options.get("simulate", False):
            return await self.smart_refactoring.simulate_refactoring(
                current_prd,
                current_summary,
                change_request
            )
        
        # 正常处理
        return await self.smart_refactoring.handle_requirement_change(
            current_prd,
            current_summary,
            change_request,
            auto_execute=options.get("auto_execute", False)
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.smart_refactoring.get_refactoring_statistics()
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取历史记录"""
        return self.smart_refactoring.get_refactoring_history(limit)