from llm.llm_executor import run_prompt as llm_run_prompt
from llm_v2.executor import run_prompt as llm_v2_run_prompt
from llm.chat_openai import chat
import tiktoken
import json
import re

tokenizer = tiktoken.encoding_for_model("gpt-4o")

SYSTEM_PROMPT = """你是一个专业的软件架构分析工具，你的任务是从文档中提取关于软件实体的详细信息并生成结构化JSON。
你需要尽可能地发掘相关信息，不要留下空字段。如果上下文中没有明确提到某个字段，请根据架构做合理推测。
你的目标是创建一个包含丰富详细信息的结构化摘要，这将用于生成全面的软件架构文档。
只返回有效的JSON对象，并用```json和```包裹。"""

def get_user_prompt(entity, schema):
    # 获取实体名称、类型和所属模块，处理可能缺失的字段
    entity_name = entity.get('name', 'unknown')
    entity_type = entity.get('type', 'unknown')
    entity_parent = entity.get('parent', None)
    
    # 构建实体描述部分
    entity_info = f"实体名称：{entity_name}\n实体类型：{entity_type}"
    if entity_parent:
        entity_info += f"\n所属模块：{entity_parent}"
    
    return f"""请为以下实体生成一个符合schema的丰富JSON结构：
{entity_info}

schema格式：
{schema}

详细需求：
1. 请从上下文中提取尽可能多的信息填充到JSON结构中
2. 对于没有明确提到的字段，请根据常见架构模式做合理推测
3. 尽量避免返回空数组[]或空对象{{}}，填充可能的值
4. 考虑实体名称和类型，推断其可能的前端组件、API端点、服务和关联
5. 特别关注：
   - 前端的页面、组件和路由
   - 后端的控制器、服务和仓储
   - 数据模型和字段
   - API端点和依赖关系

使用```json和```包裹你的答案。不要有任何解释或额外内容。"""

def create_parse_function(entity_info):
    """创建一个带有entity信息的解析函数闭包"""
    def parse_structured_summary(text):
        print("LLM原始返回：", text)
        
        # 创建默认返回结构
        default_json = {
            "module": "unknown",
            "description": "自动生成的描述",
            "frontend": {"pages": [], "components": [], "apiHooks": [], "routes": []},
            "backend": {"controllers": [], "services": [], "repositories": [], "dtos": {}, "api": []}
        }
        
        # 尝试提取JSON代码块
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                json_content = json_match.group(1).strip()
                # 移除可能的注释
                json_content = re.sub(r'(?m)^\s*//.*$', '', json_content)
                return json.loads(json_content)
            except Exception as e:
                print(f"JSON代码块解析失败: {e}")
        
        # 尝试查找大括号包含的完整JSON
        json_pattern = re.search(r'(\{[\s\S]*\})', text, re.DOTALL)
        if json_pattern:
            try:
                json_content = json_pattern.group(1).strip()
                return json.loads(json_content)
            except Exception as e:
                print(f"JSON对象解析失败: {e}")
        
        # 所有解析尝试失败，返回默认结构并填充尽可能多的信息
        print("无法解析JSON，返回默认结构")
        
        # 尝试提取模块名
        if 'name' in entity_info:
            parts = entity_info['name'].split('/')
            if len(parts) > 0:
                default_json["module"] = parts[0]
        
        # 尝试提取描述
        desc_match = re.search(r'description["\s:]+([^"]+)', text, re.IGNORECASE)
        if desc_match:
            default_json["description"] = desc_match.group(1).strip()
        else:
            if 'type' in entity_info and 'name' in entity_info:
                default_json["description"] = f"{entity_info['type']} for {entity_info['name']}"
        
        return default_json
    
    return parse_structured_summary

async def summarize_entity(entity, context, schema):
    print("[DEBUG] summarize_entity: entity=", entity)
    print("[DEBUG] summarize_entity: context=", context[:100], "..." if len(context) > 100 else "")
    print("[DEBUG] summarize_entity: schema=", schema[:100], "..." if len(schema) > 100 else "")
    
    user_prompt = get_user_prompt(entity, schema)
    parse_function = create_parse_function(entity)
    
    summary = await llm_v2_run_prompt(
        system_message=SYSTEM_PROMPT,
        user_message=user_prompt,
        model="gpt-4o",
        max_input_tokens=2000,
        parse_response=parse_function
    )
    
    print("[DEBUG] summarize_entity: summary=", summary)
    return summary 