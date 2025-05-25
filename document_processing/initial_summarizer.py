from common import print_log
"""
初始摘要生成模块。
负责从文档中为识别的实体生成初始结构化摘要。
该模块专注于基础摘要生成，不包含多轮推理的增强部分。
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional

from llm_services.executor import run_prompt
from document_processing.content_analyzer import analyze_document_content

# 配置日志
logger = logging.getLogger(__name__)

# 完整摘要模式定义
FULL_SUMMARY_SCHEMA = {
  "module": "string - 模块名称",
  "description": "string - 模块目的简述",
  "frontend": {
    "pages": ["string - 页面路径"],
    "components": ["string - 组件名称"],
    "apiHooks": ["string - API钩子"],
    "routes": ["string - 路由定义"]
  },
  "backend": {
    "controllers": ["string - 控制器名称"],
    "services": ["string - 服务名称"],
    "repositories": ["string - 仓储名称"],
    "dtos": {
      "DtoName": {
        "fields": ["string - 字段名称和类型"]
      }
    },
    "api": ["string - API端点"],
    "database": {
      "tables": ["string - 表名"],
      "indexes": ["string - 索引"]
    }
  },
  "dependencies": ["string - 依赖项"],
  "events": {
    "emit": ["string - 发出的事件"],
    "listen": ["string - 监听的事件"]
  },
  "test": {
    "unit": ["string - 单元测试"],
    "e2e": ["string - 端到端测试"]
  }
}

SYSTEM_PROMPT = """你是一个专业的软件架构分析工具，你的任务是从文档中提取关于软件实体的详细信息并生成结构化JSON。
你需要尽可能地发掘相关信息，不要留下空字段。如果上下文中没有明确提到某个字段，请根据架构做合理推测。
你的目标是创建一个包含丰富详细信息的结构化摘要，这将用于生成全面的软件架构文档。
只返回有效的JSON对象，并用```json和```包裹。"""

def get_user_prompt(entity, schema, context):
    """
    构建用户提示
    
    Args:
        entity: 实体信息
        schema: 模式定义
        context: 上下文信息
        
    Returns:
        str: 格式化的用户提示
    """
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

上下文信息：
{context}

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
    """
    创建一个带有entity信息的解析函数闭包
    
    Args:
        entity_info: 实体信息
        
    Returns:
        function: 解析函数
    """
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
                print_log(f"JSON代码块解析失败: {e}")
        
        # 尝试查找大括号包含的完整JSON
        json_pattern = re.search(r'(\{[\s\S]*\})', text, re.DOTALL)
        if json_pattern:
            try:
                json_content = json_pattern.group(1).strip()
                return json.loads(json_content)
            except Exception as e:
                print_log(f"JSON对象解析失败: {e}")
        
        # 所有解析尝试失败，返回默认结构并填充尽可能多的信息
        print_log("无法解析JSON，返回默认结构")
        
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

async def generate_initial_summary(entity: Dict[str, str], context: str) -> Dict[str, Any]:
    """
    为实体生成初始结构化摘要
    
    Args:
        entity: 实体信息
        context: 上下文信息
        
    Returns:
        Dict[str, Any]: 结构化摘要
    """
    print_log(f"📝 为实体 {entity.get('name', 'unknown')} 生成初始摘要...")
    
    # 分析文档内容以增强上下文
    try:
        content_analysis = await analyze_document_content(context)
        
        # 使用内容分析结果增强上下文
        enhanced_context = f"""
原始上下文:
{context}

文档分析结果:
主题: {content_analysis.get('topic', '')}
目的: {content_analysis.get('purpose', '')}
架构描述: {content_analysis.get('architecture', '')}

主要组件:
{json.dumps(content_analysis.get('components', []), indent=2, ensure_ascii=False)}

关键术语:
{json.dumps(content_analysis.get('technicalTerms', []), indent=2, ensure_ascii=False)}

依赖关系:
{', '.join(content_analysis.get('dependencies', []))}
"""
    except Exception as e:
        logger.warning(f"内容分析失败，使用原始上下文: {e}")
        enhanced_context = context
    
    # 准备schema
    schema_json = json.dumps(FULL_SUMMARY_SCHEMA, indent=2, ensure_ascii=False)
    
    # 准备解析函数
    parse_function = create_parse_function(entity)
    
    # 生成用户提示
    user_prompt = get_user_prompt(entity, schema_json, enhanced_context)
    
    # 调用LLM
    initial_summary = await run_prompt(
        system_message=SYSTEM_PROMPT,
        user_message=user_prompt,
        model="gpt-4o",
        max_input_tokens=6000,
        parse_response=parse_function
    )
    
    # 格式验证和基础字段补全
    initial_summary = _validate_and_complete_summary(initial_summary, entity)
    
    print_log(f"初始摘要生成完成: {entity.get('name', 'unknown')}", level="info")
    return initial_summary

def _validate_and_complete_summary(summary: Dict[str, Any], entity: Dict[str, str]) -> Dict[str, Any]:
    """
    验证并补全摘要中的基础字段
    
    Args:
        summary: 生成的摘要
        entity: 实体信息
        
    Returns:
        Dict[str, Any]: 补全后的摘要
    """
    # 确保顶级字段存在
    if not summary:
        summary = {}
    
    # 确保module字段存在
    if not summary.get("module"):
        entity_name = entity.get("name", "unknown")
        if "/" in entity_name:
            # 如果是路径形式，使用第一部分作为模块名
            summary["module"] = entity_name.split("/")[0]
        else:
            summary["module"] = entity_name
    
    # 确保description字段存在
    if not summary.get("description"):
        entity_type = entity.get("type", "Component")
        entity_name = entity.get("name", "unknown")
        summary["description"] = f"{entity_type} for {entity_name}"
    
    # 确保frontend和backend结构存在
    if "frontend" not in summary:
        summary["frontend"] = {"pages": [], "components": [], "apiHooks": [], "routes": []}
    
    if "backend" not in summary:
        summary["backend"] = {"controllers": [], "services": [], "repositories": [], "dtos": {}, "api": []}
    
    # 对于模型类型的实体，添加空数据库结构
    if entity.get("type") in ["Model", "Entity", "DTO"] and "database" not in summary.get("backend", {}):
        summary["backend"]["database"] = {"tables": [], "indexes": []}
    
    # 确保其他顶级属性存在
    for key in ["dependencies", "events", "test"]:
        if key not in summary:
            if key == "events":
                summary[key] = {"emit": [], "listen": []}
            elif key == "test":
                summary[key] = {"unit": [], "e2e": []}
            else:
                summary[key] = []
    
    return summary

def _identify_empty_sections(summary: Dict[str, Any]) -> List[str]:
    """
    识别摘要中的空白部分
    
    Args:
        summary: 摘要
        
    Returns:
        List[str]: 空部分的路径列表
    """
    empty_sections = []
    
    def check_empty(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict) and not value:
                    empty_sections.append(new_path)
                elif isinstance(value, list) and not value:
                    empty_sections.append(new_path)
                else:
                    check_empty(value, new_path)
        elif isinstance(obj, list) and not obj:
            empty_sections.append(path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_empty(item, f"{path}[{i}]")
    
    check_empty(summary)
    return empty_sections 