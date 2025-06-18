"""
智能盲点检测器的完整实现
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set
import re
import json
from dataclasses import dataclass
from datetime import datetime

from llm_services.executor import run_prompt
from common.logger import Logger

logger = Logger.get_instance("clarifier")

class BlindSpotType(Enum):
    """需求盲点类型"""
    EDGE_CASE = "edge_case"
    SCALABILITY = "scalability"
    SECURITY = "security"
    USER_EXPERIENCE = "user_experience"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    ERROR_HANDLING = "error_handling"
    DATA_CONSISTENCY = "data_consistency"
    REGULATORY = "regulatory"
    BUSINESS_LOGIC = "business_logic"
    ACCESSIBILITY = "accessibility"
    LOCALIZATION = "localization"

@dataclass
class BlindSpot:
    """盲点数据结构"""
    id: str
    type: BlindSpotType
    title: str
    description: str
    context: str
    missing_aspects: List[str]
    questions: List[str]
    severity: str  # critical, high, medium, low
    confidence: float
    suggestions: List[str]
    related_features: List[str]

class BlindSpotPatternLibrary:
    """盲点模式库"""
    
    @staticmethod
    def get_patterns() -> Dict[BlindSpotType, List[Dict]]:
        """获取所有盲点检测模式"""
        return {
            BlindSpotType.EDGE_CASE: [
                {
                    "name": "文件上传边界",
                    "triggers": ["上传", "文件", "附件", "文档"],
                    "missing_checks": [
                        "文件大小限制",
                        "文件类型限制",
                        "并发上传处理",
                        "上传失败重试",
                        "断点续传",
                        "病毒扫描"
                    ],
                    "questions": [
                        "文件大小限制是多少？超过限制如何提示？",
                        "允许哪些文件格式？如何验证文件内容与扩展名一致？",
                        "用户可以同时上传多少个文件？",
                        "网络中断时如何处理？是否支持断点续传？",
                        "如何防止恶意文件上传？需要病毒扫描吗？"
                    ]
                },
                {
                    "name": "数据删除边界",
                    "triggers": ["删除", "移除", "清理", "归档"],
                    "missing_checks": [
                        "软删除vs硬删除",
                        "级联删除影响",
                        "删除权限控制",
                        "数据恢复机制",
                        "审计日志"
                    ],
                    "questions": [
                        "是软删除还是硬删除？软删除保留多久？",
                        "删除时相关联的数据如何处理？",
                        "谁有权限执行删除？需要二次确认吗？",
                        "误删后如何恢复？恢复窗口期多长？",
                        "删除操作是否需要记录审计日志？"
                    ]
                },
                {
                    "name": "并发操作边界",
                    "triggers": ["同时", "并发", "多个用户", "协作"],
                    "missing_checks": [
                        "并发冲突处理",
                        "数据锁定机制",
                        "版本控制",
                        "冲突解决策略"
                    ],
                    "questions": [
                        "多个用户同时编辑同一数据时如何处理？",
                        "是否需要实时协作？如何显示其他用户的操作？",
                        "发生冲突时，以谁的修改为准？",
                        "是否需要版本历史和回滚功能？"
                    ]
                }
            ],
            
            BlindSpotType.SCALABILITY: [
                {
                    "name": "用户规模扩展",
                    "triggers": ["用户", "客户", "会员", "账号"],
                    "missing_checks": [
                        "并发用户数",
                        "总用户量",
                        "增长预期",
                        "性能基准"
                    ],
                    "questions": [
                        "系统需要支持多少并发在线用户？",
                        "预计一年后的用户总量是多少？",
                        "用户增长最快的场景是什么？",
                        "单个操作的响应时间要求是多少？"
                    ]
                },
                {
                    "name": "数据量扩展",
                    "triggers": ["数据", "记录", "历史", "日志"],
                    "missing_checks": [
                        "数据增长率",
                        "存储策略",
                        "查询性能",
                        "归档策略"
                    ],
                    "questions": [
                        "数据量的增长速度如何？每天/每月新增多少？",
                        "历史数据保留多久？如何归档？",
                        "大数据量下的查询性能要求？",
                        "是否需要分表分库？什么时候触发？"
                    ]
                }
            ],
            
            BlindSpotType.SECURITY: [
                {
                    "name": "身份认证安全",
                    "triggers": ["登录", "认证", "密码", "账号"],
                    "missing_checks": [
                        "密码策略",
                        "多因素认证",
                        "会话管理",
                        "异常登录检测"
                    ],
                    "questions": [
                        "密码复杂度要求是什么？",
                        "是否需要多因素认证（2FA）？",
                        "会话超时时间是多久？如何处理？",
                        "如何检测异常登录（异地、异常时间）？",
                        "连续登录失败如何处理？"
                    ]
                },
                {
                    "name": "数据安全",
                    "triggers": ["敏感", "隐私", "个人信息", "加密"],
                    "missing_checks": [
                        "数据加密",
                        "传输安全",
                        "访问控制",
                        "数据脱敏"
                    ],
                    "questions": [
                        "哪些数据需要加密存储？使用什么加密算法？",
                        "API通信是否使用HTTPS？",
                        "敏感数据的访问权限如何控制？",
                        "日志中如何脱敏敏感信息？",
                        "如何防止SQL注入和XSS攻击？"
                    ]
                }
            ],
            
            BlindSpotType.ERROR_HANDLING: [
                {
                    "name": "支付错误处理",
                    "triggers": ["支付", "付款", "交易", "退款"],
                    "missing_checks": [
                        "支付失败处理",
                        "超时处理",
                        "重复支付",
                        "退款流程",
                        "对账机制"
                    ],
                    "questions": [
                        "支付失败如何处理？自动重试几次？",
                        "支付超时如何判断？超时后如何处理？",
                        "如何防止重复支付？",
                        "退款流程是怎样的？退款失败如何处理？",
                        "如何与第三方支付平台对账？"
                    ]
                },
                {
                    "name": "系统错误处理",
                    "triggers": ["错误", "异常", "失败", "故障"],
                    "missing_checks": [
                        "错误分类",
                        "用户提示",
                        "降级策略",
                        "错误监控"
                    ],
                    "questions": [
                        "系统错误如何分类？哪些展示给用户？",
                        "用户友好的错误提示是什么样的？",
                        "关键服务不可用时的降级策略？",
                        "如何监控和告警系统错误？",
                        "错误日志保留多久？如何分析？"
                    ]
                }
            ],
            
            BlindSpotType.USER_EXPERIENCE: [
                {
                    "name": "加载性能体验",
                    "triggers": ["加载", "等待", "响应", "刷新"],
                    "missing_checks": [
                        "加载状态",
                        "骨架屏",
                        "进度提示",
                        "取消操作"
                    ],
                    "questions": [
                        "页面加载时如何显示加载状态？",
                        "长时间操作如何显示进度？",
                        "用户能否取消正在进行的操作？",
                        "如何优化首屏加载时间？",
                        "是否需要离线缓存功能？"
                    ]
                },
                {
                    "name": "移动端体验",
                    "triggers": ["手机", "移动", "响应式", "APP"],
                    "missing_checks": [
                        "触摸操作",
                        "屏幕适配",
                        "网络优化",
                        "手势支持"
                    ],
                    "questions": [
                        "移动端的交互方式有何不同？",
                        "如何适配不同屏幕尺寸？",
                        "移动网络下如何优化体验？",
                        "是否支持手势操作？哪些手势？",
                        "移动端特有功能（相机、定位等）如何使用？"
                    ]
                }
            ],
            
            BlindSpotType.DATA_CONSISTENCY: [
                {
                    "name": "分布式一致性",
                    "triggers": ["分布式", "微服务", "多个服务", "同步"],
                    "missing_checks": [
                        "事务处理",
                        "最终一致性",
                        "补偿机制",
                        "幂等性"
                    ],
                    "questions": [
                        "跨服务的事务如何保证？",
                        "使用最终一致性还是强一致性？",
                        "失败时的补偿机制是什么？",
                        "如何保证接口的幂等性？",
                        "数据不一致时如何检测和修复？"
                    ]
                }
            ],
            
            BlindSpotType.REGULATORY: [
                {
                    "name": "隐私合规",
                    "triggers": ["个人信息", "隐私", "GDPR", "用户数据"],
                    "missing_checks": [
                        "数据收集同意",
                        "数据可携带性",
                        "删除权",
                        "数据最小化"
                    ],
                    "questions": [
                        "收集用户数据前如何获得同意？",
                        "用户如何导出自己的所有数据？",
                        "用户要求删除数据时如何处理？",
                        "是否只收集必要的最少数据？",
                        "数据泄露时如何通知用户？"
                    ]
                }
            ]
        }

class BlindSpotDetector:
    """智能盲点检测器"""
    
    def __init__(self):
        self.pattern_library = BlindSpotPatternLibrary()
        self.detected_blind_spots: List[BlindSpot] = []
        self.detection_history: List[Dict] = []
        
    async def detect_blind_spots(
        self, 
        prd_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[BlindSpot]:
        """检测PRD中的盲点"""
        logger.log("🔍 开始盲点检测分析", level="info")
        
        blind_spots = []
        
        # 1. 基于模式的检测
        pattern_blind_spots = self._pattern_based_detection(prd_content)
        blind_spots.extend(pattern_blind_spots)
        
        # 2. 基于上下文的检测
        if context:
            context_blind_spots = self._context_based_detection(prd_content, context)
            blind_spots.extend(context_blind_spots)
        
        # 3. AI深度分析检测
        ai_blind_spots = await self._ai_deep_detection(prd_content, blind_spots)
        blind_spots.extend(ai_blind_spots)
        
        # 4. 去重和优先级排序
        unique_blind_spots = self._deduplicate_blind_spots(blind_spots)
        sorted_blind_spots = self._prioritize_blind_spots(unique_blind_spots)
        
        # 5. 生成盲点ID
        for i, blind_spot in enumerate(sorted_blind_spots):
            blind_spot.id = f"BS_{datetime.now().strftime('%Y%m%d')}_{i+1:03d}"
        
        self.detected_blind_spots = sorted_blind_spots
        self._record_detection(prd_content, sorted_blind_spots)
        
        logger.log(f"✅ 检测完成，发现 {len(sorted_blind_spots)} 个盲点", level="info")
        
        return sorted_blind_spots
    
    def _pattern_based_detection(self, prd_content: str) -> List[BlindSpot]:
        """基于模式库的盲点检测"""
        blind_spots = []
        patterns = self.pattern_library.get_patterns()
        
        for blind_spot_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                # 检查触发词
                if self._check_triggers(prd_content, pattern["triggers"]):
                    # 检查是否已经处理了相关内容
                    missing_aspects = self._find_missing_aspects(
                        prd_content, 
                        pattern["missing_checks"]
                    )
                    
                    if missing_aspects:
                        blind_spot = BlindSpot(
                            id="",  # 后续分配
                            type=blind_spot_type,
                            title=pattern["name"],
                            description=f"检测到{pattern['name']}相关需求，但缺少重要考虑",
                            context=self._extract_context(prd_content, pattern["triggers"]),
                            missing_aspects=missing_aspects,
                            questions=pattern["questions"],
                            severity=self._assess_severity(blind_spot_type, len(missing_aspects)),
                            confidence=0.8,
                            suggestions=self._generate_suggestions(pattern["name"], missing_aspects),
                            related_features=self._find_related_features(prd_content, pattern["triggers"])
                        )
                        blind_spots.append(blind_spot)
        
        return blind_spots
    
    def _check_triggers(self, content: str, triggers: List[str]) -> bool:
        """检查内容中是否包含触发词"""
        content_lower = content.lower()
        return any(trigger.lower() in content_lower for trigger in triggers)
    
    def _find_missing_aspects(self, content: str, checks: List[str]) -> List[str]:
        """找出缺失的考虑方面"""
        missing = []
        content_lower = content.lower()
        
        for check in checks:
            # 简单的关键词检查，实际可以更复杂
            keywords = check.lower().split()
            if not any(keyword in content_lower for keyword in keywords):
                missing.append(check)
        
        return missing
    
    def _extract_context(self, content: str, triggers: List[str]) -> str:
        """提取触发词周围的上下文"""
        sentences = content.split('。')
        relevant_sentences = []
        
        for sentence in sentences:
            if any(trigger in sentence for trigger in triggers):
                relevant_sentences.append(sentence.strip())
        
        return '。'.join(relevant_sentences[:3])  # 最多返回3个相关句子
    
    def _assess_severity(self, blind_spot_type: BlindSpotType, missing_count: int) -> str:
        """评估盲点严重程度"""
        # 关键类型
        critical_types = [
            BlindSpotType.SECURITY, 
            BlindSpotType.DATA_CONSISTENCY,
            BlindSpotType.REGULATORY
        ]
        
        if blind_spot_type in critical_types:
            return "critical" if missing_count > 2 else "high"
        elif blind_spot_type in [BlindSpotType.ERROR_HANDLING, BlindSpotType.SCALABILITY]:
            return "high" if missing_count > 3 else "medium"
        else:
            return "medium" if missing_count > 2 else "low"
    
    def _generate_suggestions(self, pattern_name: str, missing_aspects: List[str]) -> List[str]:
        """生成改进建议"""
        suggestions = [
            f"建议添加关于{pattern_name}的详细说明",
            f"明确定义以下方面：{', '.join(missing_aspects[:3])}",
            "考虑添加具体的数值指标和边界条件",
            "与技术团队讨论实现可行性"
        ]
        return suggestions
    
    def _find_related_features(self, content: str, triggers: List[str]) -> List[str]:
        """找出相关的功能特性"""
        # 简化实现，实际应该更智能
        features = []
        
        # 使用正则提取功能名称
        feature_pattern = r'(?:功能|模块|特性)[：:]\s*(\S+)'
        matches = re.findall(feature_pattern, content)
        features.extend(matches)
        
        return list(set(features))[:5]  # 最多返回5个
    
    async def _ai_deep_detection(
        self, 
        prd_content: str, 
        existing_blind_spots: List[BlindSpot]
    ) -> List[BlindSpot]:
        """使用AI进行深度盲点检测"""
        # 构建已检测盲点的摘要，避免重复
        existing_summary = "\n".join([
            f"- {bs.title}: {bs.description}"
            for bs in existing_blind_spots
        ])
        
        prompt = f"""
        作为一个经验丰富的产品经理和架构师，请分析以下PRD文档，找出潜在的需求盲点。
        
        已经检测到的盲点：
        {existing_summary}
        
        请找出其他未被发现的盲点，特别关注：
        1. 隐含的业务逻辑假设
        2. 未明确的异常场景
        3. 缺失的非功能性需求
        4. 潜在的用户体验问题
        5. 可能的技术限制
        6. 未来扩展性考虑
        
        PRD内容：
        {prd_content[:3000]}  # 限制长度
        
        请以JSON格式返回发现的盲点列表，每个盲点包含：
        - title: 盲点标题
        - type: 类型（edge_case/scalability/security/user_experience/integration/performance/error_handling/data_consistency/regulatory/business_logic）
        - description: 详细描述
        - missing_aspects: 缺失的考虑点列表
        - questions: 需要澄清的问题列表
        - severity: 严重程度（critical/high/medium/low）
        - suggestions: 改进建议列表
        """
        
        try:
            response = await run_prompt(
                system_message="你是一个细致的需求分析专家，擅长发现需求文档中的潜在问题和遗漏。",
                user_message=prompt,
                temperature=0.7
            )
            
            # 解析AI响应
            ai_blind_spots = self._parse_ai_response(response)
            
            # 转换为BlindSpot对象
            blind_spots = []
            for ai_bs in ai_blind_spots:
                blind_spot = BlindSpot(
                    id="",
                    type=BlindSpotType(ai_bs.get("type", "business_logic")),
                    title=ai_bs.get("title", "未命名盲点"),
                    description=ai_bs.get("description", ""),
                    context="AI分析发现",
                    missing_aspects=ai_bs.get("missing_aspects", []),
                    questions=ai_bs.get("questions", []),
                    severity=ai_bs.get("severity", "medium"),
                    confidence=0.7,  # AI检测的置信度略低
                    suggestions=ai_bs.get("suggestions", []),
                    related_features=[]
                )
                blind_spots.append(blind_spot)
            
            return blind_spots
            
        except Exception as e:
            logger.log(f"❌ AI盲点检测失败: {str(e)}", level="error")
            return []
    
    def _parse_ai_response(self, response: str) -> List[Dict]:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # 尝试解析整个响应
                return json.loads(response)
        except:
            # 如果解析失败，返回空列表
            logger.log("⚠️ 无法解析AI响应为JSON格式", level="warning")
            return []
    
    def _context_based_detection(
        self, 
        prd_content: str, 
        context: Dict[str, Any]
    ) -> List[BlindSpot]:
        """基于项目上下文的盲点检测"""
        blind_spots = []
        
        # 根据项目类型检测特定盲点
        project_type = context.get("project_type", "")
        
        if project_type == "e-commerce":
            # 电商特定的盲点
            blind_spots.extend(self._check_ecommerce_blind_spots(prd_content))
        elif project_type == "saas":
            # SaaS特定的盲点
            blind_spots.extend(self._check_saas_blind_spots(prd_content))
        elif project_type == "mobile_app":
            # 移动应用特定的盲点
            blind_spots.extend(self._check_mobile_blind_spots(prd_content))
        
        # 根据用户规模检测
        user_scale = context.get("user_scale", "")
        if user_scale == "large":  # 大规模用户
            blind_spots.extend(self._check_scale_blind_spots(prd_content))
        
        return blind_spots
    
    def _check_ecommerce_blind_spots(self, content: str) -> List[BlindSpot]:
        """检查电商特定的盲点"""
        blind_spots = []
        
        # 检查库存管理
        if "商品" in content and "库存" not in content:
            blind_spots.append(BlindSpot(
                id="",
                type=BlindSpotType.BUSINESS_LOGIC,
                title="库存管理缺失",
                description="电商系统需要考虑库存管理",
                context="检测到商品相关功能",
                missing_aspects=["库存追踪", "超卖预防", "库存预警"],
                questions=[
                    "如何管理商品库存？",
                    "如何防止超卖？",
                    "库存不足时如何处理？"
                ],
                severity="high",
                confidence=0.9,
                suggestions=["添加库存管理模块", "实现库存锁定机制"],
                related_features=["商品管理", "订单处理"]
            ))
        
        return blind_spots
    
    def _check_saas_blind_spots(self, content: str) -> List[BlindSpot]:
        """检查SaaS特定的盲点"""
        blind_spots = []
        
        # 检查多租户
        if "用户" in content and "租户" not in content and "多租户" not in content:
            blind_spots.append(BlindSpot(
                id="",
                type=BlindSpotType.SCALABILITY,
                title="多租户架构考虑",
                description="SaaS系统通常需要支持多租户",
                context="SaaS项目",
                missing_aspects=["数据隔离", "租户管理", "资源配额"],
                questions=[
                    "是否需要支持多租户？",
                    "如何实现租户间的数据隔离？",
                    "每个租户的资源配额如何管理？"
                ],
                severity="high",
                confidence=0.8,
                suggestions=["考虑多租户架构设计", "定义租户隔离策略"],
                related_features=["用户管理", "数据存储"]
            ))
        
        return blind_spots
    
    def _check_mobile_blind_spots(self, content: str) -> List[BlindSpot]:
        """检查移动应用特定的盲点"""
        blind_spots = []
        
        # 检查离线功能
        if "移动" in content or "APP" in content:
            if "离线" not in content and "断网" not in content:
                blind_spots.append(BlindSpot(
                    id="",
                    type=BlindSpotType.USER_EXPERIENCE,
                    title="离线使用场景",
                    description="移动应用需要考虑离线使用场景",
                    context="移动应用",
                    missing_aspects=["离线数据缓存", "离线操作队列", "数据同步策略"],
                    questions=[
                        "断网时哪些功能可以使用？",
                        "离线数据如何缓存？",
                        "恢复网络后如何同步数据？"
                    ],
                    severity="medium",
                    confidence=0.85,
                    suggestions=["设计离线模式", "实现数据同步机制"],
                    related_features=["数据管理", "用户体验"]
                ))
        
        return blind_spots
    
    def _check_scale_blind_spots(self, content: str) -> List[BlindSpot]:
        """检查大规模相关的盲点"""
        # 实现大规模系统特定的检查
        return []
    
    def _deduplicate_blind_spots(self, blind_spots: List[BlindSpot]) -> List[BlindSpot]:
        """去除重复的盲点"""
        unique_blind_spots = []
        seen_keys = set()
        
        for bs in blind_spots:
            # 使用类型和标题作为唯一键
            key = f"{bs.type.value}:{bs.title}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_blind_spots.append(bs)
            else:
                # 如果有重复，合并问题和建议
                for existing_bs in unique_blind_spots:
                    if f"{existing_bs.type.value}:{existing_bs.title}" == key:
                        # 合并问题列表
                        existing_bs.questions.extend(
                            q for q in bs.questions 
                            if q not in existing_bs.questions
                        )
                        # 合并建议列表
                        existing_bs.suggestions.extend(
                            s for s in bs.suggestions 
                            if s not in existing_bs.suggestions
                        )
                        # 更新置信度（取最高值）
                        existing_bs.confidence = max(existing_bs.confidence, bs.confidence)
                        break
        
        return unique_blind_spots
    
    def _prioritize_blind_spots(self, blind_spots: List[BlindSpot]) -> List[BlindSpot]:
        """根据严重程度和置信度排序盲点"""
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        return sorted(
            blind_spots,
            key=lambda bs: (
                severity_order.get(bs.severity, 4),
                -bs.confidence,  # 置信度高的优先
                bs.title
            )
        )
    
    def _record_detection(self, prd_content: str, blind_spots: List[BlindSpot]):
        """记录检测历史"""
        self.detection_history.append({
            "timestamp": datetime.now().isoformat(),
            "prd_hash": hash(prd_content[:100]),  # 简单的内容标识
            "blind_spots_count": len(blind_spots),
            "severity_distribution": self._get_severity_distribution(blind_spots),
            "type_distribution": self._get_type_distribution(blind_spots)
        })
    
    def _get_severity_distribution(self, blind_spots: List[BlindSpot]) -> Dict[str, int]:
        """获取严重程度分布"""
        distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for bs in blind_spots:
            distribution[bs.severity] += 1
        return distribution
    
    def _get_type_distribution(self, blind_spots: List[BlindSpot]) -> Dict[str, int]:
        """获取类型分布"""
        distribution = {}
        for bs in blind_spots:
            type_name = bs.type.value
            distribution[type_name] = distribution.get(type_name, 0) + 1
        return distribution
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """获取检测摘要"""
        if not self.detected_blind_spots:
            return {"message": "尚未进行盲点检测"}
        
        return {
            "total_blind_spots": len(self.detected_blind_spots),
            "severity_distribution": self._get_severity_distribution(self.detected_blind_spots),
            "type_distribution": self._get_type_distribution(self.detected_blind_spots),
            "critical_blind_spots": [
                {
                    "id": bs.id,
                    "title": bs.title,
                    "questions": bs.questions[:2]  # 只显示前两个问题
                }
                for bs in self.detected_blind_spots
                if bs.severity == "critical"
            ],
            "top_suggestions": self._get_top_suggestions()
        }
    
    def _get_top_suggestions(self) -> List[str]:
        """获取最重要的建议"""
        all_suggestions = []
        
        # 收集所有高严重度盲点的建议
        for bs in self.detected_blind_spots:
            if bs.severity in ["critical", "high"]:
                all_suggestions.extend(bs.suggestions)
        
        # 去重并返回前5个
        unique_suggestions = list(dict.fromkeys(all_suggestions))
        return unique_suggestions[:5]
    
    def export_blind_spots(self, format: str = "json") -> str:
        """导出盲点检测结果"""
        if format == "json":
            return json.dumps(
                [self._blind_spot_to_dict(bs) for bs in self.detected_blind_spots],
                ensure_ascii=False,
                indent=2
            )
        elif format == "markdown":
            return self._export_as_markdown()
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _blind_spot_to_dict(self, blind_spot: BlindSpot) -> Dict[str, Any]:
        """将BlindSpot转换为字典"""
        return {
            "id": blind_spot.id,
            "type": blind_spot.type.value,
            "title": blind_spot.title,
            "description": blind_spot.description,
            "context": blind_spot.context,
            "missing_aspects": blind_spot.missing_aspects,
            "questions": blind_spot.questions,
            "severity": blind_spot.severity,
            "confidence": blind_spot.confidence,
            "suggestions": blind_spot.suggestions,
            "related_features": blind_spot.related_features
        }
    
    def _export_as_markdown(self) -> str:
        """导出为Markdown格式"""
        md_lines = ["# 需求盲点检测报告", ""]
        
        # 摘要
        summary = self.get_detection_summary()
        md_lines.extend([
            "## 检测摘要",
            f"- 总计发现盲点：{summary['total_blind_spots']}个",
            f"- 严重程度分布：{summary['severity_distribution']}",
            ""
        ])
        
        # 按严重程度分组
        severity_groups = {}
        for bs in self.detected_blind_spots:
            if bs.severity not in severity_groups:
                severity_groups[bs.severity] = []
            severity_groups[bs.severity].append(bs)
        
        # 输出每个严重程度的盲点
        for severity in ["critical", "high", "medium", "low"]:
            if severity in severity_groups:
                md_lines.extend([
                    f"## {severity.upper()} 级别盲点",
                    ""
                ])
                
                for bs in severity_groups[severity]:
                    md_lines.extend([
                        f"### {bs.id}: {bs.title}",
                        f"**描述**：{bs.description}",
                        "",
                        "**缺失考虑**：",
                        *[f"- {aspect}" for aspect in bs.missing_aspects],
                        "",
                        "**澄清问题**：",
                        *[f"1. {q}" for q in bs.questions],
                        "",
                        "**改进建议**：",
                        *[f"- {s}" for s in bs.suggestions],
                        "",
                        "---",
                        ""
                    ])
        
        return "\n".join(md_lines)