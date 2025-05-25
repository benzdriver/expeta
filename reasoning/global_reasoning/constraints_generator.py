from common import print_log
"""
全局约束生成器模块。
负责生成系统级全局约束，包括命名和编码规范、接口标准、通信协议等。
基于系统分析和架构风格选择，为所有模块提供一致的指导和约束。
"""

import json
from typing import Dict, List, Any, Optional

from llm_services.executor import run_prompt

SYSTEM_PROMPT = """你是一个专业的软件架构师，专门负责制定系统全局约束和架构规范。
你需要基于系统分析和架构风格，生成详细的约束指南，包括命名规范、接口标准、通信协议等。
这些约束将确保整个系统的一致性和可维护性。
只输出JSON格式的约束结果，不要有任何解释或附加内容。"""

async def generate_constraints(system_analysis: Dict[str, Any], architecture_style: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成全局架构约束
    
    Args:
        system_analysis: 系统分析结果
        architecture_style: 架构风格建议
        
    Returns:
        Dict[str, Any]: 全局约束规范
    """
    print_log("📏 开始生成全局约束...")
    
    prompt = f"""基于以下系统分析和架构风格，生成全面的全局约束和规范:

系统分析:
```json
{json.dumps(system_analysis, indent=2, ensure_ascii=False)}
```

架构风格:
```json
{json.dumps(architecture_style, indent=2, ensure_ascii=False)}
```

请制定以下方面的约束:
1. 命名规范(文件、类、方法、变量等)
2. 代码组织和结构规范
3. 接口设计标准
4. API请求/响应格式
5. 错误处理和日志规范
6. 通信协议和数据交换格式
7. 安全规范
8. 性能要求
9. 测试策略
10. 文档规范
11. 架构分层与依赖规则（特别注重避免循环依赖）

返回JSON格式:
```json
{{
  "namingConventions": {{
    "files": "文件命名规则",
    "classes": "类命名规则",
    "methods": "方法命名规则",
    "variables": "变量命名规则",
    "constants": "常量命名规则",
    "database": "数据库相关命名规则",
    "examples": ["示例1", "示例2"]
  }},
  "codeOrganization": {{
    "directoryStructure": "目录结构规范",
    "fileStructure": "文件结构规范",
    "modulePatterns": "模块组织模式",
    "importRules": "导入规则"
  }},
  "interfaceStandards": {{
    "definition": "接口定义方式",
    "versioning": "版本管理策略",
    "documentation": "文档要求",
    "examples": ["示例1", "示例2"]
  }},
  "apiConventions": {{
    "requestFormat": "请求格式",
    "responseFormat": "响应格式",
    "statusCodes": "状态码使用规范",
    "pagination": "分页处理",
    "filtering": "过滤与排序"
  }},
  "errorHandling": {{
    "strategy": "错误处理策略",
    "loggingLevel": "日志级别规范",
    "exceptionHierarchy": "异常层次结构",
    "userFeedback": "用户反馈机制"
  }},
  "communicationProtocols": {{
    "internalCommunication": "内部通信协议",
    "externalCommunication": "外部通信协议",
    "messageFormats": "消息格式",
    "synchronization": "同步机制"
  }},
  "security": {{
    "authentication": "认证规范",
    "authorization": "授权规范",
    "dataProtection": "数据保护措施",
    "inputValidation": "输入验证要求"
  }},
  "performance": {{
    "responseTimes": "响应时间要求",
    "throughput": "吞吐量要求",
    "scalability": "可扩展性设计",
    "resourceUsage": "资源使用限制"
  }},
  "testingStrategy": {{
    "unitTesting": "单元测试要求",
    "integrationTesting": "集成测试策略",
    "coverageRequirements": "覆盖率要求",
    "testingTools": "推荐测试工具"
  }},
  "documentation": {{
    "codeComments": "代码注释规范",
    "apiDocumentation": "API文档要求",
    "architectureDocuments": "架构文档规范",
    "changeLog": "变更日志规范"
  }},
  "architectureLayers": {{
    "layerDefinition": "系统层次结构定义",
    "dependencyRules": "跨层依赖规则",
    "circularDependencyPrevention": "循环依赖预防策略",
    "layerResponsibilities": "各层职责边界"
  }}
}}
```

请确保约束符合所选架构风格，并具有足够的细节指导开发团队。"""

    result = await run_prompt(
        system_message=SYSTEM_PROMPT,
        user_message=prompt,
        model="gpt-4o",
        max_input_tokens=8000,
        parse_response=_parse_json_response
    )
    
    # 转换为架构章程格式
    charter = await _convert_to_architecture_charter(result, system_analysis, architecture_style)
    
    print_log(f"全局约束生成完成", level="info")
    return charter

async def generate_module_guidelines(constraints: Dict[str, Any], module_type: str) -> Dict[str, Any]:
    """
    基于全局约束生成特定类型模块的指导原则
    
    Args:
        constraints: 全局约束
        module_type: 模块类型(如 "frontend", "backend", "api", "database")
        
    Returns:
        Dict[str, Any]: 模块指导原则
    """
    print_log(f"📋 开始生成{module_type}模块指导原则...")
    
    prompt = f"""基于以下全局架构约束，生成{module_type}模块的详细指导原则:

全局约束:
```json
{json.dumps(constraints, indent=2, ensure_ascii=False)}
```

请为{module_type}模块制定:
1. 特定命名规范
2. 结构组织方式
3. 代码实现模式
4. 测试要求
5. 与其他模块的集成方式
6. 特定文档要求
7. 示例和最佳实践

返回JSON格式:
```json
{{
  "moduleType": "{module_type}",
  "namingRules": {{
    "specific": "特定命名规则",
    "examples": ["示例1", "示例2"]
  }},
  "structure": {{
    "organization": "组织方式",
    "keyComponents": ["组件1", "组件2"]
  }},
  "patterns": [
    {{
      "name": "模式名称",
      "purpose": "用途",
      "implementation": "实现指南"
    }}
  ],
  "testingGuidelines": {{
    "approach": "测试方法",
    "coverage": "覆盖要求"
  }},
  "integration": {{
    "interfaces": "接口规范",
    "dataFlow": "数据流规范"
  }},
  "documentation": "文档要求",
  "bestPractices": ["最佳实践1", "最佳实践2"],
  "antiPatterns": ["反模式1", "反模式2"]
}}
```

请确保指导原则详细、具体且实用，帮助开发人员统一实现方式。"""

    result = await run_prompt(
        system_message=SYSTEM_PROMPT,
        user_message=prompt,
        model="gpt-4o",
        max_input_tokens=6000,
        parse_response=_parse_json_response
    )
    
    print_log(f"{module_type}模块指导原则生成完成", level="info")
    return result

async def _convert_to_architecture_charter(constraints: Dict[str, Any], 
                                          system_analysis: Dict[str, Any], 
                                          architecture_style: Dict[str, Any]) -> Dict[str, Any]:
    """
    将约束转换为架构章程格式
    
    Args:
        constraints: 生成的约束
        system_analysis: 系统分析
        architecture_style: 架构风格
        
    Returns:
        Dict[str, Any]: 架构章程
    """
    charter = {
        "systemOverview": {
            "type": system_analysis.get("systemType", ""),
            "domain": system_analysis.get("domain", ""),
            "scale": system_analysis.get("systemScale", ""),
            "users": system_analysis.get("users", [])
        },
        "architectureDecisions": {
            "style": architecture_style.get("architectureStyle", ""),
            "justification": architecture_style.get("justification", ""),
            "frontendStack": architecture_style.get("frontendStack", []),
            "backendStack": architecture_style.get("backendStack", []),
            "dataStorage": architecture_style.get("dataStorage", [])
        },
        "constraints": constraints,
        "versionHistory": [
            {
                "version": "1.0",
                "date": "自动生成",
                "description": "初始版本"
            }
        ]
    }
    
    return charter

def _parse_json_response(text: str) -> Any:
    """解析LLM返回的JSON响应"""
    import json
    import re
    
    # 尝试从代码块中提取JSON
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            print_log(f"从代码块提取JSON失败")
    
    # 尝试提取整个JSON对象
    json_pattern = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text, re.DOTALL)
    if json_pattern:
        try:
            return json.loads(json_pattern.group(1).strip())
        except json.JSONDecodeError:
            print_log(f"从文本提取JSON失败")
    
    # 返回原始文本
    print_log("无法解析JSON，返回原始文本")
    return {"error": "无法解析响应", "original": text} 