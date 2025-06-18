"""
改进的上下文检索模块。
根据推理阶段动态构建精准、相关的上下文，避免信息过载。
"""

from typing import Dict, List, Optional, Any, Tuple
import json
from enum import Enum
from dataclasses import dataclass

from knowledge.config import logger, DEFAULT_TOP_K
from knowledge.vector_store import get_vector_store
from knowledge.entity_storage import retrieve_entity, retrieve_similar_entities
from knowledge.reasoning_memory import retrieve_entity_reasoning_history

class ContextType(Enum):
    """上下文类型枚举"""
    ENTITY_INFO = "entity_info"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    SIMILAR_EXAMPLES = "similar_examples"
    DEPENDENCIES = "dependencies"
    CONSTRAINTS = "constraints"
    HISTORY = "history"
    PATTERNS = "patterns"

@dataclass
class ContextSection:
    """上下文片段"""
    type: ContextType
    title: str
    content: str
    relevance_score: float = 1.0
    max_length: int = 1000

class FocusedContextBuilder:
    """聚焦的上下文构建器"""
    
    def __init__(self):
        self.context_sections: List[ContextSection] = []
        self.max_total_length = 5000  # 总长度限制
        
    async def build_for_phase(
        self,
        entity_name: str,
        phase: str,
        current_summary: Dict[str, Any],
        previous_qa: Optional[List[Dict[str, str]]] = None,
        global_constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        为特定阶段构建聚焦的上下文。
        
        Args:
            entity_name: 实体名称
            phase: 推理阶段
            current_summary: 当前摘要
            previous_qa: 历史问答
            global_constraints: 全局约束
            
        Returns:
            str: 优化后的上下文
        """
        self.context_sections = []
        
        # 根据阶段选择需要的上下文类型
        if phase == "功能定义与边界划分":
            await self._add_entity_info(entity_name, current_summary)
            await self._add_domain_knowledge(entity_name, phase)
            await self._add_similar_modules(entity_name, limit=2)
            
        elif phase == "技术实现与模式选择":
            await self._add_entity_summary(current_summary, focus="functionality")
            await self._add_pattern_recommendations(entity_name)
            await self._add_tech_stack_examples(entity_name)
            if previous_qa:
                self._add_previous_decisions(previous_qa, limit=3)
                
        elif phase == "集成设计与依赖分析":
            await self._add_entity_summary(current_summary, focus="technical")
            await self._add_dependency_context(entity_name)
            await self._add_integration_patterns()
            if global_constraints:
                self._add_constraints(global_constraints, focus="integration")
                
        elif phase == "质量保证与优化":
            await self._add_entity_summary(current_summary, focus="implementation")
            await self._add_quality_patterns()
            await self._add_performance_guidelines(entity_name)
            await self._add_security_guidelines(entity_name)
        
        # 优化和格式化上下文
        return self._format_optimized_context(phase)
    
    async def _add_entity_info(self, entity_name: str, summary: Dict[str, Any]):
        """添加实体基本信息"""
        content_parts = [
            f"实体名称: {entity_name}",
            f"类型: {summary.get('type', '未定义')}",
            f"描述: {summary.get('description', '待定义')}"
        ]
        
        # 如果有现有功能定义，添加摘要
        if summary.get('core_functionality'):
            content_parts.append("\n已识别的功能:")
            for func in summary['core_functionality'][:3]:
                content_parts.append(f"- {func}")
        
        self.context_sections.append(
            ContextSection(
                type=ContextType.ENTITY_INFO,
                title="实体信息",
                content="\n".join(content_parts),
                relevance_score=1.0,
                max_length=500
            )
        )
    
    async def _add_domain_knowledge(self, entity_name: str, phase: str):
        """添加领域知识"""
        # 根据实体名称推断领域
        domain_keywords = self._extract_domain_keywords(entity_name)
        
        domain_content = []
        
        # 用户管理领域
        if any(keyword in entity_name.lower() for keyword in ['user', '用户', 'auth', '认证']):
            domain_content.extend([
                "用户管理领域最佳实践:",
                "- 使用JWT或OAuth2进行认证",
                "- 密码应使用bcrypt或argon2加密",
                "- 实现用户会话管理和令牌刷新",
                "- 考虑多因素认证(MFA)支持",
                "- 用户数据应遵循GDPR等隐私法规"
            ])
        
        # 订单/交易领域
        elif any(keyword in entity_name.lower() for keyword in ['order', '订单', 'payment', '支付']):
            domain_content.extend([
                "订单管理领域最佳实践:",
                "- 使用状态机管理订单生命周期",
                "- 实现幂等性以防止重复订单",
                "- 考虑分布式事务或Saga模式",
                "- 订单数据应支持审计追踪",
                "- 集成支付网关时注意PCI合规"
            ])
        
        # 通用领域知识
        else:
            domain_content.extend([
                f"{entity_name}模块设计考虑:",
                "- 明确定义模块边界和职责",
                "- 使用领域驱动设计(DDD)原则",
                "- 考虑SOLID设计原则",
                "- 实现适当的错误处理和日志记录"
            ])
        
        if domain_content:
            self.context_sections.append(
                ContextSection(
                    type=ContextType.DOMAIN_KNOWLEDGE,
                    title="领域知识",
                    content="\n".join(domain_content),
                    relevance_score=0.9,
                    max_length=600
                )
            )
    
    async def _add_similar_modules(self, entity_name: str, limit: int = 2):
        """添加相似模块示例"""
        similar_entities = retrieve_similar_entities(entity_name, top_k=limit)
        
        if similar_entities:
            content_parts = ["参考相似模块的设计:"]
            
            for entity in similar_entities[:limit]:
                name = entity.get('name', 'unknown')
                desc = entity.get('description', '')
                
                # 提取关键设计要素
                if entity.get('technical_decisions'):
                    tech = entity['technical_decisions']
                    content_parts.append(f"\n{name}:")
                    content_parts.append(f"  描述: {desc[:100]}...")
                    if tech.get('framework'):
                        content_parts.append(f"  技术栈: {tech.get('framework')}")
                    if entity.get('implementation', {}).get('services'):
                        services = entity['implementation']['services'][:3]
                        content_parts.append(f"  核心服务: {', '.join(services)}")
            
            self.context_sections.append(
                ContextSection(
                    type=ContextType.SIMILAR_EXAMPLES,
                    title="相似模块参考",
                    content="\n".join(content_parts),
                    relevance_score=0.8,
                    max_length=500
                )
            )
    
    async def _add_pattern_recommendations(self, entity_name: str):
        """添加设计模式建议"""
        patterns = []
        
        # 基于实体类型推荐模式
        entity_lower = entity_name.lower()
        
        if 'service' in entity_lower:
            patterns.append({
                "name": "Service Layer Pattern",
                "usage": "封装业务逻辑，提供统一的服务接口",
                "example": "UserService, OrderService"
            })
        
        if 'repository' in entity_lower or 'repo' in entity_lower:
            patterns.append({
                "name": "Repository Pattern",
                "usage": "抽象数据访问逻辑，提供领域对象的持久化",
                "example": "UserRepository接口 + UserRepositoryImpl实现"
            })
        
        if 'controller' in entity_lower:
            patterns.append({
                "name": "MVC Pattern",
                "usage": "分离展示逻辑和业务逻辑",
                "example": "UserController处理HTTP请求，调用UserService"
            })
        
        # 通用推荐
        patterns.extend([
            {
                "name": "Dependency Injection",
                "usage": "降低模块间耦合，提高可测试性",
                "example": "通过构造函数注入依赖服务"
            },
            {
                "name": "Factory Pattern",
                "usage": "创建复杂对象时隐藏创建细节",
                "example": "UserFactory.createUser(data)"
            }
        ])
        
        content_parts = ["推荐的设计模式:"]
        for pattern in patterns[:4]:  # 限制数量
            content_parts.append(f"\n{pattern['name']}:")
            content_parts.append(f"  用途: {pattern['usage']}")
            content_parts.append(f"  示例: {pattern['example']}")
        
        self.context_sections.append(
            ContextSection(
                type=ContextType.PATTERNS,
                title="设计模式建议",
                content="\n".join(content_parts),
                relevance_score=0.85,
                max_length=600
            )
        )
    
    async def _add_dependency_context(self, entity_name: str):
        """添加精简的依赖上下文"""
        try:
            from dependency import dependency_manager
            dm = dependency_manager.DependencyManager()
            
            content_parts = []
            
            # 获取层次信息
            if entity_name in dm.graph:
                layer = dm.graph[entity_name].get("layer") or dm.infer_layer(entity_name)
                allowed_layers = dm.layer_rules.get(layer, [])
                
                content_parts.extend([
                    f"当前层次: {layer}",
                    f"允许依赖: {', '.join(allowed_layers)}",
                    "",
                    "依赖设计原则:",
                    "- 只依赖下层，不依赖上层",
                    "- 使用接口而非具体实现",
                    "- 避免循环依赖"
                ])
                
                # 检查现有依赖
                depends_on = dm.graph[entity_name].get("depends_on", [])
                if depends_on:
                    content_parts.append(f"\n现有依赖: {', '.join(depends_on[:5])}")
            else:
                content_parts.extend([
                    "依赖设计指导:",
                    "- 遵循分层架构原则",
                    "- 核心业务逻辑不依赖基础设施",
                    "- 使用依赖注入模式"
                ])
            
            self.context_sections.append(
                ContextSection(
                    type=ContextType.DEPENDENCIES,
                    title="依赖管理",
                    content="\n".join(content_parts),
                    relevance_score=0.9,
                    max_length=400
                )
            )
        except Exception as e:
            logger.log(f"获取依赖上下文失败: {e}", level="warning")
    
    async def _add_quality_patterns(self):
        """添加质量保证模式"""
        content = """质量保证关键点:

性能优化:
- 使用缓存减少数据库查询(Redis/内存缓存)
- 实现分页和懒加载
- 考虑数据库索引优化
- 使用连接池管理资源

安全措施:
- 输入验证和清理(防止注入攻击)
- 使用HTTPS和数据加密
- 实现访问控制(RBAC/ABAC)
- 敏感数据脱敏处理

测试策略:
- 单元测试覆盖核心逻辑(目标80%+)
- 集成测试验证模块交互
- 性能测试确保响应时间
- 安全测试检查漏洞"""
        
        self.context_sections.append(
            ContextSection(
                type=ContextType.PATTERNS,
                title="质量保证模式",
                content=content,
                relevance_score=0.9,
                max_length=500
            )
        )
    
    def _add_constraints(self, constraints: Dict[str, Any], focus: str = "general"):
        """添加相关约束"""
        relevant_constraints = []
        
        for key, value in constraints.items():
            # 根据焦点过滤约束
            if focus == "integration" and any(k in key.lower() for k in ['api', 'integration', 'protocol']):
                relevant_constraints.append(f"- {key}: {value}")
            elif focus == "general":
                relevant_constraints.append(f"- {key}: {value}")
        
        if relevant_constraints:
            self.context_sections.append(
                ContextSection(
                    type=ContextType.CONSTRAINTS,
                    title="架构约束",
                    content="相关架构约束:\n" + "\n".join(relevant_constraints[:5]),
                    relevance_score=0.85,
                    max_length=300
                )
            )
    
    def _add_previous_decisions(self, previous_qa: List[Dict[str, str]], limit: int = 3):
        """添加关键的历史决策"""
        if not previous_qa:
            return
        
        # 提取最重要的决策
        key_decisions = []
        
        for qa in previous_qa[-limit:]:
            question = qa.get('question', '')
            answer = qa.get('answer', '')
            
            # 识别关键决策(包含具体技术选择的)
            if any(keyword in answer.lower() for keyword in ['使用', 'implement', 'service', 'class', 'api']):
                # 提取答案的核心部分
                answer_summary = answer[:200] + "..." if len(answer) > 200 else answer
                key_decisions.append(f"Q: {question}\nA: {answer_summary}")
        
        if key_decisions:
            self.context_sections.append(
                ContextSection(
                    type=ContextType.HISTORY,
                    title="已做决策",
                    content="\n\n".join(key_decisions),
                    relevance_score=0.95,
                    max_length=600
                )
            )
    
    async def _add_entity_summary(self, summary: Dict[str, Any], focus: str = "general"):
        """添加实体摘要的特定部分"""
        content_parts = []
        
        if focus == "functionality" and summary.get('core_functionality'):
            content_parts.append("已定义的核心功能:")
            for func in summary['core_functionality']:
                content_parts.append(f"- {func}")
                
        elif focus == "technical" and summary.get('technical_decisions'):
            tech = summary['technical_decisions']
            content_parts.append("技术决策:")
            if tech.get('language'):
                content_parts.append(f"- 语言: {tech['language']}")
            if tech.get('framework'):
                content_parts.append(f"- 框架: {tech['framework']}")
            if tech.get('patterns'):
                content_parts.append(f"- 模式: {', '.join(tech['patterns'][:3])}")
                
        elif focus == "implementation" and summary.get('implementation'):
            impl = summary['implementation']
            content_parts.append("实现细节:")
            if impl.get('services'):
                content_parts.append(f"- 服务: {', '.join(impl['services'][:3])}")
            if impl.get('repositories'):
                content_parts.append(f"- 仓储: {', '.join(impl['repositories'][:3])}")
        
        if content_parts:
            self.context_sections.append(
                ContextSection(
                    type=ContextType.ENTITY_INFO,
                    title="当前设计状态",
                    content="\n".join(content_parts),
                    relevance_score=1.0,
                    max_length=400
                )
            )
    
    async def _add_tech_stack_examples(self, entity_name: str):
        """添加技术栈示例"""
        # 基于实体类型推荐技术栈
        examples = []
        
        if 'api' in entity_name.lower() or 'service' in entity_name.lower():
            examples.append({
                "scenario": "RESTful API服务",
                "stack": "Node.js + Express + TypeScript",
                "reason": "轻量级、高性能、类型安全"
            })
            examples.append({
                "scenario": "微服务架构",
                "stack": "Spring Boot 2.7 + Java 11",
                "reason": "成熟生态、企业级特性"
            })
        
        if 'web' in entity_name.lower() or 'frontend' in entity_name.lower():
            examples.append({
                "scenario": "现代Web应用",
                "stack": "React 18 + Next.js 13 + TypeScript",
                "reason": "SEO友好、性能优化、开发体验好"
            })
        
        if examples:
            content_parts = ["技术栈参考:"]
            for ex in examples[:2]:
                content_parts.append(f"\n{ex['scenario']}:")
                content_parts.append(f"  技术栈: {ex['stack']}")
                content_parts.append(f"  选择理由: {ex['reason']}")
            
            self.context_sections.append(
                ContextSection(
                    type=ContextType.PATTERNS,
                    title="技术栈示例",
                    content="\n".join(content_parts),
                    relevance_score=0.8,
                    max_length=400
                )
            )
    
    async def _add_integration_patterns(self):
        """添加集成模式"""
        content = """常用集成模式:

同步集成:
- RESTful API (HTTP/JSON)
- GraphQL (灵活查询)
- gRPC (高性能RPC)

异步集成:
- 消息队列 (RabbitMQ/Kafka)
- 事件驱动 (Event Bus)
- Webhook (回调通知)

数据集成:
- 数据库共享 (谨慎使用)
- ETL管道 (数据同步)
- API网关 (统一入口)"""
        
        self.context_sections.append(
            ContextSection(
                type=ContextType.PATTERNS,
                title="集成模式",
                content=content,
                relevance_score=0.85,
                max_length=400
            )
        )
    
    async def _add_performance_guidelines(self, entity_name: str):
        """添加性能指导"""
        guidelines = [
            "性能目标:",
            "- API响应时间 < 200ms (P95)",
            "- 支持并发用户数 > 1000",
            "- 数据库查询 < 50ms",
            "",
            "优化策略:",
            "- 实施缓存策略(Redis/CDN)",
            "- 数据库查询优化(索引/分页)",
            "- 异步处理耗时操作",
            "- 使用连接池和资源复用"
        ]
        
        self.context_sections.append(
            ContextSection(
                type=ContextType.PATTERNS,
                title="性能指南",
                content="\n".join(guidelines),
                relevance_score=0.8,
                max_length=300
            )
        )
    
    async def _add_security_guidelines(self, entity_name: str):
        """添加安全指导"""
        guidelines = [
            "安全要求:",
            "- 所有API需要认证(JWT/OAuth2)",
            "- 敏感数据加密存储(AES-256)",
            "- HTTPS传输加密",
            "- 实施访问控制(RBAC)",
            "",
            "安全实践:",
            "- 输入验证防止注入",
            "- 使用安全头(CORS/CSP)",
            "- 审计日志记录",
            "- 定期安全扫描"
        ]
        
        self.context_sections.append(
            ContextSection(
                type=ContextType.PATTERNS,
                title="安全指南",
                content="\n".join(guidelines),
                relevance_score=0.85,
                max_length=300
            )
        )
    
    def _extract_domain_keywords(self, entity_name: str) -> List[str]:
        """从实体名称提取领域关键词"""
        # 简单的关键词提取逻辑
        keywords = []
        name_lower = entity_name.lower()
        
        # 预定义的领域关键词映射
        domain_mappings = {
            'user': ['用户', 'account', 'profile', 'auth'],
            'order': ['订单', 'purchase', 'transaction'],
            'product': ['产品', 'item', 'catalog'],
            'payment': ['支付', 'billing', 'invoice'],
            'admin': ['管理', 'dashboard', 'control']
        }
        
        for key, values in domain_mappings.items():
            if key in name_lower or any(v in name_lower for v in values):
                keywords.append(key)
        
        return keywords
    
    def _format_optimized_context(self, phase: str) -> str:
        """格式化优化的上下文"""
        # 按相关性排序
        self.context_sections.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # 构建最终上下文
        formatted_parts = [
            f"# 架构设计上下文 - {phase}",
            ""
        ]
        
        current_length = 0
        
        for section in self.context_sections:
            if current_length >= self.max_total_length:
                break
            
            # 截断内容以适应长度限制
            content = section.content
            if len(content) > section.max_length:
                content = content[:section.max_length] + "..."
            
            # 添加节
            formatted_parts.extend([
                f"## {section.title}",
                content,
                ""
            ])
            
            current_length += len(content)
        
        # 添加提示
        formatted_parts.extend([
            "---",
            f"请基于以上上下文，针对{phase}阶段提供具体、可实施的设计方案。"
        ])
        
        return "\n".join(formatted_parts)

# 便捷函数
async def build_improved_context(
    entity_name: str,
    phase: str,
    current_summary: Dict[str, Any],
    **kwargs
) -> str:
    """
    构建改进的上下文的便捷函数。
    
    Args:
        entity_name: 实体名称
        phase: 推理阶段
        current_summary: 当前摘要
        **kwargs: 其他参数
        
    Returns:
        str: 优化的上下文
    """
    builder = FocusedContextBuilder()
    return await builder.build_for_phase(
        entity_name=entity_name,
        phase=phase,
        current_summary=current_summary,
        previous_qa=kwargs.get('previous_qa'),
        global_constraints=kwargs.get('global_constraints')
    )