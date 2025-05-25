from common import print_log
"""
实体发现模块。
负责从软件文档中识别和提取各类软件实体，如API端点、服务、仓储层、模型等。
使用大语言模型进行智能识别和分类。
"""

import json
import re
from typing import List, Dict, Any

from llm_services.executor import run_prompt

SYSTEM_PROMPT = '''你是一个专业的软件架构分析工具，专门用于从软件设计文档中提取实体。
你的任务是识别所有API端点、服务、仓储层、工具类、数据模型等关键实体。
只输出JSON格式的实体列表，不要有任何解释或附加内容。'''

def get_entity_discovery_prompt(doc_text: str, chunk_index: int = None, total_chunks: int = None) -> str:
    """
    构建实体发现的提示。
    
    Args:
        doc_text: 文档内容
        chunk_index: 当前分块索引
        total_chunks: 总分块数
        
    Returns:
        str: 格式化的提示
    """
    chunk_info = ""
    if chunk_index is not None and total_chunks is not None:
        chunk_info = f"这是整个文档的第{chunk_index}个分块，共{total_chunks}个分块。仅分析此分块中的内容。\n\n"
    
    return f'''{chunk_info}分析以下文档，识别所有软件实体（API端点、服务、仓储层、工具类等）。

文档内容：
{doc_text}

输出要求：
1. 使用JSON数组格式
2. 每个实体包含name（名称）、type（类型）、parent（所属模块）字段
3. 使用code block包裹JSON (```json)
4. 不要有任何解释或额外文本

示例：
```json
[{"name": "auth/login", "type": "Function", "parent": "Auth"}]
```'''

def parse_entity_list(text: str) -> List[Dict[str, str]]:
    """
    解析LLM返回的实体列表文本。
    
    Args:
        text: LLM返回的文本
        
    Returns:
        List[Dict[str, str]]: 解析后的实体列表
    """
    print("LLM原始返回：", text)
    # 尝试找到JSON部分
    json_match = re.search(r'```json\n(.*?)\n```|```(.*?)```|\[.*\]', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1) or json_match.group(2) or json_match.group(0)
        json_str = json_str.strip()
        print("提取的JSON：", json_str)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print_log(f"JSON解析错误：{e}")
            # 返回空列表而不是抛出异常
            print_log("返回空列表以继续处理")
            return []
    else:
        print_log("未找到有效的JSON内容，返回空列表以继续处理")
        return []

def merge_entities(accumulated_result: List[Dict[str, str]], new_result: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    合并两组实体列表，用于分块处理。
    
    Args:
        accumulated_result: 已积累的实体列表
        new_result: 新的实体列表
        
    Returns:
        List[Dict[str, str]]: 合并后的实体列表
    """
    if accumulated_result is None:
        return new_result
    if not new_result:
        return accumulated_result
    return accumulated_result + new_result

async def discover_entities(all_text: str) -> List[Dict[str, str]]:
    """
    从文档中发现所有实体，支持大型文档分块处理。
    
    Args:
        all_text: 文档内容
    
    Returns:
        List[Dict[str, str]]: 实体列表
    """
    print_log("📚 开始实体发现...")
    
    # 使用run_prompt进行自动分块处理
    entities = await run_prompt(
        user_message=all_text,
        system_message=SYSTEM_PROMPT,
        model="gpt-4o",
        max_input_tokens=4000,  # 使用更大的分块大小
        parse_response=parse_entity_list,
        merge_result=merge_entities,
        get_system_prompt=lambda chunk_idx, total_chunks: SYSTEM_PROMPT + f"\n\n这是文档的第{chunk_idx}个分块，共{total_chunks}个分块。仅分析此分块中的内容。"
    )
    
    # 去重处理
    unique_entities = []
    seen = set()
    for entity in entities:
        entity_key = f"{entity.get('name')}|{entity.get('type')}|{entity.get('parent')}"
        if entity_key not in seen:
            seen.add(entity_key)
            unique_entities.append(entity)
    
    print_log(f"🔍 实体发现完成: 原始实体数={len(entities)}, 去重后={len(unique_entities)}")
    return unique_entities 