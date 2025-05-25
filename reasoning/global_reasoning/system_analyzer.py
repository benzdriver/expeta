from common import print_log
"""
系统分析器模块。
负责分析整体系统类型、领域特点、主要用户群体和核心用例。
根据文档内容确定系统的规模和复杂度，为后续架构决策提供基础。
"""

import json
from typing import Dict, List, Any, Optional

from llm_services.executor import run_prompt
from document_processing.content_analyzer import analyze_document_content
from knowledge.context_retrieval import retrieve_similar_systems

SYSTEM_PROMPT = """你是一个专业的软件架构分析专家，专门负责识别和分析软件系统的整体类型和特征。
你需要根据文档内容深入分析系统的领域、规模、复杂度和核心需求。
你的分析将为后续架构决策提供重要基础。
只输出JSON格式的分析结果，不要有任何解释或附加内容。"""

async def analyze_system_type(document_text: str) -> Dict[str, Any]:
    """
    分析系统类型和关键特征
    
    Args:
        document_text: 文档内容
        
    Returns:
        Dict[str, Any]: 系统分析结果
    """
    print_log("🔍 开始系统类型分析...")
    
    # 先使用内容分析器提取关键信息
    content_analysis = await analyze_document_content(document_text)
    
    prompt = f"""分析以下软件文档，确定系统的类型和关键特征:

文档内容:
{document_text}

请分析以下方面:
1. 系统类型(如企业应用、Web平台、移动应用、嵌入式系统等)
2. 所属领域和行业
3. 主要用户群体
4. 核心用例和业务流程
5. 系统规模和复杂度
6. 关键技术挑战
7. 运行环境和部署要求
8. 关键质量属性(如可用性、可扩展性、安全性等)

返回JSON格式:
```json
{{
  "systemType": "系统类型",
  "domain": "所属领域",
  "users": ["用户群体1", "用户群体2"],
  "coreUseCases": ["核心用例1", "核心用例2"],
  "systemScale": "规模描述",
  "complexity": "复杂度评估",
  "technicalChallenges": ["技术挑战1", "技术挑战2"],
  "deploymentEnvironment": "部署环境",
  "qualityAttributes": [
    {{
      "attribute": "质量属性",
      "importance": "重要性",
      "justification": "理由"
    }}
  ]
}}
```

请确保分析全面且基于文档提供的实际信息。对不确定的内容，可以适当推断但要合理。"""

    # 使用自定义解析器处理LLM响应
    result = await run_prompt(
        system_message=SYSTEM_PROMPT,
        user_message=prompt,
        model="gpt-4o",
        max_input_tokens=6000,
        parse_response=_parse_json_response
    )
    
    # 增强分析结果
    enhanced_result = await _enhance_analysis_with_similar_systems(result)
    
    print_log(f"系统类型分析完成", level="info")
    return enhanced_result

async def determine_architecture_style(system_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    基于系统分析结果确定适合的架构风格，并生成初始模块列表及依赖关系
    
    Args:
        system_analysis: 系统分析结果
        
    Returns:
        Dict[str, Any]: 包含架构风格建议和初始模块列表的结果
    """
    print_log("🏗️ 开始架构风格确定...")
    
    prompt = f"""基于以下系统分析结果，推荐最适合的架构风格并识别核心系统模块:

系统分析:
```json
{json.dumps(system_analysis, indent=2, ensure_ascii=False)}
```

请完成以下任务:
1. 确定整体架构风格(如微服务、单体、前后端分离、事件驱动等)
2. 推荐前后端技术栈、数据存储方案等技术选型
3. 识别系统中的核心模块，并为每个模块提供简短描述
4. 明确模块之间的初始依赖关系

返回JSON格式:
```json
{{
  "architectureStyle": "架构风格",
  "justification": "选择理由",
  "alternatives": ["备选方案1", "备选方案2"],
  "frontendStack": ["技术1", "技术2"],
  "backendStack": ["技术1", "技术2"],
  "dataStorage": ["存储方案1", "存储方案2"],
  "communication": ["通信方式1", "通信方式2"],
  "deployment": "部署策略",
  "scalability": "扩展策略",
  "caveats": ["注意事项1", "注意事项2"],
  "modules": [
    {{
      "name": "模块名称",
      "description": "模块简短描述",
      "responsibilities": ["职责1", "职责2"],
      "layer": "架构层次(如presentation, application, domain, infrastructure)",
      "depends_on": ["依赖模块1", "依赖模块2"]
    }}
  ]
}}
```

请确保建议符合系统特性并基于现代最佳实践。考虑系统规模、复杂度、质量属性和技术挑战。

请确保模块列表全面覆盖系统的核心功能，并明确指出模块间的依赖关系。依赖关系应符合良好的架构分层原则，如上层模块依赖下层模块，避免循环依赖。"""

    # 获取架构风格建议
    result = await run_prompt(
        system_message=SYSTEM_PROMPT,
        user_message=prompt,
        model="gpt-4o",
        max_input_tokens=6000,
        parse_response=_parse_json_response
    )
    
    print_log(f"架构风格确定完成", level="info")
    return result

async def _enhance_analysis_with_similar_systems(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    通过检索类似系统的信息增强分析结果
    
    Args:
        analysis: 初步分析结果
        
    Returns:
        Dict[str, Any]: 增强后的分析结果
    """
    try:
        # 使用系统类型和领域检索类似系统
        system_type = analysis.get("systemType", "")
        domain = analysis.get("domain", "")
        query = f"system type: {system_type}, domain: {domain}"
        
        # 注意：retrieve_similar_systems 是同步函数，不需要 await
        similar_systems = retrieve_similar_systems(query, top_k=3)
        
        if similar_systems:
            # 如果找到类似系统，添加到分析结果中
            analysis["similarSystems"] = similar_systems
    except Exception as e:
        print_log(f"增强分析结果时出错: {e}")
    
    return analysis

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

# 为兼容测试添加analyze_system函数
async def analyze_system(document_content: str) -> Dict[str, Any]:
    """
    分析系统特征并返回结果(兼容测试用例)
    
    Args:
        document_content: 文档内容
        
    Returns:
        Dict[str, Any]: 系统分析结果
    """
    # 调用真正的实现
    system_type = await analyze_system_type(document_content)
    architecture_style = await determine_architecture_style(system_type)
    
    # 组合结果
    result = {
        "systemAnalysis": system_type,
        "architectureRecommendation": architecture_style
    }
    
    return result 