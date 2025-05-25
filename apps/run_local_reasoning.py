from common import print_log
#!/usr/bin/env python3
"""
运行局部架构推理。

该脚本加载实体摘要，对每个实体运行局部推理流程，生成丰富的架构设计。
"""

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledge.entity_storage import retrieve_entity, update_entity
from reasoning.local_reasoning.local_chain import run_full_local_reasoning
from document_processing.initial_summarizer import generate_initial_summary
from knowledge.entity_storage import store_entity_summary
from llm_services.rag import retrieve_context_for_entity

async def mock_retrieve_context(entity_name: str, all_text: str) -> str:
    """
    模拟上下文检索函数，用于在Qdrant服务不可用时提供简单的文本搜索
    
    Args:
        entity_name: 实体名称
        all_text: 全部文档内容
        
    Returns:
        str: 提取的上下文
    """
    print_log(f"使用简单文本搜索查找实体 {entity_name} 的上下文...")
    
    # 简单的上下文提取
    context = ""
    
    # 在文本中查找与实体名称相似的段落
    paragraphs = all_text.split("\n\n")
    relevant_paragraphs = []
    
    for paragraph in paragraphs:
        if entity_name.lower() in paragraph.lower() or "用户" in paragraph.lower() or "登录" in paragraph.lower() or "注册" in paragraph.lower() or "权限" in paragraph.lower():
            relevant_paragraphs.append(paragraph)
    
    if relevant_paragraphs:
        context = "\n\n".join(relevant_paragraphs)
        print_log(f"找到 {len(relevant_paragraphs)} 个相关段落", level="info")
    else:
        # 如果找不到相关段落，返回一些默认内容
        print_log("未找到相关段落，使用通用上下文", level="warning")
        context = all_text[:5000]  # 取前5000个字符作为上下文
    
    return context

async def mock_generate_initial_summary(entity: Dict[str, str], context: str) -> Dict[str, Any]:
    """
    模拟初始摘要生成，用于在API服务不可用时提供基础摘要
    
    Args:
        entity: 实体信息
        context: 上下文内容
        
    Returns:
        Dict[str, Any]: 初始摘要
    """
    entity_name = entity.get('name', 'unknown')
    print_log(f"为 {entity_name} 生成初始摘要...")
    
    # 从initial_modules.json中提取基础信息
    initial_modules_path = Path("data/output/architecture/initial_modules.json")
    if initial_modules_path.exists():
        try:
            with open(initial_modules_path, "r", encoding="utf-8") as f:
                modules = json.load(f)
            
            # 查找匹配的模块
            for module in modules:
                if module.get("name") == entity_name:
                    print_log(f"在初始模块中找到 {entity_name}", level="info")
                    
                    # 复制基本信息并扩展
                    summary = {
                        "name": entity_name,
                        "module": entity_name,
                        "description": module.get("description", ""),
                        "responsibilities": module.get("responsibilities", []),
                        "depends_on": module.get("depends_on", []),
                        "layer": module.get("layer", "application"),
                        "frontend": {
                            "pages": [],
                            "components": []
                        },
                        "backend": {
                            "controllers": [],
                            "services": []
                        }
                    }
                    
                    # 根据模块名称添加一些基本内容
                    if "用户管理" in entity_name:
                        summary["frontend"]["pages"] = ["登录页", "注册页", "个人资料页"]
                        summary["frontend"]["components"] = ["用户表单", "登录组件", "权限控制组件"]
                        summary["backend"]["controllers"] = ["用户控制器"]
                        summary["backend"]["services"] = ["认证服务", "用户服务"]
                    
                    return summary
        except Exception as e:
            print_log(f"从初始模块加载失败: {e}", level="warning")
    
    # 如果找不到相关模块或加载失败，返回通用模板
    print_log("使用通用模板生成初始摘要", level="warning")
    return {
        "name": entity_name,
        "module": entity_name,
        "description": "负责系统中的用户管理功能",
        "responsibilities": ["用户管理", "身份验证", "权限控制"],
        "depends_on": ["身份验证模块", "数据库模块"],
        "layer": "application",
        "frontend": {
            "pages": ["登录页", "注册页", "个人资料页"],
            "components": ["用户表单", "登录组件", "权限控制组件"]
        },
        "backend": {
            "controllers": ["用户控制器"],
            "services": ["认证服务", "用户服务"]
        }
    }

async def process_entity(
    entity: Dict[str, str], 
    all_text: str, 
    global_results: Dict[str, Any], 
    output_dir: str, 
    max_reasoning_rounds: int = 4
) -> Dict[str, Any]:
    """
    处理单个实体的详细架构推理
    
    Args:
        entity: 实体信息
        all_text: 文档内容
        global_results: 全局推理结果
        output_dir: 输出目录
        max_reasoning_rounds: 最大推理轮数
        
    Returns:
        Dict[str, Any]: 推理完成后的实体架构
    """
    entity_name = entity.get('name', 'unknown')
    entity_type = entity.get('type', 'unknown')
    
    print_log(f"\n🔍 开始处理实体: {entity_name} (类型: {entity_type})")
    
    # 查找相关上下文
    try:
        print_log(f"🔍 为实体 {entity_name} 检索上下文...")
        context = await retrieve_context_for_entity(entity_name, all_text)
    except Exception as e:
        print_log(f"上下文检索失败: {e}", level="warning")
        print_log(f"使用备用方法检索上下文...", level="info")
        context = await mock_retrieve_context(entity_name, all_text)
    
    # 生成初始摘要
    try:
        print_log(f"📝 为 {entity_name} 生成初始摘要...")
        initial_summary = await generate_initial_summary(entity, context)
    except Exception as e:
        print_log(f"初始摘要生成失败: {e}", level="warning")
        print_log(f"使用备用方法生成初始摘要...", level="info")
        initial_summary = await mock_generate_initial_summary(entity, context)
    
    # 运行局部推理链
    print_log(f"🧠 为 {entity_name} 执行多轮推理...")
    try:
        enhanced_summary = await run_full_local_reasoning(
            entity_name=entity_name,
            initial_summary=initial_summary,
            global_constraints=global_results.get("constraints", {}),
            max_rounds=max_reasoning_rounds
        )
    except Exception as e:
        print_log(f"局部推理失败: {e}", level="warning")
        print_log(f"使用初始摘要作为结果", level="info")
        enhanced_summary = initial_summary
    
    # 保存结果
    entity_dir = Path(output_dir) / _sanitize_path(entity_name)
    entity_dir.mkdir(parents=True, exist_ok=True)
    
    summary_path = entity_dir / "full_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(enhanced_summary, f, indent=2, ensure_ascii=False)
    
    # 生成Markdown版本
    md_path = entity_dir / "architecture.md"
    _generate_entity_markdown(entity, enhanced_summary, md_path)
    
    # 存储到知识库
    try:
        await store_entity_summary(entity_name, enhanced_summary)
    except Exception as e:
        print_log(f"存储实体摘要失败: {e}", level="warning")
    
    print_log(f"实体 {entity_name} 处理完成", level="info")
    return enhanced_summary

def _sanitize_path(path: str) -> str:
    """处理路径名，将可能的路径分隔符替换为下划线"""
    return path.replace('/', '_').replace('\\', '_')

def _generate_entity_markdown(entity: Dict[str, str], 
                             summary: Dict[str, Any], 
                             output_path: Path):
    """
    生成实体架构的Markdown文档
    
    Args:
        entity: 实体信息
        summary: 推理后的摘要
        output_path: 输出路径
    """
    entity_name = entity.get('name', 'unknown')
    entity_type = entity.get('type', 'unknown')
    
    markdown = f"""# {entity_name} 架构设计

## 基本信息

- **名称**: {entity_name}
- **类型**: {entity_type}
- **模块**: {summary.get('module', 'unknown')}

## 描述

{summary.get('description', '无描述')}

"""
    
    # 前端部分
    if 'frontend' in summary and any(summary['frontend'].values()):
        markdown += "## 前端设计\n\n"
        
        if summary['frontend'].get('pages'):
            markdown += "### 页面\n\n"
            for page in summary['frontend']['pages']:
                markdown += f"- {page}\n"
            markdown += "\n"
        
        if summary['frontend'].get('components'):
            markdown += "### 组件\n\n"
            for component in summary['frontend']['components']:
                markdown += f"- {component}\n"
            markdown += "\n"
    
    # 后端部分
    if 'backend' in summary and any(summary['backend'].values()):
        markdown += "## 后端设计\n\n"
        
        if summary['backend'].get('controllers'):
            markdown += "### 控制器\n\n"
            for controller in summary['backend']['controllers']:
                markdown += f"- {controller}\n"
            markdown += "\n"
        
        if summary['backend'].get('services'):
            markdown += "### 服务\n\n"
            for service in summary['backend']['services']:
                markdown += f"- {service}\n"
            markdown += "\n"
    
    # 依赖关系
    if 'depends_on' in summary and summary['depends_on']:
        markdown += "## 依赖关系\n\n"
        for dependency in summary['depends_on']:
            markdown += f"- {dependency}\n"
        markdown += "\n"
    
    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

async def process_entity_old(
    entity_name: str,
    initial_summary: Optional[Dict[str, Any]] = None,
    global_constraints: Optional[Dict[str, Any]] = None,
    max_rounds: int = 4
) -> Dict[str, Any]:
    """处理单个实体"""
    # 如果没有提供初始摘要，尝试从存储中检索
    if initial_summary is None:
        print_log(f"尝试从存储中检索实体: {entity_name}")
        initial_summary = retrieve_entity(entity_name)
        
        if initial_summary is None:
            print_log(f"未找到实体: {entity_name}", level="error")
            return None
        
    print_log(f"开始处理实体: {entity_name}")
    
    # 运行完整局部推理流程
    updated_summary = await run_full_local_reasoning(
        entity_name=entity_name,
        initial_summary=initial_summary,
        global_constraints=global_constraints,
        max_rounds=max_rounds
    )
    
    # 更新实体存储
    if updated_summary is not None:
        success = update_entity(entity_name, updated_summary)
        if success:
            print_log(f"已更新实体存储: {entity_name}", level="info")
        else:
            print_log(f"实体存储更新失败: {entity_name}", level="error")
    
    return updated_summary

async def process_entities_from_json(
    input_path: str,
    output_path: Optional[str] = None,
    global_constraints_path: Optional[str] = None,
    max_rounds: int = 4
) -> List[Dict[str, Any]]:
    """从JSON文件处理多个实体"""
    # 加载输入
    print_log(f"从 {input_path} 加载实体")
    with open(input_path, 'r', encoding='utf-8') as f:
        entities = json.load(f)
    
    # 加载全局约束（如果有）
    global_constraints = None
    if global_constraints_path:
        try:
            with open(global_constraints_path, 'r', encoding='utf-8') as f:
                global_constraints = json.load(f)
            print_log(f"已加载全局约束: {global_constraints_path}")
        except Exception as e:
            print_log(f"加载全局约束失败: {e}", level="error")
    
    # 处理每个实体
    updated_entities = []
    for entity in entities:
        entity_name = entity.get("name", "unknown")
        updated_summary = await process_entity_old(
            entity_name=entity_name,
            initial_summary=entity,
            global_constraints=global_constraints,
            max_rounds=max_rounds
        )
        
        if updated_summary:
            updated_entities.append(updated_summary)
    
    # 保存输出（如果提供了输出路径）
    if output_path and updated_entities:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(updated_entities, f, indent=2, ensure_ascii=False)
        print_log(f"已保存更新后的实体到: {output_path}", level="info")
    
    return updated_entities

async def process_directory(
    input_dir: str,
    output_dir: str,
    global_constraints_path: Optional[str] = None,
    max_rounds: int = 4
) -> None:
    """处理目录中的所有实体摘要"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print_log(f"输入目录不存在: {input_dir}", level="error")
        return
    
    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 加载全局约束（如果有）
    global_constraints = None
    if global_constraints_path:
        try:
            with open(global_constraints_path, 'r', encoding='utf-8') as f:
                global_constraints = json.load(f)
            print_log(f"已加载全局约束: {global_constraints_path}")
        except Exception as e:
            print_log(f"加载全局约束失败: {e}", level="error")
    
    # 遍历输入目录中的所有JSON文件
    for file_path in input_path.glob("**/*.json"):
        # 跳过非实体摘要文件
        if file_path.name != "full_summary.json" and file_path.name != "entity_summary.json":
            continue
        
        print_log(f"处理: {file_path}")
        
        try:
            # 加载实体
            with open(file_path, 'r', encoding='utf-8') as f:
                entity = json.load(f)
            
            # 提取实体名称
            entity_name = entity.get("name") or entity.get("module", Path(file_path).parent.name)
            
            # 处理实体
            updated_summary = await process_entity_old(
                entity_name=entity_name,
                initial_summary=entity,
                global_constraints=global_constraints,
                max_rounds=max_rounds
            )
            
            if updated_summary:
                # 创建输出文件
                rel_path = file_path.relative_to(input_path)
                output_file = output_path / rel_path
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(updated_summary, f, indent=2, ensure_ascii=False)
                
                print_log(f"已保存更新后的实体到: {output_file}", level="info")
        
        except Exception as e:
            print_log(f"处理 {file_path} 时出错: {e}", level="error")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行局部架构推理流程")
    parser.add_argument("--input", "-i", required=True, help="输入文件或目录路径")
    parser.add_argument("--output", "-o", help="输出文件或目录路径")
    parser.add_argument("--constraints", "-c", help="全局约束JSON文件路径")
    parser.add_argument("--rounds", "-r", type=int, default=4, help="推理轮次数量 (默认: 4)")
    parser.add_argument("--entity-name", "-n", help="要处理的单个实体名称")
    
    args = parser.parse_args()
    
    # 设置默认输出路径
    if not args.output and args.input:
        input_path = Path(args.input)
        if input_path.is_file():
            args.output = str(input_path.with_suffix('.enhanced.json'))
        else:
            args.output = str(input_path.parent / f"{input_path.name}_enhanced")
    
    # 运行推理
    if args.entity_name:
        # 处理单个实体
        asyncio.run(process_entity_old(
            entity_name=args.entity_name,
            global_constraints=None if not args.constraints else json.load(open(args.constraints)),
            max_rounds=args.rounds
        ))
    elif Path(args.input).is_file():
        # 处理单个JSON文件
        asyncio.run(process_entities_from_json(
            input_path=args.input,
            output_path=args.output,
            global_constraints_path=args.constraints,
            max_rounds=args.rounds
        ))
    else:
        # 处理目录
        asyncio.run(process_directory(
            input_dir=args.input,
            output_dir=args.output,
            global_constraints_path=args.constraints,
            max_rounds=args.rounds
        ))

if __name__ == "__main__":
    main() 