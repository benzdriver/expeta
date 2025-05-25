from common import print_log
"""
内容分析模块。
负责从文档中分析提取关键信息，如主题、关键概念、重要段落等。
提供上下文理解，为后续处理步骤准备数据。
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from llm_services.executor import run_prompt

SYSTEM_PROMPT = """你是一个专业的软件文档分析助手，专门帮助分析软件设计文档。
你的任务是从文档中提取关键信息，如主题、重要概念、核心功能描述等。
你需要识别文档的结构，并提取最有价值的内容，为后续处理提供精确的上下文。
只返回JSON格式的分析结果，不要有任何解释或附加内容。"""

async def analyze_document_content(document_text: str) -> Dict[str, Any]:
    """
    分析文档内容，提取关键信息
    
    Args:
        document_text: 文档内容
        
    Returns:
        Dict[str, Any]: 包含分析结果的字典
    """
    print_log("📊 开始分析文档内容...")
    
    prompt = f"""分析以下软件文档，提取关键信息:

文档内容:
{document_text}

请提取以下信息:
1. 文档主题和目的
2. 主要软件组件/模块
3. 关键技术术语及其含义
4. 架构相关描述
5. 功能需求要点
6. 非功能需求(如性能、安全性等)
7. 依赖关系
8. 重要段落位置及内容概述

以JSON格式返回结果:
```json
{{
  "topic": "文档主题",
  "purpose": "文档目的",
  "components": [
    {{
      "name": "组件名称",
      "description": "组件描述"
    }}
  ],
  "technicalTerms": [
    {{
      "term": "术语",
      "meaning": "含义"
    }}
  ],
  "architecture": "架构描述",
  "functionalRequirements": ["功能需求1", "功能需求2"],
  "nonFunctionalRequirements": ["非功能需求1", "非功能需求2"],
  "dependencies": ["依赖1", "依赖2"],
  "keyPassages": [
    {{
      "location": "段落位置描述",
      "summary": "内容概述"
    }}
  ]
}}
```

注意:
- 如果某项信息文档中未提及，请使用空数组或空字符串
- 保持客观性，不要添加文档中未包含的信息
- 只返回JSON格式，不要有任何解释或额外内容"""

    # 使用自定义解析器处理LLM响应
    result = await run_prompt(
        system_message=SYSTEM_PROMPT,
        user_message=prompt,
        model="gpt-4o",
        max_input_tokens=6000,
        parse_response=_parse_json_response
    )
    
    print_log(f"文档内容分析完成", level="info")
    return result

async def extract_topic_sections(document_text: str) -> Dict[str, str]:
    """
    从文档中提取主题段落，按主题或章节进行区分
    
    Args:
        document_text: 文档内容
        
    Returns:
        Dict[str, str]: 以主题为键，段落内容为值的字典
    """
    print_log("📑 开始提取文档主题段落...")
    
    # 查找标题行（# 开头的Markdown标题）
    headers = re.findall(r'^(#{1,6})\s+(.+)$', document_text, re.MULTILINE)
    
    if not headers:
        # 如果没有找到Markdown标题，使用LLM进行智能分段
        sections = await _llm_based_section_extraction(document_text)
    else:
        # 基于Markdown标题构建段落
        sections = {}
        current_section = "Introduction"
        current_content = []
        
        lines = document_text.split('\n')
        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                # 保存上一部分
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                # 开始新部分
                current_section = header_match.group(2)
                current_content = []
            else:
                current_content.append(line)
        
        # 保存最后一部分
        if current_content:
            sections[current_section] = '\n'.join(current_content)
    
    print_log(f"识别出 {len(sections)} 个主题段落", level="info")
    return sections

async def identify_key_passages(document_text: str, max_passages: int = 5) -> List[Dict[str, str]]:
    """
    识别文档中的关键段落，对架构理解最重要的部分
    
    Args:
        document_text: 文档内容
        max_passages: 最多返回的关键段落数
        
    Returns:
        List[Dict[str, str]]: 关键段落列表，每个段落包含位置和内容
    """
    print_log("🔍 开始识别关键段落...")
    
    prompt = f"""从以下软件文档中识别最多{max_passages}个关键段落，这些段落对理解软件架构最为重要。

文档内容:
{document_text}

请按重要性排序，返回每个关键段落的位置描述和内容。返回JSON格式:

```json
[
  {{
    "location": "段落位置描述(如'第3章第2节'或'用户认证部分')",
    "content": "段落的完整内容",
    "importance": "为什么这个段落对架构理解很重要"
  }}
]
```

注意:
- 选择对理解系统架构、组件关系和设计决策最重要的段落
- 关注技术描述而非业务背景
- 只返回JSON格式，不要有任何解释或额外内容"""

    result = await run_prompt(
        system_message=SYSTEM_PROMPT,
        user_message=prompt,
        model="gpt-4o",
        max_input_tokens=6000,
        parse_response=_parse_json_response
    )
    
    print_log(f"识别出 {len(result) if isinstance(result, list) else 0} 个关键段落", level="info")
    return result if isinstance(result, list) else []

async def _llm_based_section_extraction(document_text: str) -> Dict[str, str]:
    """
    使用LLM智能分析文档并提取主题段落
    
    Args:
        document_text: 文档内容
        
    Returns:
        Dict[str, str]: 以主题为键，段落内容为值的字典
    """
    prompt = f"""分析以下软件文档，将其划分为有意义的主题段落。
即使文档没有明确的标题或章节，也请基于内容的逻辑结构进行划分。

文档内容:
{document_text}

返回一个JSON对象，其中键是主题名称，值是该主题的内容:
```json
{{
  "主题1": "主题1的完整内容...",
  "主题2": "主题2的完整内容...",
  ...
}}
```

注意:
- 每个主题应该有意义且自包含
- 主题名称应该简洁且描述性强
- 确保文档的所有内容都被包含
- 只返回JSON格式，不要有任何解释或额外内容"""

    sections = await run_prompt(
        system_message=SYSTEM_PROMPT,
        user_message=prompt,
        model="gpt-4o",
        max_input_tokens=6000,
        parse_response=_parse_json_response
    )
    
    return sections if isinstance(sections, dict) else {"全文": document_text}

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
    return text 