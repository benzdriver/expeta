from common import print_log
#!/usr/bin/env python3
"""
完整架构推理流水线应用脚本。
集成全局架构推理和局部模块推理，提供端到端的架构分析体验。
分析文档 => 执行全局推理 => 发现实体 => 执行局部推理 => 生成完整架构
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from reasoning.global_reasoning import run_global_reasoning
from reasoning.local_reasoning.local_chain import run_local_reasoning
from document_processing.entity_discovery import discover_entities
from document_processing.content_analyzer import analyze_document_content
from document_processing.initial_summarizer import generate_initial_summary
from knowledge.entity_storage import store_entity_summary

async def load_documents(input_dir: str) -> str:
    """
    从输入目录加载所有文档
    
    Args:
        input_dir: 输入目录路径
        
    Returns:
        str: 合并后的文档内容
    """
    print_log(f"📂 从目录 {input_dir} 加载文档...")
    
    input_path = Path(input_dir)
    all_text = ""
    
    # 计数器
    doc_count = 0
    
    # 支持的文件扩展名
    supported_exts = [".md", ".txt", ".rst"]
    
    # 遍历目录中的所有文件
    for file_path in sorted(input_path.glob("**/*")):
        if file_path.is_file() and file_path.suffix.lower() in supported_exts:
            try:
                file_content = file_path.read_text(encoding="utf-8")
                all_text += f"\n\n### FILE: {file_path.name} ###\n\n"
                all_text += file_content
                doc_count += 1
            except Exception as e:
                print_log(f"无法读取文件 {file_path}: {e}", level="error")
    
    print_log(f"已加载 {doc_count} 个文档", level="info")
    return all_text

async def process_entity(entity: Dict[str, str], 
                        all_text: str, 
                        global_results: Dict[str, Any], 
                        output_dir: str, 
                        max_reasoning_rounds: int = 4) -> Dict[str, Any]:
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
    from llm_services.rag import retrieve_context_for_entity
    context = await retrieve_context_for_entity(entity_name, all_text)
    
    # 生成初始摘要
    print_log(f"📝 为 {entity_name} 生成初始摘要...")
    initial_summary = await generate_initial_summary(entity, context)
    
    # 运行局部推理链
    print_log(f"🧠 为 {entity_name} 执行多轮推理...")
    enhanced_summary = await run_local_reasoning(
        entity_name=entity_name,
        initial_summary=initial_summary,
        context=context,
        global_constraints=global_results.get("constraints", {}),
        max_rounds=max_reasoning_rounds
    )
    
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
    await store_entity_summary(entity_name, enhanced_summary)
    
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
        
        if summary['frontend'].get('routes'):
            markdown += "### 路由\n\n"
            for route in summary['frontend']['routes']:
                markdown += f"- {route}\n"
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
        
        if summary['backend'].get('repositories'):
            markdown += "### 仓储\n\n"
            for repo in summary['backend']['repositories']:
                markdown += f"- {repo}\n"
            markdown += "\n"
        
        if summary['backend'].get('api'):
            markdown += "### API端点\n\n"
            for api in summary['backend']['api']:
                markdown += f"- {api}\n"
            markdown += "\n"
        
        if summary['backend'].get('dtos') and isinstance(summary['backend']['dtos'], dict):
            markdown += "### 数据传输对象\n\n"
            for dto_name, dto_info in summary['backend']['dtos'].items():
                markdown += f"#### {dto_name}\n\n"
                if isinstance(dto_info, dict) and 'fields' in dto_info:
                    for field in dto_info['fields']:
                        markdown += f"- {field}\n"
                markdown += "\n"
    
    # 依赖关系
    if 'dependencies' in summary and summary['dependencies']:
        markdown += "## 依赖关系\n\n"
        for dependency in summary['dependencies']:
            markdown += f"- {dependency}\n"
        markdown += "\n"
    
    # 测试计划
    if 'test' in summary and (summary['test'].get('unit') or summary['test'].get('e2e')):
        markdown += "## 测试计划\n\n"
        
        if summary['test'].get('unit'):
            markdown += "### 单元测试\n\n"
            for test in summary['test']['unit']:
                markdown += f"- {test}\n"
            markdown += "\n"
        
        if summary['test'].get('e2e'):
            markdown += "### 端到端测试\n\n"
            for test in summary['test']['e2e']:
                markdown += f"- {test}\n"
            markdown += "\n"
    
    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

async def run_pipeline(input_dir: str, output_dir: str, max_reasoning_rounds: int = 4):
    """
    运行完整架构推理流水线
    
    Args:
        input_dir: 输入文档目录
        output_dir: 输出目录
        max_reasoning_rounds: 最大推理轮数
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 步骤1: 加载文档
    all_text = await load_documents(input_dir)
    
    if not all_text.strip():
        print_log(f"未找到任何文档内容，请检查输入目录", level="error")
        return
    
    # 步骤2: 全局架构推理
    print_log("\n🌍 开始全局架构推理...")
    global_results = await run_global_reasoning(all_text)
    
    # 保存全局推理结果
    global_dir = output_path / "global"
    global_dir.mkdir(exist_ok=True)
    
    with open(global_dir / "architecture_charter.json", "w", encoding="utf-8") as f:
        json.dump(global_results, f, indent=2, ensure_ascii=False)
    
    # 步骤3: 发现实体
    print_log("\n🔎 发现实体...")
    entities = await discover_entities(all_text)
    
    print_log(f"发现 {len(entities)} 个实体:")
    for i, entity in enumerate(entities):
        print_log(f"  {i+1}. {entity.get('name', 'unknown')} (类型: {entity.get('type', 'unknown')})")
    
    # 保存实体列表
    with open(output_path / "entities.json", "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    
    # 步骤4: 为每个实体执行局部推理
    entities_dir = output_path / "entities"
    entities_dir.mkdir(exist_ok=True)
    
    # 按复杂度排序实体，先处理简单实体
    simple_entities = [e for e in entities if '/' not in e.get('name', '')]
    complex_entities = [e for e in entities if '/' in e.get('name', '')]
    
    # 按名称长度/复杂度排序
    simple_entities.sort(key=lambda e: len(e.get('name', '')))
    complex_entities.sort(key=lambda e: len(e.get('name', '').split('/')))
    
    # 合并排序后的列表
    sorted_entities = simple_entities + complex_entities
    
    # 处理实体
    processed_entities = []
    for entity in sorted_entities:
        entity_name = entity.get('name', 'unknown')
        try:
            summary = await process_entity(
                entity=entity,
                all_text=all_text,
                global_results=global_results,
                output_dir=str(entities_dir),
                max_reasoning_rounds=max_reasoning_rounds
            )
            processed_entities.append({"name": entity_name, "success": True})
        except Exception as e:
            print_log(f"处理实体 {entity_name} 时出错: {e}", level="error")
            processed_entities.append({"name": entity_name, "success": False, "error": str(e)})
    
    # 生成全局架构图
    try:
        print_log("\n📊 生成架构图...")
        await generate_architecture_diagram(processed_entities, global_results, output_path)
    except Exception as e:
        print_log(f"生成架构图时出错: {e}", level="warning")
    
    # 生成索引页面
    generate_index_page(processed_entities, output_path)
    
    print_log("\n🎉 完整架构推理流水线执行完成！")
    print_log(f"📁 输出目录: {output_dir}")
    print_log(f"📘 架构章程: {global_dir}/architecture_charter.json")
    print_log(f"🔗 索引页面: {output_path}/index.md")

async def generate_architecture_diagram(processed_entities: List[Dict[str, Any]], 
                                      global_results: Dict[str, Any],
                                      output_dir: Path):
    """
    生成架构图（简化版，仅生成文本描述）
    
    Args:
        processed_entities: 处理过的实体列表
        global_results: 全局推理结果
        output_dir: 输出目录
    """
    # 这里只生成一个简单的文本描述，实际实现可能会生成PlantUML或Mermaid图
    arch_desc = """# 系统架构图

```
此处应有架构图 - 将在未来版本实现自动生成
在实际实现中，可考虑使用PlantUML或Mermaid格式
```

## 系统结构概览

"""
    
    # 添加系统类型和架构风格
    system_analysis = global_results.get("systemAnalysis", {})
    architecture_style = global_results.get("architectureStyle", {})
    
    arch_desc += f"- **系统类型**: {system_analysis.get('systemType', '未指定')}\n"
    arch_desc += f"- **架构风格**: {architecture_style.get('architectureStyle', '未指定')}\n\n"
    
    # 添加主要组件列表
    arch_desc += "## 主要组件\n\n"
    successful_entities = [e["name"] for e in processed_entities if e.get("success", False)]
    
    for entity_name in successful_entities:
        arch_desc += f"- {entity_name}\n"
    
    # 写入文件
    with open(output_dir / "architecture_diagram.md", "w", encoding="utf-8") as f:
        f.write(arch_desc)

def generate_index_page(processed_entities: List[Dict[str, Any]], output_dir: Path):
    """
    生成索引页面
    
    Args:
        processed_entities: 处理过的实体列表
        output_dir: 输出目录
    """
    index = """# 架构文档索引

## 全局架构

- [架构章程](global/architecture_charter.json)
- [架构图](architecture_diagram.md)

## 实体架构

"""
    
    # 添加实体列表，分类显示
    successful = [e for e in processed_entities if e.get("success", False)]
    failed = [e for e in processed_entities if not e.get("success", False)]
    
    # 成功处理的实体
    if successful:
        for entity in successful:
            entity_name = entity["name"]
            safe_name = _sanitize_path(entity_name)
            index += f"- [{entity_name}](entities/{safe_name}/architecture.md)\n"
    
    # 处理失败的实体
    if failed:
        index += "\n### 处理失败的实体\n\n"
        for entity in failed:
            index += f"- {entity['name']} - 错误: {entity.get('error', '未知错误')}\n"
    
    # 写入文件
    with open(output_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(index)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="完整架构推理流水线")
    parser.add_argument("--input", "-i", type=str, default="data/input", help="输入文档目录")
    parser.add_argument("--output", "-o", type=str, default="data/output/architecture_full", help="输出目录")
    parser.add_argument("--rounds", "-r", type=int, default=4, help="最大推理轮数")
    
    args = parser.parse_args()
    
    try:
        await run_pipeline(args.input, args.output, args.rounds)
    except Exception as e:
        print_log(f"流水线执行过程中出错: {e}", level="error")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 