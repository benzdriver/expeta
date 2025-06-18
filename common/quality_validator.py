"""
质量验证器模块。
用于评估生成内容的具体性和质量。
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class QualityLevel(Enum):
    """质量等级枚举"""
    EXCELLENT = "excellent"  # 90-100分
    GOOD = "good"           # 70-89分
    FAIR = "fair"           # 50-69分
    POOR = "poor"           # 0-49分

@dataclass
class QualityReport:
    """质量评估报告"""
    score: int
    level: QualityLevel
    issues: List[str]
    suggestions: List[str]
    metrics: Dict[str, Any]

class QualityValidator:
    """生成内容质量验证器"""
    
    # 空泛词汇列表
    VAGUE_TERMS = [
        "处理", "管理", "相关", "合适的", "一些", "某些",
        "功能", "模块", "可以考虑", "建议使用", "大概", "可能"
    ]
    
    # 具体性指标
    SPECIFICITY_PATTERNS = {
        "class_names": r'[A-Z]\w+(?:Service|Repository|Controller|Factory|Builder|Manager|Handler|Provider|Validator)',
        "method_signatures": r'\w+\([^)]*\)(?:\s*:\s*\w+)?',
        "api_endpoints": r'(?:GET|POST|PUT|DELETE|PATCH)\s+/[\w/\{\}]+',
        "version_numbers": r'\d+\.\d+(?:\.\d+)?',
        "field_definitions": r'\w+\s*:\s*(?:string|number|boolean|array|object|\w+\[\])',
        "concrete_examples": r'(?:例如|示例|如)[:：]\s*[^\n]+',
        "error_codes": r'(?:4\d{2}|5\d{2}|[A-Z_]+_ERROR)',
        "time_metrics": r'\d+\s*(?:ms|秒|分钟|毫秒|s)',
        "size_metrics": r'\d+\s*(?:MB|GB|KB|bytes)',
        "percentage": r'\d+\s*%'
    }
    
    @classmethod
    def validate_text(cls, text: str, context_type: str = "general") -> QualityReport:
        """
        验证文本内容的质量。
        
        Args:
            text: 要验证的文本
            context_type: 上下文类型（general, api, implementation, testing）
            
        Returns:
            QualityReport: 质量评估报告
        """
        score = 100
        issues = []
        suggestions = []
        metrics = {}
        
        # 1. 检查空泛词汇
        vague_count = 0
        for term in cls.VAGUE_TERMS:
            pattern = rf'\b{term}\b(?![A-Z]|\w+Service|\w+Repository|\w+Controller)'
            occurrences = len(re.findall(pattern, text, re.IGNORECASE))
            if occurrences > 0:
                vague_count += occurrences
                score -= min(3 * occurrences, 15)  # 最多扣15分
                issues.append(f"使用空泛词汇 '{term}' {occurrences} 次")
        
        metrics['vague_terms_count'] = vague_count
        
        # 2. 检查具体性指标
        specificity_scores = {}
        for pattern_name, pattern in cls.SPECIFICITY_PATTERNS.items():
            matches = re.findall(pattern, text)
            specificity_scores[pattern_name] = len(matches)
            metrics[f'{pattern_name}_count'] = len(matches)
        
        # 3. 根据上下文类型调整评分
        if context_type == "api":
            if specificity_scores['api_endpoints'] == 0:
                score -= 20
                issues.append("API设计缺少具体端点定义")
                suggestions.append("添加具体的RESTful端点，如 'POST /api/v1/users'")
            
            if specificity_scores['error_codes'] == 0:
                score -= 10
                issues.append("缺少错误码定义")
                suggestions.append("定义具体的错误码，如 '404 NOT_FOUND'")
                
        elif context_type == "implementation":
            if specificity_scores['class_names'] == 0:
                score -= 25
                issues.append("缺少具体的类名定义")
                suggestions.append("使用具体的类名，如 'UserService', 'OrderRepository'")
            
            if specificity_scores['method_signatures'] == 0:
                score -= 20
                issues.append("缺少方法签名")
                suggestions.append("提供完整的方法签名，如 'createUser(data: UserDTO): User'")
                
        elif context_type == "testing":
            if specificity_scores['percentage'] == 0:
                score -= 15
                issues.append("缺少具体的测试覆盖率指标")
                suggestions.append("明确测试覆盖率目标，如 '单元测试覆盖率 80%'")
        
        # 4. 检查内容长度和结构
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        if len(non_empty_lines) < 5:
            score -= 15
            issues.append("内容过于简短，缺少详细说明")
            suggestions.append("提供更详细的设计说明和实现细节")
        
        metrics['total_lines'] = len(lines)
        metrics['content_lines'] = len(non_empty_lines)
        
        # 5. 检查是否有代码示例或结构化内容
        has_code_block = '```' in text or '    ' in text
        has_list = re.search(r'^\s*[-*•]\s+', text, re.MULTILINE)
        has_numbered_list = re.search(r'^\s*\d+\.\s+', text, re.MULTILINE)
        
        structured_content = has_code_block or has_list or has_numbered_list
        if not structured_content and len(text) > 200:
            score -= 10
            issues.append("缺少结构化内容（列表、代码示例等）")
            suggestions.append("使用列表、代码块等结构化格式组织内容")
        
        metrics['has_code_examples'] = has_code_block
        metrics['has_structured_content'] = structured_content
        
        # 6. 检查技术栈的具体性
        if "技术" in text or "框架" in text:
            if specificity_scores['version_numbers'] == 0:
                score -= 10
                issues.append("技术栈缺少版本号")
                suggestions.append("指定具体的技术版本，如 'Spring Boot 2.7.0'")
        
        # 确保分数在有效范围内
        score = max(0, min(100, score))
        
        # 确定质量等级
        if score >= 90:
            level = QualityLevel.EXCELLENT
        elif score >= 70:
            level = QualityLevel.GOOD
        elif score >= 50:
            level = QualityLevel.FAIR
        else:
            level = QualityLevel.POOR
        
        # 如果质量良好但仍有改进空间，添加建议
        if level in [QualityLevel.EXCELLENT, QualityLevel.GOOD] and not suggestions:
            if specificity_scores['concrete_examples'] == 0:
                suggestions.append("添加具体示例会让设计更清晰")
            if specificity_scores['time_metrics'] == 0 and context_type != "api":
                suggestions.append("考虑添加性能指标（响应时间、吞吐量等）")
        
        return QualityReport(
            score=score,
            level=level,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics
        )
    
    @classmethod
    def validate_json_summary(cls, summary: Dict[str, Any]) -> QualityReport:
        """
        验证JSON摘要的质量。
        
        Args:
            summary: JSON格式的摘要
            
        Returns:
            QualityReport: 质量评估报告
        """
        score = 100
        issues = []
        suggestions = []
        metrics = {}
        
        # 1. 检查必需字段
        required_fields = ["module", "description", "technical_decisions"]
        for field in required_fields:
            if field not in summary or not summary[field]:
                score -= 10
                issues.append(f"缺少必需字段 '{field}' 或字段为空")
        
        # 2. 检查技术决策的具体性
        tech_decisions = summary.get("technical_decisions", {})
        if isinstance(tech_decisions, dict):
            if not tech_decisions.get("language"):
                score -= 10
                issues.append("未指定编程语言")
                suggestions.append("明确指定使用的编程语言和版本")
            
            if not tech_decisions.get("framework"):
                score -= 10
                issues.append("未指定框架")
                suggestions.append("指定核心框架，如 'Spring Boot 2.7.0'")
        
        # 3. 检查实现细节
        implementation = summary.get("implementation", {})
        if isinstance(implementation, dict):
            services = implementation.get("services", [])
            if not services:
                score -= 15
                issues.append("缺少服务类定义")
                suggestions.append("列出具体的服务类，如 ['UserService', 'AuthService']")
            else:
                # 检查服务命名规范
                for service in services:
                    if not service.endswith("Service"):
                        score -= 5
                        issues.append(f"服务类命名不规范: {service}")
                        suggestions.append("服务类应以 'Service' 结尾")
            
            metrics['services_count'] = len(services)
            metrics['repositories_count'] = len(implementation.get("repositories", []))
            metrics['controllers_count'] = len(implementation.get("controllers", []))
        
        # 4. 检查API设计
        api_design = summary.get("api_design", {})
        if isinstance(api_design, dict):
            endpoints = api_design.get("endpoints", [])
            if isinstance(endpoints, list):
                valid_endpoints = 0
                for endpoint in endpoints:
                    if isinstance(endpoint, dict):
                        if endpoint.get("method") and endpoint.get("path"):
                            valid_endpoints += 1
                        else:
                            issues.append("API端点缺少method或path")
                
                if valid_endpoints == 0 and len(endpoints) > 0:
                    score -= 10
                    issues.append("API端点定义不完整")
                
                metrics['api_endpoints_count'] = valid_endpoints
        
        # 5. 检查描述的具体性
        description = str(summary.get("description", ""))
        if description:
            text_report = cls.validate_text(description, "general")
            if text_report.level == QualityLevel.POOR:
                score -= 10
                issues.append("描述过于空泛")
                issues.extend(text_report.issues)
        
        # 6. 检查是否有空数组或空对象
        empty_collections = []
        
        def check_empty(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if isinstance(value, (dict, list)) and not value:
                        empty_collections.append(new_path)
                    check_empty(value, new_path)
            elif isinstance(obj, list):
                if not obj:
                    empty_collections.append(path)
        
        check_empty(summary)
        
        if len(empty_collections) > 3:
            score -= 5 * (len(empty_collections) - 3)
            issues.append(f"存在 {len(empty_collections)} 个空集合")
            suggestions.append("填充空的数组和对象，或移除不需要的字段")
        
        metrics['empty_collections'] = len(empty_collections)
        
        # 确保分数在有效范围内
        score = max(0, min(100, score))
        
        # 确定质量等级
        if score >= 90:
            level = QualityLevel.EXCELLENT
        elif score >= 70:
            level = QualityLevel.GOOD
        elif score >= 50:
            level = QualityLevel.FAIR
        else:
            level = QualityLevel.POOR
        
        return QualityReport(
            score=score,
            level=level,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics
        )
    
    @classmethod
    def suggest_improvements(cls, text: str, target_score: int = 80) -> List[str]:
        """
        基于当前文本提供具体的改进建议。
        
        Args:
            text: 当前文本
            target_score: 目标分数
            
        Returns:
            List[str]: 改进建议列表
        """
        report = cls.validate_text(text)
        improvements = []
        
        if report.score >= target_score:
            improvements.append(f"当前质量已达标（{report.score}分）")
            return improvements
        
        # 基于问题生成具体改进建议
        improvements.extend(report.suggestions)
        
        # 添加具体示例
        if "缺少具体的类名" in str(report.issues):
            improvements.append(
                "示例改进：将 '处理用户数据' 改为 "
                "'UserService 类包含 createUser(), updateUser(), deleteUser() 方法'"
            )
        
        if "缺少版本号" in str(report.issues):
            improvements.append(
                "示例改进：将 '使用Spring框架' 改为 '使用Spring Boot 2.7.0 + Spring Security 5.7.0'"
            )
        
        return improvements

# 便捷函数
def validate_quality(content: Any, content_type: str = "text") -> Tuple[int, List[str]]:
    """
    验证内容质量的便捷函数。
    
    Args:
        content: 要验证的内容（文本或JSON）
        content_type: 内容类型（text, json）
        
    Returns:
        Tuple[int, List[str]]: (质量分数, 问题列表)
    """
    if content_type == "json":
        report = QualityValidator.validate_json_summary(content)
    else:
        report = QualityValidator.validate_text(str(content))
    
    return report.score, report.issues

def is_high_quality(content: Any, min_score: int = 70) -> bool:
    """
    检查内容是否达到质量标准。
    
    Args:
        content: 要检查的内容
        min_score: 最低分数要求
        
    Returns:
        bool: 是否达到质量标准
    """
    score, _ = validate_quality(content)
    return score >= min_score