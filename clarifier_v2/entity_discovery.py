from llm.llm_executor import run_prompt as llm_run_prompt
from llm_v2.executor import run_prompt as llm_v2_run_prompt
from llm.chat_openai import chat
import tiktoken
import json
import re

tokenizer = tiktoken.encoding_for_model("gpt-4o")

SYSTEM_PROMPT = '''你是一个专业的软件架构分析工具，专门用于从软件设计文档中提取实体。
你的任务是识别所有API端点、服务、仓储层、工具类、数据模型等关键实体。
只输出JSON格式的实体列表，不要有任何解释或附加内容。'''

def get_entity_discovery_prompt(doc_text: str, chunk_index: int = None, total_chunks: int = None) -> str:
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

def parse_entity_list(text: str):
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
            print(f"JSON解析错误：{e}")
            # 返回空列表而不是抛出异常
            print("返回空列表以继续处理")
            return []
    else:
        print("未找到有效的JSON内容，返回空列表以继续处理")
        return []

def merge_entities(accumulated_result, new_result):
    """合并两组实体列表，用于分块处理"""
    if accumulated_result is None:
        return new_result
    if not new_result:
        return accumulated_result
    return accumulated_result + new_result

async def discover_entities(all_text: str):
    """
    从文档中发现所有实体，支持大型文档分块处理
    
    Args:
        all_text: 文档内容
    
    Returns:
        实体列表
    """
    print("📚 开始实体发现...")
    
    # 使用llm_v2的run_prompt进行自动分块处理
    entities = await llm_v2_run_prompt(
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
    
    print(f"🔍 实体发现完成: 原始实体数={len(entities)}, 去重后={len(unique_entities)}")
    return unique_entities 