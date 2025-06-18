"""
Clarifier系统编排器 - 整合所有组件
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json
from datetime import datetime
import asyncio

from llm_services.executor import run_prompt
from common.logger import Logger

logger = Logger.get_instance('clarifier')

from .blind_spot_detector import BlindSpotDetector, BlindSpot
from .version_manager import VersionManager, ChangeType
from .impact_analyzer import ImpactAnalyzer
from .refactoring_engine import SmartRefactoring, RefactoringStrategy

class ClarifierMode(Enum):
    """Clarifier工作模式"""
    INTERACTIVE = "interactive"  # 交互式澄清
    PRD_ANALYSIS = "prd_analysis"  # PRD分析增强
    QUICK_CHECK = "quick_check"  # 快速检查
    FULL_ANALYSIS = "full_analysis"  # 全面分析

@dataclass
class ClarificationRequest:
    """澄清请求"""
    blind_spot_id: str
    user_response: str
    additional_context: Optional[Dict[str, Any]] = None

@dataclass
class ClarifierSession:
    """Clarifier会话"""
    session_id: str
    mode: ClarifierMode
    created_at: str
    current_version_id: str
    blind_spots_addressed: List[str]
    pending_blind_spots: List[str]
    interaction_history: List[Dict[str, Any]]

class ClarifierOrchestrator:
    """Clarifier系统编排器"""
    
    def __init__(self):
        # 初始化所有组件
        self.blind_spot_detector = BlindSpotDetector()
        self.version_manager = VersionManager()
        self.impact_analyzer = ImpactAnalyzer()
        self.refactoring_engine = SmartRefactoring(
            self.version_manager.requirement_version,
            self.impact_analyzer
        )
        
        # 会话管理
        self.active_sessions: Dict[str, ClarifierSession] = {}
        
    async def start_clarification_session(
        self,
        prd_content: str,
        initial_summary: Optional[Dict[str, Any]] = None,
        mode: ClarifierMode = ClarifierMode.INTERACTIVE,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """启动澄清会话"""
        logger.log(f"🚀 启动Clarifier会话 - 模式: {mode.value}", level="info")
        
        # 生成会话ID
        session_id = f"CS_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 如果没有提供初始摘要，生成一个基础版本
        if not initial_summary:
            initial_summary = await self._generate_initial_summary(prd_content)
        
        # 初始化版本管理
        version_id = self.version_manager.initialize_with_prd(
            prd_content, 
            initial_summary
        )
        
        # 检测盲点
        blind_spots = await self.blind_spot_detector.detect_blind_spots(
            prd_content,
            context
        )
        
        # 创建会话
        session = ClarifierSession(
            session_id=session_id,
            mode=mode,
            created_at=datetime.now().isoformat(),
            current_version_id=version_id,
            blind_spots_addressed=[],
            pending_blind_spots=[bs.id for bs in blind_spots],
            interaction_history=[]
        )
        
        self.active_sessions[session_id] = session
        
        # 根据模式决定下一步
        if mode == ClarifierMode.INTERACTIVE:
            # 返回第一个需要澄清的盲点
            next_action = self._prepare_next_clarification(session, blind_spots)
        elif mode == ClarifierMode.PRD_ANALYSIS:
            # 自动分析并增强PRD
            enhanced_result = await self._auto_enhance_prd(
                session, 
                prd_content, 
                initial_summary, 
                blind_spots
            )
            next_action = enhanced_result
        else:
            # 快速检查或全面分析模式
            analysis_result = self._analyze_blind_spots(blind_spots)
            next_action = analysis_result
        
        return session_id, {
            "session_id": session_id,
            "mode": mode.value,
            "initial_version": version_id,
            "total_blind_spots": len(blind_spots),
            "blind_spots_summary": self.blind_spot_detector.get_detection_summary(),
            "next_action": next_action
        }
    
    async def process_clarification(
        self,
        session_id: str,
        clarification: ClarificationRequest
    ) -> Dict[str, Any]:
        """处理用户的澄清响应"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话 {session_id} 不存在")
        
        session = self.active_sessions[session_id]
        logger.log(f"📝 处理盲点澄清: {clarification.blind_spot_id}", level="info")
        
        # 获取当前版本
        current_version = self.version_manager.requirement_version.get_current_version()
        if not current_version:
            raise ValueError("无法获取当前版本")
        
        # 更新PRD和摘要
        updated_prd, updated_summary = await self._apply_clarification(
            current_version.prd_content,
            current_version.json_summary,
            clarification
        )
        
        # 创建新版本
        new_version_id = self.version_manager.save_blind_spot_clarification(
            updated_prd,
            updated_summary,
            clarification.blind_spot_id,
            clarification.user_response
        )
        
        # 更新会话状态
        session.current_version_id = new_version_id
        session.blind_spots_addressed.append(clarification.blind_spot_id)
        session.pending_blind_spots.remove(clarification.blind_spot_id)
        
        # 记录交互历史
        session.interaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "blind_spot_id": clarification.blind_spot_id,
            "user_response": clarification.user_response,
            "version_created": new_version_id
        })
        
        # 检查是否还有待处理的盲点
        if session.pending_blind_spots:
            # 获取下一个盲点
            remaining_blind_spots = [
                bs for bs in self.blind_spot_detector.detected_blind_spots
                if bs.id in session.pending_blind_spots
            ]
            next_action = self._prepare_next_clarification(session, remaining_blind_spots)
        else:
            # 所有盲点已处理
            next_action = {
                "type": "completion",
                "message": "所有盲点已澄清完成",
                "final_version": new_version_id,
                "total_clarifications": len(session.blind_spots_addressed)
            }
        
        return {
            "status": "processed",
            "new_version": new_version_id,
            "blind_spots_remaining": len(session.pending_blind_spots),
            "next_action": next_action
        }
    
    async def handle_requirement_change(
        self,
        change_request: Dict[str, Any],
        auto_execute: bool = False
    ) -> Dict[str, Any]:
        """处理需求变更"""
        logger.log(f"🔄 处理需求变更请求", level="info")
        
        # 获取当前版本
        current_version = self.version_manager.requirement_version.get_current_version()
        if not current_version:
            raise ValueError("没有当前版本，请先初始化")
        
        # 使用重构引擎处理变更
        result = await self.refactoring_engine.handle_requirement_change(
            current_version.prd_content,
            current_version.json_summary,
            change_request,
            auto_execute
        )
        
        return result
    
    async def execute_refactoring(
        self,
        refactoring_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行重构计划"""
        logger.log(f"⚡ 执行重构计划", level="info")
        
        # 获取当前版本
        current_version = self.version_manager.requirement_version.get_current_version()
        if not current_version:
            raise ValueError("没有当前版本")
        
        # 执行重构
        result = await self.refactoring_engine._execute_refactoring(
            refactoring_plan,
            current_version.prd_content,
            current_version.json_summary
        )
        
        if result.success:
            # 保存新版本
            new_version_id = self.version_manager.save_requirement_change(
                result.updated_prd,
                result.updated_json_summary,
                refactoring_plan["change_request"]
            )
            result.new_version_id = new_version_id
        
        return {
            "success": result.success,
            "version_id": result.new_version_id if result.success else None,
            "changes_made": result.changes_made,
            "validation_results": result.validation_results
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """获取会话状态"""
        if session_id not in self.active_sessions:
            return {"error": f"会话 {session_id} 不存在"}
        
        session = self.active_sessions[session_id]
        current_version = self.version_manager.requirement_version.get_version(
            session.current_version_id
        )
        
        return {
            "session_id": session_id,
            "mode": session.mode.value,
            "created_at": session.created_at,
            "current_version": {
                "id": current_version.id,
                "number": current_version.version_number
            } if current_version else None,
            "progress": {
                "total_blind_spots": len(session.blind_spots_addressed) + len(session.pending_blind_spots),
                "addressed": len(session.blind_spots_addressed),
                "pending": len(session.pending_blind_spots)
            },
            "interaction_count": len(session.interaction_history)
        }
    
    def get_version_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取版本历史"""
        versions = self.version_manager.requirement_version.get_version_history(limit)
        
        return [{
            "id": v.id,
            "number": v.version_number,
            "created_at": v.created_at,
            "created_by": v.created_by,
            "change_summary": v.change_summary,
            "metadata": v.metadata
        } for v in versions]
    
    def export_session_report(
        self, 
        session_id: str, 
        format: str = "markdown"
    ) -> str:
        """导出会话报告"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话 {session_id} 不存在")
        
        session = self.active_sessions[session_id]
        
        if format == "markdown":
            return self._export_session_as_markdown(session)
        elif format == "json":
            return self._export_session_as_json(session)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    # 私有辅助方法
    
    async def _generate_initial_summary(self, prd_content: str) -> Dict[str, Any]:
        """生成初始摘要"""
        prompt = f"""
        分析以下PRD文档，生成结构化的JSON摘要。
        
        PRD内容：
        {prd_content[:2000]}
        
        请生成包含以下字段的JSON：
        - project_name: 项目名称
        - description: 项目描述
        - features: 主要功能列表
        - users: 目标用户
        - technical_requirements: 技术要求
        - constraints: 约束条件
        """
        
        response = await run_prompt(
            system_message="你是一个产品需求分析专家",
            user_message=prompt,
            temperature=0.3
        )
        
        try:
            return json.loads(response)
        except:
            # 返回基础结构
            return {
                "project_name": "未命名项目",
                "description": "待完善",
                "features": [],
                "users": [],
                "technical_requirements": {},
                "constraints": []
            }
    
    def _prepare_next_clarification(
        self, 
        session: ClarifierSession, 
        blind_spots: List[BlindSpot]
    ) -> Dict[str, Any]:
        """准备下一个需要澄清的盲点"""
        if not blind_spots:
            return {
                "type": "completion",
                "message": "没有更多盲点需要澄清"
            }
        
        # 获取优先级最高的盲点
        next_blind_spot = blind_spots[0]
        
        return {
            "type": "clarification_needed",
            "blind_spot": {
                "id": next_blind_spot.id,
                "title": next_blind_spot.title,
                "description": next_blind_spot.description,
                "context": next_blind_spot.context,
                "questions": next_blind_spot.questions,
                "suggestions": next_blind_spot.suggestions,
                "severity": next_blind_spot.severity
            },
            "prompt": self._generate_clarification_prompt(next_blind_spot)
        }
    
    def _generate_clarification_prompt(self, blind_spot: BlindSpot) -> str:
        """生成澄清提示"""
        prompt_parts = [
            f"关于【{blind_spot.title}】，我们需要澄清以下内容：",
            "",
            blind_spot.description,
            "",
            "请回答以下问题："
        ]
        
        for i, question in enumerate(blind_spot.questions, 1):
            prompt_parts.append(f"{i}. {question}")
        
        if blind_spot.suggestions:
            prompt_parts.extend([
                "",
                "建议考虑："
            ])
            for suggestion in blind_spot.suggestions[:3]:
                prompt_parts.append(f"- {suggestion}")
        
        return "\n".join(prompt_parts)
    
    async def _auto_enhance_prd(
        self,
        session: ClarifierSession,
        prd_content: str,
        initial_summary: Dict[str, Any],
        blind_spots: List[BlindSpot]
    ) -> Dict[str, Any]:
        """自动增强PRD"""
        logger.log(f"🤖 自动增强PRD - 发现 {len(blind_spots)} 个盲点", level="info")
        
        enhanced_prd = prd_content
        enhanced_summary = initial_summary.copy()
        
        # 批量处理盲点
        for blind_spot in blind_spots[:10]:  # 限制处理数量
            # 生成自动回答
            auto_response = await self._generate_auto_clarification(
                blind_spot,
                enhanced_prd
            )
            
            # 应用澄清
            clarification = ClarificationRequest(
                blind_spot_id=blind_spot.id,
                user_response=auto_response,
                additional_context={"auto_generated": True}
            )
            
            enhanced_prd, enhanced_summary = await self._apply_clarification(
                enhanced_prd,
                enhanced_summary,
                clarification
            )
            
            # 更新会话状态
            session.blind_spots_addressed.append(blind_spot.id)
            session.pending_blind_spots.remove(blind_spot.id)
        
        # 创建增强版本
        enhanced_version_id = self.version_manager.save_blind_spot_clarification(
            enhanced_prd,
            enhanced_summary,
            "auto_enhancement",
            f"自动增强PRD - 处理了 {len(session.blind_spots_addressed)} 个盲点"
        )
        
        return {
            "type": "auto_enhanced",
            "enhanced_version": enhanced_version_id,
            "blind_spots_addressed": len(session.blind_spots_addressed),
            "blind_spots_remaining": len(session.pending_blind_spots),
            "enhanced_prd": enhanced_prd[:500] + "...",  # 预览
            "enhancement_summary": self._generate_enhancement_summary(
                session.blind_spots_addressed,
                blind_spots
            )
        }
    
    async def _generate_auto_clarification(
        self, 
        blind_spot: BlindSpot,
        prd_content: str
    ) -> str:
        """生成自动澄清内容"""
        prompt = f"""
        基于以下PRD内容和检测到的盲点，生成合理的澄清内容。
        
        盲点：{blind_spot.title}
        描述：{blind_spot.description}
        
        需要回答的问题：
        {chr(10).join(f"- {q}" for q in blind_spot.questions)}
        
        PRD相关内容：
        {blind_spot.context}
        
        请生成专业、具体的回答，避免模糊表述。
        """
        
        response = await run_prompt(
            system_message="你是一个经验丰富的产品经理，擅长补充需求细节",
            user_message=prompt,
            temperature=0.5
        )
        
        return response
    
    async def _apply_clarification(
        self,
        prd_content: str,
        json_summary: Dict[str, Any],
        clarification: ClarificationRequest
    ) -> Tuple[str, Dict[str, Any]]:
        """应用澄清到PRD和摘要"""
        # 查找对应的盲点
        blind_spot = next(
            (bs for bs in self.blind_spot_detector.detected_blind_spots 
             if bs.id == clarification.blind_spot_id),
            None
        )
        
        if not blind_spot:
            return prd_content, json_summary
        
        # 更新PRD内容
        updated_prd = await self._update_prd_with_clarification(
            prd_content,
            blind_spot,
            clarification.user_response
        )
        
        # 更新JSON摘要
        updated_summary = await self._update_summary_with_clarification(
            json_summary,
            blind_spot,
            clarification.user_response
        )
        
        return updated_prd, updated_summary
    
    async def _update_prd_with_clarification(
        self,
        prd_content: str,
        blind_spot: BlindSpot,
        clarification: str
    ) -> str:
        """更新PRD内容"""
        prompt = f"""
        更新PRD文档，加入以下澄清内容：
        
        原始PRD片段：
        {blind_spot.context}
        
        盲点类型：{blind_spot.title}
        澄清内容：{clarification}
        
        请返回更新后的PRD片段，保持原有格式和风格。
        """
        
        response = await run_prompt(
            system_message="你是一个PRD文档编辑专家",
            user_message=prompt,
            temperature=0.3
        )
        
        # 简单替换策略（实际应该更智能）
        if blind_spot.context in prd_content:
            return prd_content.replace(blind_spot.context, response)
        else:
            # 添加到相关部分
            return prd_content + f"\n\n## {blind_spot.title}\n{response}"
    
    async def _update_summary_with_clarification(
        self,
        json_summary: Dict[str, Any],
        blind_spot: BlindSpot,
        clarification: str
    ) -> Dict[str, Any]:
        """更新JSON摘要"""
        updated_summary = json_summary.copy()
        
        # 根据盲点类型更新相应字段
        if blind_spot.type.value == "security":
            if "security_requirements" not in updated_summary:
                updated_summary["security_requirements"] = {}
            updated_summary["security_requirements"][blind_spot.title] = clarification
        
        elif blind_spot.type.value == "scalability":
            if "scalability_requirements" not in updated_summary:
                updated_summary["scalability_requirements"] = {}
            updated_summary["scalability_requirements"][blind_spot.title] = clarification
        
        elif blind_spot.type.value == "error_handling":
            if "error_handling" not in updated_summary:
                updated_summary["error_handling"] = {}
            updated_summary["error_handling"][blind_spot.title] = clarification
        
        else:
            # 通用处理
            if "clarifications" not in updated_summary:
                updated_summary["clarifications"] = {}
            updated_summary["clarifications"][blind_spot.id] = {
                "type": blind_spot.type.value,
                "title": blind_spot.title,
                "clarification": clarification
            }
        
        return updated_summary
    
    def _analyze_blind_spots(self, blind_spots: List[BlindSpot]) -> Dict[str, Any]:
        """分析盲点"""
        return {
            "type": "analysis",
            "total_blind_spots": len(blind_spots),
            "by_severity": self.blind_spot_detector._get_severity_distribution(blind_spots),
            "by_type": self.blind_spot_detector._get_type_distribution(blind_spots),
            "critical_items": [
                {
                    "id": bs.id,
                    "title": bs.title,
                    "description": bs.description,
                    "top_questions": bs.questions[:3]
                }
                for bs in blind_spots
                if bs.severity in ["critical", "high"]
            ][:5]
        }
    
    def _generate_enhancement_summary(
        self,
        addressed_ids: List[str],
        all_blind_spots: List[BlindSpot]
    ) -> Dict[str, Any]:
        """生成增强摘要"""
        addressed_blind_spots = [
            bs for bs in all_blind_spots
            if bs.id in addressed_ids
        ]
        
        return {
            "enhancements_made": len(addressed_ids),
            "by_type": self.blind_spot_detector._get_type_distribution(addressed_blind_spots),
            "key_improvements": [
                f"增强了{bs.title}相关的需求描述"
                for bs in addressed_blind_spots[:5]
            ]
        }
    
    def _export_session_as_markdown(self, session: ClarifierSession) -> str:
        """导出会话为Markdown"""
        lines = [
            f"# Clarifier会话报告",
            f"",
            f"**会话ID**: {session.session_id}",
            f"**模式**: {session.mode.value}",
            f"**创建时间**: {session.created_at}",
            f"",
            f"## 进度",
            f"- 总盲点数: {len(session.blind_spots_addressed) + len(session.pending_blind_spots)}",
            f"- 已处理: {len(session.blind_spots_addressed)}",
            f"- 待处理: {len(session.pending_blind_spots)}",
            f"",
            f"## 交互历史",
            f""
        ]
        
        for interaction in session.interaction_history:
            lines.extend([
                f"### {interaction['timestamp']}",
                f"- 盲点ID: {interaction['blind_spot_id']}",
                f"- 用户响应: {interaction['user_response'][:100]}...",
                f"- 创建版本: {interaction['version_created']}",
                f""
            ])
        
        return "\n".join(lines)
    
    def _export_session_as_json(self, session: ClarifierSession) -> str:
        """导出会话为JSON"""
        return json.dumps({
            "session_id": session.session_id,
            "mode": session.mode.value,
            "created_at": session.created_at,
            "current_version_id": session.current_version_id,
            "progress": {
                "total": len(session.blind_spots_addressed) + len(session.pending_blind_spots),
                "addressed": len(session.blind_spots_addressed),
                "pending": len(session.pending_blind_spots)
            },
            "blind_spots_addressed": session.blind_spots_addressed,
            "interaction_history": session.interaction_history
        }, ensure_ascii=False, indent=2)

    async def generate_structured_summary(
        self,
        prd_content: str,
        version_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成最终的结构化JSON摘要"""
        logger.log("📋 生成结构化JSON摘要", level="info")
        
        # 获取指定版本或当前版本
        if version_id:
            version = self.version_manager.requirement_version.get_version(version_id)
        else:
            version = self.version_manager.requirement_version.get_current_version()
        
        if not version:
            raise ValueError("无法获取版本信息")
        
        # 使用改进后的提示词生成具体的摘要
        prompt = f"""
        基于以下PRD内容生成详细、具体的技术架构JSON摘要。

        PRD内容：
        {version.prd_content}

        已有的澄清信息：
        {json.dumps(version.json_summary.get('clarifications', {}), ensure_ascii=False)}

        要求：
        1. 所有描述必须具体、可执行
        2. 避免使用模糊词汇（处理、管理、相关、合适的等）
        3. 包含具体的技术选型、数据结构、API设计
        4. 每个功能模块都要有明确的输入输出
        5. 包含具体的错误处理和边界条件

        生成以下结构的JSON：
        {{
            "project_info": {{
                "name": "具体项目名称",
                "version": "1.0.0",
                "description": "具体的项目描述"
            }},
            "technical_architecture": {{
                "frontend": {{
                    "framework": "具体框架名称和版本",
                    "ui_library": "具体UI库",
                    "state_management": "具体状态管理方案",
                    "routing": "具体路由方案"
                }},
                "backend": {{
                    "framework": "具体框架名称和版本",
                    "database": "具体数据库和版本",
                    "cache": "具体缓存方案",
                    "message_queue": "具体消息队列"
                }},
                "deployment": {{
                    "platform": "具体部署平台",
                    "container": "具体容器化方案",
                    "ci_cd": "具体CI/CD工具"
                }}
            }},
            "functional_modules": [
                {{
                    "name": "具体模块名称",
                    "description": "模块的具体功能",
                    "apis": [
                        {{
                            "endpoint": "/api/v1/specific-endpoint",
                            "method": "POST",
                            "request_body": {{"field": "type"}},
                            "response": {{"field": "type"}},
                            "error_codes": ["400", "401", "500"]
                        }}
                    ],
                    "database_tables": [
                        {{
                            "name": "specific_table",
                            "fields": [
                                {{"name": "id", "type": "bigint", "constraints": "primary key"}},
                                {{"name": "field_name", "type": "varchar(255)", "constraints": "not null"}}
                            ]
                        }}
                    ],
                    "business_rules": [
                        "具体的业务规则1",
                        "具体的业务规则2"
                    ]
                }}
            ],
            "non_functional_requirements": {{
                "performance": {{
                    "response_time": "< 200ms for 95% requests",
                    "concurrent_users": "10000",
                    "throughput": "1000 TPS"
                }},
                "security": {{
                    "authentication": "JWT with 2FA",
                    "encryption": "AES-256 for data at rest, TLS 1.3 for data in transit",
                    "compliance": ["GDPR", "SOC2"]
                }},
                "scalability": {{
                    "horizontal_scaling": "Auto-scaling with Kubernetes",
                    "database_sharding": "Hash-based sharding by user_id",
                    "caching_strategy": "Redis with 5 minute TTL"
                }}
            }},
            "error_handling": {{
                "client_errors": [
                    {{
                        "code": "AUTH_001",
                        "message": "Invalid credentials",
                        "action": "Redirect to login page"
                    }}
                ],
                "server_errors": [
                    {{
                        "code": "SRV_001", 
                        "message": "Database connection failed",
                        "action": "Retry with exponential backoff"
                    }}
                ]
            }},
            "integration_points": [
                {{
                    "service": "Payment Gateway",
                    "provider": "Stripe",
                    "api_version": "2023-10-16",
                    "timeout": "30s",
                    "retry_policy": "3 retries with exponential backoff"
                }}
            ]
        }}
        """
        
        response = await run_prompt(
            system_message="你是一个技术架构师，擅长将需求转化为具体的技术实现方案",
            user_message=prompt,
            temperature=0.2
        )
        
        try:
            structured_summary = json.loads(response)
            
            # 验证摘要质量
            from common.quality_validator import QualityValidator
            validator = QualityValidator()
            
            score = validator.calculate_quality_score(structured_summary)
            if score < 80:
                logger.log(f"⚠️ 摘要质量分数较低: {score}", level="warning")
                # 可以触发重新生成或人工审核
            
            return {
                "version_id": version.id,
                "quality_score": score,
                "summary": structured_summary
            }
            
        except json.JSONDecodeError as e:
            logger.log(f"❌ JSON解析失败: {str(e)}", level="error")
            raise ValueError("生成的摘要格式不正确")