"""
变更影响分析器的完整实现
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass
import json
from datetime import datetime

from common.logger import Logger

logger = Logger.get_instance('clarifier')

class ComponentType(Enum):
    """组件类型"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    API = "api"
    BUSINESS_LOGIC = "business_logic"
    UI_UX = "ui_ux"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INFRASTRUCTURE = "infrastructure"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"

class ImpactSeverity(Enum):
    """影响严重程度"""
    CRITICAL = "critical"  # 必须立即处理
    HIGH = "high"         # 重要影响
    MEDIUM = "medium"     # 中等影响
    LOW = "low"          # 轻微影响

@dataclass
class Impact:
    """影响描述"""
    component: str
    component_type: ComponentType
    description: str
    severity: ImpactSeverity
    action_required: str
    estimated_effort: str  # 预计工作量
    dependencies: List[str]

@dataclass
class RiskAssessment:
    """风险评估"""
    risk_level: str  # high, medium, low
    risk_factors: List[str]
    mitigation_strategies: List[str]
    rollback_plan: str

@dataclass
class RefactoringPlan:
    """重构计划"""
    immediate_actions: List[Dict[str, Any]]
    short_term_actions: List[Dict[str, Any]]
    long_term_actions: List[Dict[str, Any]]
    estimated_total_effort: str
    recommended_approach: str

class DependencyGraph:
    """依赖关系图"""
    
    def __init__(self):
        self.graph: Dict[str, Set[str]] = {}
        self.reverse_graph: Dict[str, Set[str]] = {}  # 反向依赖
        self.component_types: Dict[str, ComponentType] = {}
        
    def add_component(self, component: str, component_type: ComponentType):
        """添加组件"""
        if component not in self.graph:
            self.graph[component] = set()
            self.reverse_graph[component] = set()
        self.component_types[component] = component_type
    
    def add_dependency(self, from_component: str, to_component: str):
        """添加依赖关系"""
        if from_component not in self.graph:
            self.add_component(from_component, ComponentType.BUSINESS_LOGIC)
        if to_component not in self.graph:
            self.add_component(to_component, ComponentType.BUSINESS_LOGIC)
            
        self.graph[from_component].add(to_component)
        self.reverse_graph[to_component].add(from_component)
    
    def get_dependencies(self, component: str) -> Set[str]:
        """获取组件的直接依赖"""
        return self.graph.get(component, set())
    
    def get_dependents(self, component: str) -> Set[str]:
        """获取依赖该组件的其他组件"""
        return self.reverse_graph.get(component, set())
    
    def get_all_dependencies(self, component: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """获取组件的所有依赖（包括传递依赖）"""
        if visited is None:
            visited = set()
            
        if component in visited:
            return set()
            
        visited.add(component)
        all_deps = set()
        
        direct_deps = self.get_dependencies(component)
        all_deps.update(direct_deps)
        
        for dep in direct_deps:
            all_deps.update(self.get_all_dependencies(dep, visited))
            
        return all_deps
    
    def get_all_dependents(self, component: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """获取所有依赖该组件的其他组件（包括传递依赖）"""
        if visited is None:
            visited = set()
            
        if component in visited:
            return set()
            
        visited.add(component)
        all_dependents = set()
        
        direct_dependents = self.get_dependents(component)
        all_dependents.update(direct_dependents)
        
        for dep in direct_dependents:
            all_dependents.update(self.get_all_dependents(dep, visited))
            
        return all_dependents
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """查找循环依赖"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path.copy()):
                        return True
                elif neighbor in rec_stack:
                    # 找到循环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            rec_stack.remove(node)
            return False
        
        for node in self.graph:
            if node not in visited:
                dfs(node, [])
                
        return cycles

class ImpactRules:
    """影响规则定义"""
    
    @staticmethod
    def get_rules() -> Dict[str, Dict[str, Any]]:
        """获取影响规则"""
        return {
            "data_model_change": {
                "description": "数据模型变更",
                "impacts": [
                    ComponentType.DATABASE,
                    ComponentType.API,
                    ComponentType.BACKEND,
                    ComponentType.TESTING
                ],
                "severity": ImpactSeverity.HIGH,
                "actions": [
                    "更新数据库schema",
                    "创建数据迁移脚本",
                    "更新ORM模型",
                    "更新API序列化器",
                    "更新单元测试"
                ]
            },
            "api_change": {
                "description": "API接口变更",
                "impacts": [
                    ComponentType.FRONTEND,
                    ComponentType.DOCUMENTATION,
                    ComponentType.TESTING,
                    ComponentType.DEPLOYMENT
                ],
                "severity": ImpactSeverity.HIGH,
                "actions": [
                    "更新前端调用",
                    "更新API文档",
                    "更新集成测试",
                    "考虑版本兼容性"
                ]
            },
            "business_logic_change": {
                "description": "业务逻辑变更",
                "impacts": [
                    ComponentType.BACKEND,
                    ComponentType.TESTING,
                    ComponentType.DOCUMENTATION
                ],
                "severity": ImpactSeverity.MEDIUM,
                "actions": [
                    "更新业务逻辑实现",
                    "更新单元测试",
                    "更新业务规则文档"
                ]
            },
            "ui_change": {
                "description": "界面变更",
                "impacts": [
                    ComponentType.FRONTEND,
                    ComponentType.UI_UX,
                    ComponentType.TESTING
                ],
                "severity": ImpactSeverity.LOW,
                "actions": [
                    "更新UI组件",
                    "更新样式",
                    "进行UI测试",
                    "更新截图文档"
                ]
            },
            "security_change": {
                "description": "安全相关变更",
                "impacts": [
                    ComponentType.SECURITY,
                    ComponentType.BACKEND,
                    ComponentType.INFRASTRUCTURE,
                    ComponentType.TESTING
                ],
                "severity": ImpactSeverity.CRITICAL,
                "actions": [
                    "安全审计",
                    "更新安全配置",
                    "进行渗透测试",
                    "更新安全文档"
                ]
            },
            "performance_optimization": {
                "description": "性能优化",
                "impacts": [
                    ComponentType.PERFORMANCE,
                    ComponentType.BACKEND,
                    ComponentType.DATABASE,
                    ComponentType.TESTING
                ],
                "severity": ImpactSeverity.MEDIUM,
                "actions": [
                    "性能测试",
                    "优化查询",
                    "添加缓存",
                    "更新性能基准"
                ]
            }
        }

class ChangeImpactAnalyzer:
    """变更影响分析器"""
    
    def __init__(self):
        self.dependency_graph = DependencyGraph()
        self.impact_rules = ImpactRules.get_rules()
        self._initialize_default_dependencies()
        
    def _initialize_default_dependencies(self):
        """初始化默认的依赖关系"""
        # 典型的分层架构依赖
        typical_dependencies = [
            ("frontend", "api"),
            ("api", "backend"),
            ("backend", "database"),
            ("backend", "security"),
            ("testing", "backend"),
            ("testing", "frontend"),
            ("documentation", "api"),
            ("deployment", "infrastructure")
        ]
        
        for from_comp, to_comp in typical_dependencies:
            self.dependency_graph.add_dependency(from_comp, to_comp)
    
    async def analyze_change_impact(
        self,
        change_type: str,
        affected_feature: str,
        change_details: Dict[str, Any],
        json_summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析变更影响"""
        logger.log(f"🔍 分析变更影响: {change_type} - {affected_feature}", level="info")
        
        # 1. 识别直接影响
        direct_impacts = self._identify_direct_impacts(
            change_type,
            affected_feature,
            change_details
        )
        
        # 2. 分析传递影响
        transitive_impacts = self._analyze_transitive_impacts(
            direct_impacts,
            affected_feature
        )
        
        # 3. 评估风险
        risk_assessment = self._assess_risks(
            change_type,
            direct_impacts + transitive_impacts,
            change_details
        )
        
        # 4. 生成重构计划
        refactoring_plan = self._generate_refactoring_plan(
            change_type,
            affected_feature,
            direct_impacts + transitive_impacts,
            change_details
        )
        
        # 5. 估算工作量
        effort_estimation = self._estimate_effort(
            direct_impacts + transitive_impacts,
            refactoring_plan
        )
        
        # 6. 如果提供了json_summary，进行更深入的分析
        if json_summary:
            specific_impacts = await self._analyze_specific_impacts(
                json_summary,
                change_type,
                affected_feature,
                change_details
            )
            direct_impacts.extend(specific_impacts)
        
        return {
            "change_summary": {
                "type": change_type,
                "feature": affected_feature,
                "details": change_details,
                "timestamp": datetime.now().isoformat()
            },
            "impact_analysis": {
                "direct_impacts": direct_impacts,
                "transitive_impacts": transitive_impacts,
                "total_affected_components": len(set(
                    impact.component for impact in direct_impacts + transitive_impacts
                )),
                "severity_distribution": self._get_severity_distribution(
                    direct_impacts + transitive_impacts
                )
            },
            "risk_assessment": risk_assessment,
            "refactoring_plan": refactoring_plan,
            "effort_estimation": effort_estimation,
            "recommendations": self._generate_recommendations(
                change_type,
                direct_impacts + transitive_impacts,
                risk_assessment
            )
        }
    
    def _identify_direct_impacts(
        self,
        change_type: str,
        affected_feature: str,
        change_details: Dict[str, Any]
    ) -> List[Impact]:
        """识别直接影响"""
        impacts = []
        
        # 基于规则的影响识别
        if change_type in self.impact_rules:
            rule = self.impact_rules[change_type]
            
            for component_type in rule["impacts"]:
                impact = Impact(
                    component=component_type.value,
                    component_type=component_type,
                    description=f"{rule['description']}影响{component_type.value}",
                    severity=rule["severity"],
                    action_required=self._get_action_for_component(
                        component_type,
                        rule["actions"]
                    ),
                    estimated_effort=self._estimate_component_effort(
                        component_type,
                        change_details
                    ),
                    dependencies=[]
                )
                impacts.append(impact)
        
        # 基于特征的影响识别
        feature_impacts = self._identify_feature_specific_impacts(
            affected_feature,
            change_details
        )
        impacts.extend(feature_impacts)
        
        return impacts
    
    def _identify_feature_specific_impacts(
        self,
        feature: str,
        change_details: Dict[str, Any]
    ) -> List[Impact]:
        """识别特定功能的影响"""
        impacts = []
        
        # 用户管理相关
        if any(keyword in feature.lower() for keyword in ["user", "用户", "auth", "认证"]):
            impacts.append(Impact(
                component="user_management",
                component_type=ComponentType.BACKEND,
                description="用户管理模块需要更新",
                severity=ImpactSeverity.HIGH,
                action_required="更新用户相关逻辑",
                estimated_effort="8小时",
                dependencies=["database", "api"]
            ))
        
        # 支付相关
        if any(keyword in feature.lower() for keyword in ["payment", "支付", "pay"]):
            impacts.append(Impact(
                component="payment_system",
                component_type=ComponentType.BACKEND,
                description="支付系统需要更新",
                severity=ImpactSeverity.CRITICAL,
                action_required="更新支付流程，确保事务安全",
                estimated_effort="16小时",
                dependencies=["security", "database", "third_party"]
            ))
        
        # 通知相关
        if any(keyword in feature.lower() for keyword in ["notification", "通知", "提醒"]):
            impacts.append(Impact(
                component="notification_service",
                component_type=ComponentType.BACKEND,
                description="通知服务需要更新",
                severity=ImpactSeverity.MEDIUM,
                action_required="更新通知逻辑和模板",
                estimated_effort="6小时",
                dependencies=["message_queue", "template_engine"]
            ))
        
        return impacts
    
    def _analyze_transitive_impacts(
        self,
        direct_impacts: List[Impact],
        affected_feature: str
    ) -> List[Impact]:
        """分析传递影响"""
        transitive_impacts = []
        analyzed_components = set()
        
        for impact in direct_impacts:
            component = impact.component
            
            # 获取依赖此组件的其他组件
            dependents = self.dependency_graph.get_all_dependents(component)
            
            for dependent in dependents:
                if dependent not in analyzed_components:
                    analyzed_components.add(dependent)
                    
                    transitive_impact = Impact(
                        component=dependent,
                        component_type=self.dependency_graph.component_types.get(
                            dependent,
                            ComponentType.BUSINESS_LOGIC
                        ),
                        description=f"由于{component}的变更，{dependent}需要相应调整",
                        severity=self._reduce_severity(impact.severity),
                        action_required=f"检查并更新{dependent}中与{component}的交互",
                        estimated_effort=self._estimate_transitive_effort(
                            impact.estimated_effort
                        ),
                        dependencies=[component]
                    )
                    transitive_impacts.append(transitive_impact)
        
        return transitive_impacts
    
    def _reduce_severity(self, severity: ImpactSeverity) -> ImpactSeverity:
        """降低传递影响的严重程度"""
        severity_reduction = {
            ImpactSeverity.CRITICAL: ImpactSeverity.HIGH,
            ImpactSeverity.HIGH: ImpactSeverity.MEDIUM,
            ImpactSeverity.MEDIUM: ImpactSeverity.LOW,
            ImpactSeverity.LOW: ImpactSeverity.LOW
        }
        return severity_reduction.get(severity, ImpactSeverity.LOW)
    
    def _assess_risks(
        self,
        change_type: str,
        impacts: List[Impact],
        change_details: Dict[str, Any]
    ) -> RiskAssessment:
        """评估风险"""
        risk_factors = []
        
        # 检查严重影响的数量
        critical_impacts = [i for i in impacts if i.severity == ImpactSeverity.CRITICAL]
        high_impacts = [i for i in impacts if i.severity == ImpactSeverity.HIGH]
        
        if len(critical_impacts) > 0:
            risk_factors.append(f"存在{len(critical_impacts)}个关键影响")
        if len(high_impacts) > 2:
            risk_factors.append(f"存在{len(high_impacts)}个高严重度影响")
        
        # 检查是否影响核心组件
        core_components = ["payment_system", "user_management", "security", "database"]
        affected_core = [
            i.component for i in impacts
            if i.component in core_components
        ]
        if affected_core:
            risk_factors.append(f"影响核心组件: {', '.join(affected_core)}")
        
        # 检查是否有循环依赖
        cycles = self.dependency_graph.find_circular_dependencies()
        if cycles:
            risk_factors.append(f"存在{len(cycles)}个循环依赖")
        
        # 确定风险等级
        if len(critical_impacts) > 0 or len(risk_factors) > 3:
            risk_level = "high"
        elif len(high_impacts) > 0 or len(risk_factors) > 1:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # 制定缓解策略
        mitigation_strategies = self._generate_mitigation_strategies(
            risk_level,
            risk_factors,
            change_type
        )
        
        # 制定回滚计划
        rollback_plan = self._generate_rollback_plan(
            change_type,
            impacts,
            risk_level
        )
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_factors=risk_factors,
            mitigation_strategies=mitigation_strategies,
            rollback_plan=rollback_plan
        )
    
    def _generate_mitigation_strategies(
        self,
        risk_level: str,
        risk_factors: List[str],
        change_type: str
    ) -> List[str]:
        """生成风险缓解策略"""
        strategies = []
        
        if risk_level == "high":
            strategies.extend([
                "进行全面的代码审查",
                "在测试环境进行完整测试",
                "准备详细的回滚方案",
                "分阶段部署，先小流量验证"
            ])
        elif risk_level == "medium":
            strategies.extend([
                "进行重点模块的代码审查",
                "增加自动化测试覆盖",
                "准备快速回滚脚本"
            ])
        
        # 特定风险的缓解策略
        if "循环依赖" in str(risk_factors):
            strategies.append("重构代码解决循环依赖")
        if "核心组件" in str(risk_factors):
            strategies.append("对核心组件进行压力测试")
        if "payment" in change_type.lower():
            strategies.append("进行支付流程的端到端测试")
        
        return strategies
    
    def _generate_rollback_plan(
        self,
        change_type: str,
        impacts: List[Impact],
        risk_level: str
    ) -> str:
        """生成回滚计划"""
        if risk_level == "high":
            return """
高风险回滚计划：
1. 保存当前版本的完整备份
2. 准备数据库回滚脚本
3. 使用特性开关，可快速关闭新功能
4. 保持旧版本服务运行，使用蓝绿部署
5. 监控关键指标，设置自动回滚触发器
"""
        elif risk_level == "medium":
            return """
中风险回滚计划：
1. 使用版本控制标记部署点
2. 准备快速回滚脚本
3. 保留前一版本的部署包
4. 监控错误率和性能指标
"""
        else:
            return """
低风险回滚计划：
1. 标准的Git回滚流程
2. 重新部署前一版本
3. 通知相关人员
"""
    
    def _generate_refactoring_plan(
        self,
        change_type: str,
        affected_feature: str,
        impacts: List[Impact],
        change_details: Dict[str, Any]
    ) -> RefactoringPlan:
        """生成重构计划"""
        immediate_actions = []
        short_term_actions = []
        long_term_actions = []
        
        # 根据影响生成行动项
        for impact in impacts:
            if impact.severity in [ImpactSeverity.CRITICAL, ImpactSeverity.HIGH]:
                immediate_actions.append({
                    "action": impact.action_required,
                    "component": impact.component,
                    "estimated_time": impact.estimated_effort,
                    "priority": "P0" if impact.severity == ImpactSeverity.CRITICAL else "P1"
                })
            elif impact.severity == ImpactSeverity.MEDIUM:
                short_term_actions.append({
                    "action": impact.action_required,
                    "component": impact.component,
                    "estimated_time": impact.estimated_effort,
                    "priority": "P2"
                })
            else:
                long_term_actions.append({
                    "action": impact.action_required,
                    "component": impact.component,
                    "estimated_time": impact.estimated_effort,
                    "priority": "P3"
                })
        
        # 添加通用的重构建议
        if change_type == "api_change":
            short_term_actions.append({
                "action": "更新API版本管理策略",
                "component": "api_gateway",
                "estimated_time": "4小时",
                "priority": "P2"
            })
        
        if len(impacts) > 10:
            long_term_actions.append({
                "action": "考虑模块化重构以降低耦合",
                "component": "architecture",
                "estimated_time": "2周",
                "priority": "P3"
            })
        
        # 计算总工作量
        total_hours = self._calculate_total_effort(
            immediate_actions + short_term_actions + long_term_actions
        )
        
        # 推荐方法
        if len(immediate_actions) > 3:
            recommended_approach = "建议采用分阶段实施，先处理关键影响"
        else:
            recommended_approach = "可以并行处理多个组件的更新"
        
        return RefactoringPlan(
            immediate_actions=immediate_actions,
            short_term_actions=short_term_actions,
            long_term_actions=long_term_actions,
            estimated_total_effort=f"{total_hours}小时",
            recommended_approach=recommended_approach
        )
    
    def _estimate_effort(
        self,
        impacts: List[Impact],
        refactoring_plan: RefactoringPlan
    ) -> Dict[str, Any]:
        """估算工作量"""
        # 从影响中提取工作量
        effort_by_component = {}
        for impact in impacts:
            component = impact.component
            hours = self._parse_effort_hours(impact.estimated_effort)
            effort_by_component[component] = effort_by_component.get(component, 0) + hours
        
        # 计算各阶段工作量
        immediate_hours = sum(
            self._parse_effort_hours(action["estimated_time"])
            for action in refactoring_plan.immediate_actions
        )
        short_term_hours = sum(
            self._parse_effort_hours(action["estimated_time"])
            for action in refactoring_plan.short_term_actions
        )
        long_term_hours = sum(
            self._parse_effort_hours(action["estimated_time"])
            for action in refactoring_plan.long_term_actions
        )
        
        total_hours = immediate_hours + short_term_hours + long_term_hours
        
        return {
            "total_effort_hours": total_hours,
            "effort_by_component": effort_by_component,
            "effort_by_phase": {
                "immediate": immediate_hours,
                "short_term": short_term_hours,
                "long_term": long_term_hours
            },
            "estimated_duration": self._estimate_duration(total_hours),
            "recommended_team_size": self._recommend_team_size(total_hours, immediate_hours)
        }
    
    def _parse_effort_hours(self, effort_str: str) -> int:
        """解析工作量字符串为小时数"""
        if "小时" in effort_str:
            return int(effort_str.replace("小时", "").strip())
        elif "天" in effort_str:
            days = int(effort_str.replace("天", "").strip())
            return days * 8
        elif "周" in effort_str:
            weeks = int(effort_str.replace("周", "").strip())
            return weeks * 40
        else:
            return 8  # 默认1天
    
    def _estimate_duration(self, total_hours: int) -> str:
        """估算项目持续时间"""
        if total_hours <= 40:
            return "1周内"
        elif total_hours <= 80:
            return "2周"
        elif total_hours <= 160:
            return "1个月"
        else:
            months = (total_hours + 159) // 160
            return f"{months}个月"
    
    def _recommend_team_size(self, total_hours: int, immediate_hours: int) -> int:
        """推荐团队规模"""
        if immediate_hours > 40:
            # 紧急工作多，需要更多人
            return max(3, total_hours // 80)
        else:
            # 正常情况
            return max(2, total_hours // 160)
    
    def _calculate_total_effort(self, actions: List[Dict[str, Any]]) -> int:
        """计算总工作量"""
        total = 0
        for action in actions:
            hours = self._parse_effort_hours(action["estimated_time"])
            total += hours
        return total
    
    def _get_action_for_component(
        self,
        component_type: ComponentType,
        actions: List[str]
    ) -> str:
        """获取组件的具体行动"""
        component_action_map = {
            ComponentType.DATABASE: "更新数据库schema",
            ComponentType.API: "更新API接口",
            ComponentType.FRONTEND: "更新前端调用",
            ComponentType.BACKEND: "更新后端逻辑",
            ComponentType.TESTING: "更新测试用例",
            ComponentType.DOCUMENTATION: "更新文档",
            ComponentType.SECURITY: "进行安全审计",
            ComponentType.PERFORMANCE: "进行性能测试"
        }
        
        default_action = component_action_map.get(component_type, "更新相关代码")
        
        # 查找更具体的行动
        for action in actions:
            if component_type.value.lower() in action.lower():
                return action
                
        return default_action
    
    def _estimate_component_effort(
        self,
        component_type: ComponentType,
        change_details: Dict[str, Any]
    ) -> str:
        """估算组件工作量"""
        # 基础工作量
        base_effort = {
            ComponentType.DATABASE: 8,
            ComponentType.API: 6,
            ComponentType.FRONTEND: 8,
            ComponentType.BACKEND: 10,
            ComponentType.TESTING: 6,
            ComponentType.DOCUMENTATION: 4,
            ComponentType.SECURITY: 12,
            ComponentType.PERFORMANCE: 8
        }
        
        hours = base_effort.get(component_type, 6)
        
        # 根据变更复杂度调整
        complexity = change_details.get("complexity", "medium")
        if complexity == "high":
            hours *= 1.5
        elif complexity == "low":
            hours *= 0.7
            
        return f"{int(hours)}小时"
    
    def _estimate_transitive_effort(self, direct_effort: str) -> str:
        """估算传递影响的工作量"""
        direct_hours = self._parse_effort_hours(direct_effort)
        transitive_hours = int(direct_hours * 0.3)  # 传递影响通常是直接影响的30%
        return f"{transitive_hours}小时"
    
    def _get_severity_distribution(self, impacts: List[Impact]) -> Dict[str, int]:
        """获取严重程度分布"""
        distribution = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for impact in impacts:
            distribution[impact.severity.value] += 1
            
        return distribution
    
    def _generate_recommendations(
        self,
        change_type: str,
        impacts: List[Impact],
        risk_assessment: RiskAssessment
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于风险级别的建议
        if risk_assessment.risk_level == "high":
            recommendations.extend([
                "建议进行架构评审会议",
                "考虑分阶段实施，降低风险",
                "准备详细的测试计划"
            ])
        
        # 基于影响范围的建议
        if len(impacts) > 15:
            recommendations.append("影响范围较大，建议考虑重构以降低模块耦合")
        
        # 基于组件类型的建议
        impacted_components = set(impact.component_type for impact in impacts)
        if ComponentType.SECURITY in impacted_components:
            recommendations.append("涉及安全组件，建议进行安全审计")
        if ComponentType.PERFORMANCE in impacted_components:
            recommendations.append("涉及性能，建议进行性能基准测试")
        if ComponentType.API in impacted_components:
            recommendations.append("API变更，注意版本兼容性")
        
        return recommendations
    
    async def _analyze_specific_impacts(
        self,
        json_summary: Dict[str, Any],
        change_type: str,
        affected_feature: str,
        change_details: Dict[str, Any]
    ) -> List[Impact]:
        """基于JSON摘要的具体影响分析"""
        specific_impacts = []
        
        # 分析功能需求的影响
        if "functional_requirements" in json_summary:
            features = json_summary["functional_requirements"].get("core_features", [])
            
            for feature in features:
                if feature.get("name") == affected_feature:
                    # 找到了被影响的功能
                    dependencies = feature.get("dependencies", [])
                    
                    for dep in dependencies:
                        specific_impacts.append(Impact(
                            component=dep,
                            component_type=ComponentType.BUSINESS_LOGIC,
                            description=f"{affected_feature}的变更影响依赖模块{dep}",
                            severity=ImpactSeverity.MEDIUM,
                            action_required=f"检查{dep}与{affected_feature}的交互",
                            estimated_effort="4小时",
                            dependencies=[affected_feature]
                        ))
        
        # 分析技术决策的影响
        if change_type == "technical_change" and "technical_decisions" in json_summary:
            tech = json_summary["technical_decisions"]
            
            if tech.get("database") and "database" in str(change_details):
                specific_impacts.append(Impact(
                    component="data_layer",
                    component_type=ComponentType.DATABASE,
                    description="数据库技术栈变更",
                    severity=ImpactSeverity.HIGH,
                    action_required="迁移数据和更新数据访问层",
                    estimated_effort="24小时",
                    dependencies=["all_services"]
                ))
        
        return specific_impacts
    
    def add_custom_dependency(self, from_component: str, to_component: str):
        """添加自定义依赖关系"""
        self.dependency_graph.add_dependency(from_component, to_component)
        logger.log(f"✅ 添加依赖: {from_component} -> {to_component}", level="info")
    
    def visualize_impact(self, impacts: List[Impact]) -> str:
        """可视化影响（文本形式）"""
        lines = ["影响关系图:", ""]
        
        # 按组件分组
        component_impacts = {}
        for impact in impacts:
            if impact.component not in component_impacts:
                component_impacts[impact.component] = []
            component_impacts[impact.component].append(impact)
        
        # 绘制影响
        for component, impacts_list in component_impacts.items():
            severity_symbols = {
                ImpactSeverity.CRITICAL: "🔴",
                ImpactSeverity.HIGH: "🟠",
                ImpactSeverity.MEDIUM: "🟡",
                ImpactSeverity.LOW: "🟢"
            }
            
            max_severity = max(i.severity for i in impacts_list)
            symbol = severity_symbols.get(max_severity, "⚪")
            
            lines.append(f"{symbol} {component}")
            for impact in impacts_list:
                lines.append(f"  └─ {impact.description}")
                if impact.dependencies:
                    lines.append(f"     依赖: {', '.join(impact.dependencies)}")
            lines.append("")
        
        return "\n".join(lines)

class ImpactAnalyzer:
    """影响分析器门面"""
    
    def __init__(self):
        self.change_impact_analyzer = ChangeImpactAnalyzer()
    
    async def analyze_requirement_change(
        self,
        change_request: Dict[str, Any],
        current_json_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析需求变更的影响"""
        change_type = self._infer_change_type(change_request)
        affected_feature = change_request.get("feature", "unknown")
        
        impact_analysis = await self.change_impact_analyzer.analyze_change_impact(
            change_type=change_type,
            affected_feature=affected_feature,
            change_details=change_request,
            json_summary=current_json_summary
        )
        
        return impact_analysis
    
    def _infer_change_type(self, change_request: Dict[str, Any]) -> str:
        """推断变更类型"""
        request_type = change_request.get("type", "").lower()
        
        if "data" in request_type or "model" in request_type:
            return "data_model_change"
        elif "api" in request_type:
            return "api_change"
        elif "business" in request_type or "logic" in request_type:
            return "business_logic_change"
        elif "ui" in request_type or "interface" in request_type:
            return "ui_change"
        elif "security" in request_type:
            return "security_change"
        elif "performance" in request_type:
            return "performance_optimization"
        else:
            return "general_change"
    
    def add_project_dependencies(self, dependencies: List[Tuple[str, str]]):
        """添加项目特定的依赖关系"""
        for from_comp, to_comp in dependencies:
            self.change_impact_analyzer.add_custom_dependency(from_comp, to_comp)
    
    def get_impact_summary(self, impact_analysis: Dict[str, Any]) -> str:
        """获取影响分析的文本摘要"""
        summary_parts = []
        
        # 变更摘要
        change = impact_analysis["change_summary"]
        summary_parts.append(
            f"变更类型: {change['type']}\n"
            f"影响功能: {change['feature']}\n"
        )
        
        # 影响统计
        impact_stats = impact_analysis["impact_analysis"]
        summary_parts.append(
            f"影响范围:\n"
            f"- 直接影响: {len(impact_stats['direct_impacts'])}个组件\n"
            f"- 传递影响: {len(impact_stats['transitive_impacts'])}个组件\n"
            f"- 严重程度分布: {impact_stats['severity_distribution']}\n"
        )
        
        # 风险评估
        risk = impact_analysis["risk_assessment"]
        summary_parts.append(
            f"风险级别: {risk.risk_level}\n"
            f"风险因素: {', '.join(risk.risk_factors[:3])}\n"
        )
        
        # 工作量估算
        effort = impact_analysis["effort_estimation"]
        summary_parts.append(
            f"预计工作量: {effort['total_effort_hours']}小时\n"
            f"预计工期: {effort['estimated_duration']}\n"
            f"建议团队规模: {effort['recommended_team_size']}人\n"
        )
        
        # 建议
        recommendations = impact_analysis["recommendations"]
        if recommendations:
            summary_parts.append(
                "建议:\n" + "\n".join(f"- {r}" for r in recommendations[:3])
            )
        
        return "\n".join(summary_parts)