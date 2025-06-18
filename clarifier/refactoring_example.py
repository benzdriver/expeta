"""
快速重构的实际例子
展示如何处理常见的需求变更场景
"""

from typing import Dict, List, Any
import json

class RefactoringScenarios:
    """常见重构场景示例"""
    
    @staticmethod
    async def scenario_add_new_feature():
        """场景1: 添加新功能"""
        # 原始需求
        original_summary = {
            "functional_requirements": {
                "core_features": [
                    {
                        "name": "客户管理",
                        "description": "管理客户基本信息"
                    },
                    {
                        "name": "文档管理",
                        "description": "上传和管理申请文档"
                    }
                ]
            }
        }
        
        # 用户请求：添加"自动提醒"功能
        change_request = {
            "type": "feature_addition",
            "feature": "自动提醒系统",
            "details": {
                "description": "自动提醒重要日期和待办事项",
                "sub_features": [
                    "邮件提醒",
                    "短信提醒",
                    "应用内通知"
                ],
                "trigger_rules": [
                    "文档过期前7天",
                    "面试前1天",
                    "补料截止前3天"
                ]
            }
        }
        
        # 系统分析影响
        impact_analysis = {
            "new_dependencies": [
                "需要集成邮件服务（如 SendGrid）",
                "需要集成短信服务（如 Twilio）",
                "需要实现定时任务系统"
            ],
            "affected_features": [
                "客户管理（需要添加通知偏好设置）",
                "文档管理（需要添加过期日期字段）"
            ],
            "required_changes": [
                {
                    "component": "数据模型",
                    "change": "添加 notifications 表",
                    "fields": ["type", "recipient", "content", "scheduled_at", "sent_at"]
                },
                {
                    "component": "后台服务",
                    "change": "添加定时任务服务",
                    "technology": "Celery + Redis"
                }
            ],
            "effort_estimate": {
                "development": "2周",
                "testing": "3天",
                "deployment": "1天"
            }
        }
        
        # 自动更新后的摘要
        updated_summary = {
            "functional_requirements": {
                "core_features": [
                    # ... 原有功能
                    {
                        "name": "自动提醒系统",
                        "description": "自动提醒重要日期和待办事项",
                        "priority": "must-have",
                        "sub_features": change_request["details"]["sub_features"],
                        "dependencies": ["客户管理", "文档管理"],
                        "technical_requirements": impact_analysis["new_dependencies"]
                    }
                ]
            },
            "non_functional_requirements": {
                "reliability": "提醒发送成功率 > 99%",
                "performance": "提醒延迟 < 5分钟"
            },
            "data_model_changes": impact_analysis["required_changes"]
        }
        
        return {
            "change_request": change_request,
            "impact_analysis": impact_analysis,
            "updated_summary": updated_summary
        }
    
    @staticmethod
    async def scenario_modify_business_rule():
        """场景2: 修改业务规则"""
        # 原始规则：顾问最多管理 100 个客户
        # 新规则：根据顾问级别设置不同限制
        
        change_request = {
            "type": "business_rule_modification",
            "feature": "客户管理",
            "old_rule": "每个顾问最多管理100个客户",
            "new_rule": {
                "junior_consultant": 50,
                "senior_consultant": 150,
                "partner": "unlimited"
            },
            "reason": "不同级别顾问能力不同"
        }
        
        # 影响分析
        impact_analysis = {
            "code_changes": [
                {
                    "file": "user_management",
                    "function": "validate_client_limit",
                    "change": "根据顾问级别动态判断"
                }
            ],
            "ui_changes": [
                {
                    "page": "顾问档案",
                    "change": "显示当前客户数/最大限制"
                },
                {
                    "page": "添加客户",
                    "change": "达到限制时显示升级提示"
                }
            ],
            "data_migration": {
                "required": True,
                "script": "add_consultant_level_field.sql"
            },
            "backward_compatibility": {
                "issue": "现有顾问需要分配级别",
                "solution": "默认设为 senior_consultant"
            }
        }
        
        return {
            "change_request": change_request,
            "impact_analysis": impact_analysis,
            "migration_plan": {
                "steps": [
                    "1. 添加顾问级别字段",
                    "2. 为现有顾问设置默认级别",
                    "3. 更新验证逻辑",
                    "4. 更新UI显示",
                    "5. 通知用户变更"
                ],
                "rollback_plan": "保留原验证逻辑开关，可快速回滚"
            }
        }
    
    @staticmethod
    async def scenario_performance_optimization():
        """场景3: 性能优化需求"""
        change_request = {
            "type": "performance_optimization",
            "issue": "文档列表加载缓慢",
            "current_performance": "加载100个文档需要5秒",
            "target_performance": "加载100个文档小于1秒",
            "user_feedback": "用户抱怨等待时间过长"
        }
        
        # 分析和解决方案
        optimization_plan = {
            "root_cause_analysis": [
                "每个文档都单独查询数据库",
                "文档包含大量不必要的字段",
                "没有使用缓存"
            ],
            "solutions": [
                {
                    "approach": "批量查询优化",
                    "implementation": "使用 SQL JOIN 替代 N+1 查询",
                    "expected_improvement": "60%"
                },
                {
                    "approach": "字段精简",
                    "implementation": "列表只返回必要字段，详情再加载全部",
                    "expected_improvement": "20%"
                },
                {
                    "approach": "添加缓存层",
                    "implementation": "Redis 缓存常用查询",
                    "expected_improvement": "15%"
                }
            ],
            "implementation_order": [
                "先优化查询（快速见效）",
                "再添加缓存（长期收益）",
                "最后精简字段（需要前端配合）"
            ],
            "no_functional_change": True,
            "risk": "low"
        }
        
        # 更新非功能需求
        updated_requirements = {
            "performance": {
                "document_list_load": "<1s for 100 items",
                "document_search": "<500ms",
                "document_upload": "<10s for 10MB file"
            },
            "scalability": {
                "concurrent_users": "1000+",
                "total_documents": "1M+"
            }
        }
        
        return {
            "change_request": change_request,
            "optimization_plan": optimization_plan,
            "updated_requirements": updated_requirements
        }
    
    @staticmethod
    async def scenario_compliance_requirement():
        """场景4: 新的合规要求"""
        change_request = {
            "type": "compliance_requirement",
            "regulation": "GDPR",
            "requirements": [
                "用户数据可导出",
                "用户可请求删除数据",
                "数据处理需要明确同意",
                "数据泄露72小时内通知"
            ],
            "deadline": "2024-06-01"
        }
        
        compliance_plan = {
            "new_features": [
                {
                    "name": "数据导出功能",
                    "description": "用户可下载所有个人数据",
                    "format": "JSON/PDF",
                    "scope": "所有用户数据表"
                },
                {
                    "name": "数据删除请求",
                    "description": "软删除 + 30天后硬删除",
                    "includes": "级联删除相关数据"
                },
                {
                    "name": "同意管理",
                    "description": "记录用户同意历史",
                    "ui_changes": "添加同意复选框"
                }
            ],
            "technical_changes": [
                "添加审计日志表",
                "实现数据加密",
                "添加数据生命周期管理"
            ],
            "process_changes": [
                "制定数据泄露响应流程",
                "指定数据保护官",
                "员工GDPR培训"
            ],
            "impact_on_existing": {
                "user_registration": "需要添加隐私政策同意",
                "data_storage": "需要加密敏感字段",
                "third_party_integration": "需要审查数据共享协议"
            }
        }
        
        return {
            "change_request": change_request,
            "compliance_plan": compliance_plan,
            "priority": "critical",
            "estimated_effort": "4-6周"
        }

class IncrementalRefactoring:
    """增量重构策略"""
    
    @staticmethod
    def generate_refactoring_steps(
        change_type: str,
        scope: str,
        current_state: Dict,
        target_state: Dict
    ) -> List[Dict[str, Any]]:
        """生成增量重构步骤"""
        
        if change_type == "feature_addition":
            return [
                {
                    "step": 1,
                    "action": "创建功能分支",
                    "command": "git checkout -b feature/new-feature"
                },
                {
                    "step": 2,
                    "action": "更新数据模型",
                    "files": ["models/", "migrations/"],
                    "validation": "运行数据库迁移测试"
                },
                {
                    "step": 3,
                    "action": "实现后端API",
                    "files": ["api/", "services/"],
                    "validation": "API单元测试通过"
                },
                {
                    "step": 4,
                    "action": "更新前端界面",
                    "files": ["components/", "pages/"],
                    "validation": "UI测试通过"
                },
                {
                    "step": 5,
                    "action": "更新文档",
                    "files": ["docs/api.md", "docs/user-guide.md"],
                    "validation": "文档审查"
                },
                {
                    "step": 6,
                    "action": "集成测试",
                    "validation": "端到端测试通过"
                },
                {
                    "step": 7,
                    "action": "部署到测试环境",
                    "validation": "QA验收"
                }
            ]
        
        elif change_type == "business_rule_modification":
            return [
                {
                    "step": 1,
                    "action": "识别受影响的代码",
                    "tool": "grep -r 'old_rule' .",
                    "expected_files": ["services/validation.py", "tests/"]
                },
                {
                    "step": 2,
                    "action": "创建特性开关",
                    "purpose": "支持新旧规则并存",
                    "code": "if feature_flag('new_business_rule'):"
                },
                {
                    "step": 3,
                    "action": "实现新规则",
                    "parallel": True,
                    "validation": "新规则单元测试"
                },
                {
                    "step": 4,
                    "action": "数据迁移脚本",
                    "script": "migrate_business_rules.py",
                    "dry_run": True
                },
                {
                    "step": 5,
                    "action": "灰度发布",
                    "percentage": "10% -> 50% -> 100%",
                    "monitoring": "监控错误率和性能"
                }
            ]
        
        return []
    
    @staticmethod
    def estimate_change_effort(
        change_request: Dict[str, Any],
        codebase_metrics: Dict[str, int]
    ) -> Dict[str, Any]:
        """估算变更工作量"""
        
        # 基础工作量因子
        base_effort = {
            "feature_addition": 40,  # 人时
            "feature_modification": 24,
            "feature_removal": 16,
            "business_rule_modification": 32,
            "performance_optimization": 48,
            "compliance_requirement": 80
        }
        
        # 复杂度因子
        complexity_factors = {
            "affected_modules": len(change_request.get("affected_modules", [])) * 0.2,
            "data_migration": 0.3 if change_request.get("requires_migration") else 0,
            "third_party_integration": 0.4 if change_request.get("external_deps") else 0,
            "ui_changes": 0.3 if change_request.get("ui_impact") else 0,
            "backward_compatibility": 0.2 if change_request.get("breaking_change") else 0
        }
        
        # 计算总工作量
        change_type = change_request.get("type", "feature_modification")
        base = base_effort.get(change_type, 40)
        
        complexity_multiplier = 1 + sum(complexity_factors.values())
        total_effort = base * complexity_multiplier
        
        # 分解工作量
        effort_breakdown = {
            "analysis": total_effort * 0.15,
            "development": total_effort * 0.40,
            "testing": total_effort * 0.25,
            "documentation": total_effort * 0.10,
            "deployment": total_effort * 0.10
        }
        
        return {
            "total_hours": round(total_effort),
            "breakdown": effort_breakdown,
            "factors": complexity_factors,
            "confidence": "high" if complexity_multiplier < 1.5 else "medium",
            "risks": [
                "未知的技术债务" if codebase_metrics.get("tech_debt", 0) > 50 else None,
                "第三方API变更" if change_request.get("external_deps") else None,
                "数据迁移风险" if change_request.get("requires_migration") else None
            ]
        }

# 使用示例
async def demonstrate_quick_refactoring():
    """演示快速重构"""
    
    # 1. 添加新功能
    print("=== 场景1: 添加自动提醒功能 ===")
    result1 = await RefactoringScenarios.scenario_add_new_feature()
    print(f"影响分析: {json.dumps(result1['impact_analysis'], indent=2, ensure_ascii=False)}")
    
    # 2. 修改业务规则
    print("\n=== 场景2: 修改客户数量限制规则 ===")
    result2 = await RefactoringScenarios.scenario_modify_business_rule()
    print(f"迁移计划: {json.dumps(result2['migration_plan'], indent=2, ensure_ascii=False)}")
    
    # 3. 性能优化
    print("\n=== 场景3: 优化文档加载性能 ===")
    result3 = await RefactoringScenarios.scenario_performance_optimization()
    print(f"优化方案: {json.dumps(result3['optimization_plan'], indent=2, ensure_ascii=False)}")
    
    # 4. 合规要求
    print("\n=== 场景4: 实施GDPR合规 ===")
    result4 = await RefactoringScenarios.scenario_compliance_requirement()
    print(f"合规计划: {json.dumps(result4['compliance_plan'], indent=2, ensure_ascii=False)}")
    
    # 5. 估算工作量
    print("\n=== 工作量估算 ===")
    effort = IncrementalRefactoring.estimate_change_effort(
        result1["change_request"],
        {"tech_debt": 30, "code_coverage": 75}
    )
    print(f"预计工作量: {effort['total_hours']} 小时")
    print(f"工作分解: {json.dumps(effort['breakdown'], indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(demonstrate_quick_refactoring())