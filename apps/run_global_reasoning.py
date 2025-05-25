from common import print_log
#!/usr/bin/env python3
"""
全局架构推理应用脚本。
分析文档目录中的所有文件，执行全局系统分析、架构风格确定和约束生成。
结果将保存为架构章程和模块指导原则。
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from reasoning.global_reasoning import run_global_reasoning, get_module_guidelines
from document_processing.content_analyzer import analyze_document_content
from dependency.dependency_inference import build_initial_dependency_graph

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

async def run_pipeline(input_dir: str, output_dir: str) -> Dict[str, Any]:
    """
    运行全局架构推理管道
    
    Args:
        input_dir: 输入文档目录
        output_dir: 输出结果目录
        
    Returns:
        Dict[str, Any]: 全局推理结果
    """
    # 1. 加载文档
    print_log(f"🚀 开始全局架构推理流程...")
    all_text = await load_documents(input_dir)
    
    if not all_text.strip():
        print_log(f"未找到任何文档内容，请检查输入目录", level="error")
        return {}
    
    # 2. 文档内容分析（可选）
    try:
        print_log(f"📊 分析文档内容...")
        doc_analysis = await analyze_document_content(all_text)
        print_log(f"✅ 文档分析完成，提取了 {len(doc_analysis.get('keyPoints', []))} 个关键点", level="info")
    except Exception as e:
        print_log(f"文档分析过程中出错: {e}", level="warning")
        doc_analysis = {"keyPoints": [], "summary": ""}
    
    # 3. 执行全局推理
    print_log(f"🧠 执行全局架构推理...")
    global_results = await run_global_reasoning(all_text)
    
    if not global_results:
        print_log(f"全局推理未产生结果", level="error")
        return {}
    
    # 4. 保存结果
    await save_results(global_results, output_dir)
    
    print_log(f"✅ 全局架构推理完成！结果已保存到 {output_dir}", level="info")
    return global_results

async def save_results(results: Dict[str, Any], output_dir: str):
    """
    保存推理结果到输出目录
    
    Args:
        results: 推理结果
        output_dir: 输出目录路径
    """
    print_log(f"💾 保存结果到目录 {output_dir}...")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 保存系统分析结果
    system_analysis_path = output_path / "system_analysis.json"
    with open(system_analysis_path, "w", encoding="utf-8") as f:
        json.dump(results.get("systemAnalysis", {}), f, indent=2, ensure_ascii=False)
    
    # 保存架构风格结果
    architecture_style_path = output_path / "architecture_style.json"
    with open(architecture_style_path, "w", encoding="utf-8") as f:
        json.dump(results.get("architectureStyle", {}), f, indent=2, ensure_ascii=False)
    
    # 保存全局约束/架构章程
    constraints_path = output_path / "architecture_charter.json"
    with open(constraints_path, "w", encoding="utf-8") as f:
        json.dump(results.get("constraints", {}), f, indent=2, ensure_ascii=False)
    
    # 保存初始模块列表
    modules_path = output_path / "initial_modules.json"
    modules = results.get("architectureStyle", {}).get("modules", [])
    with open(modules_path, "w", encoding="utf-8") as f:
        json.dump(modules, f, indent=2, ensure_ascii=False)
    
    # 如果存在模块列表，构建初始依赖图
    if modules:
        print_log(f"🔄 基于 {len(modules)} 个初始模块构建依赖图...", level="info")
        # 构建初始依赖图
        dependency_map = await build_initial_dependency_graph(modules)
        
        # 保存依赖图
        dependencies_path = output_path / "initial_dependencies.json"
        with open(dependencies_path, "w", encoding="utf-8") as f:
            json.dump(dependency_map, f, indent=2, ensure_ascii=False)
    
    # 为常见模块类型生成指导原则
    module_types = ["frontend", "backend", "api", "database", "testing"]
    module_guidelines_dir = output_path / "module_guidelines"
    module_guidelines_dir.mkdir(exist_ok=True)
    
    for module_type in module_types:
        try:
            print_log(f"🔍 生成 {module_type} 模块指导原则...")
            guidelines = await get_module_guidelines(module_type)
            
            guidelines_path = module_guidelines_dir / f"{module_type}_guidelines.json"
            with open(guidelines_path, "w", encoding="utf-8") as f:
                json.dump(guidelines, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print_log(f"为模块类型 {module_type} 生成指导原则时出错: {e}", level="error")
    
    # 创建架构章程的Markdown格式
    try:
        await generate_markdown_charter(results, output_path / "architecture_charter.md")
    except Exception as e:
        print_log(f"生成Markdown架构章程时出错: {e}", level="warning")
    
    print_log(f"结果已保存到 {output_dir}", level="info")

async def generate_markdown_charter(results: Dict[str, Any], output_path: Path):
    """
    生成架构章程的Markdown格式
    
    Args:
        results: 推理结果
        output_path: 输出文件路径
    """
    system_analysis = results.get("systemAnalysis", {})
    architecture_style = results.get("architectureStyle", {})
    constraints = results.get("constraints", {})
    
    markdown = f"""# 架构章程

## 1. 系统概述

- **系统类型**: {system_analysis.get("systemType", "未指定")}
- **所属领域**: {system_analysis.get("domain", "未指定")}
- **系统规模**: {system_analysis.get("systemScale", "未指定")}
- **用户群体**: {", ".join(system_analysis.get("users", ["未指定"]))}

### 1.1 核心用例

{_list_to_markdown(system_analysis.get("coreUseCases", []))}

### 1.2 技术挑战

{_list_to_markdown(system_analysis.get("technicalChallenges", []))}

## 2. 架构决策

- **架构风格**: {architecture_style.get("architectureStyle", "未指定")}
- **选择理由**: {architecture_style.get("justification", "未指定")}

### 2.1 技术栈

**前端技术**:
{_list_to_markdown(architecture_style.get("frontendStack", []))}

**后端技术**:
{_list_to_markdown(architecture_style.get("backendStack", []))}

**数据存储**:
{_list_to_markdown(architecture_style.get("dataStorage", []))}

### 2.2 部署与扩展

- **部署策略**: {architecture_style.get("deployment", "未指定")}
- **扩展策略**: {architecture_style.get("scalability", "未指定")}

## 3. 全局约束

### 3.1 命名规范

"""
    
    # 添加命名规范部分
    naming = constraints.get("namingConventions", {})
    for key, value in naming.items():
        if key != "examples":
            markdown += f"- **{key}**: {value}\n"
    
    if "examples" in naming:
        markdown += "\n**示例**:\n"
        markdown += _list_to_markdown(naming.get("examples", []))
    
    markdown += """
### 3.2 代码组织结构

"""
    
    # 添加代码组织部分
    code_org = constraints.get("codeOrganization", {})
    for key, value in code_org.items():
        markdown += f"- **{key}**: {value}\n"
    
    markdown += """
### 3.3 API 约定

"""
    
    # 添加API约定部分
    api_conv = constraints.get("apiConventions", {})
    for key, value in api_conv.items():
        markdown += f"- **{key}**: {value}\n"
    
    markdown += """
### 3.4 错误处理与日志

"""
    
    # 添加错误处理部分
    error_handling = constraints.get("errorHandling", {})
    for key, value in error_handling.items():
        markdown += f"- **{key}**: {value}\n"
    
    # 添加安全规范部分
    markdown += """
### 3.5 安全规范

"""
    
    security = constraints.get("security", {})
    for key, value in security.items():
        markdown += f"- **{key}**: {value}\n"
    
    # 添加性能要求部分
    markdown += """
### 3.6 性能要求

"""
    
    performance = constraints.get("performance", {})
    for key, value in performance.items():
        markdown += f"- **{key}**: {value}\n"
    
    # 添加测试策略部分
    markdown += """
### 3.7 测试策略

"""
    
    testing = constraints.get("testingStrategy", {})
    for key, value in testing.items():
        markdown += f"- **{key}**: {value}\n"
    
    # 添加文档规范部分
    markdown += """
### 3.8 文档规范

"""
    
    docs = constraints.get("documentation", {})
    for key, value in docs.items():
        markdown += f"- **{key}**: {value}\n"
    
    # 添加版本历史
    markdown += """
## 4. 版本历史

"""
    
    version_history = constraints.get("versionHistory", [{"version": "1.0", "date": "自动生成", "description": "初始版本"}])
    for version in version_history:
        markdown += f"- **版本 {version.get('version')}** ({version.get('date')}): {version.get('description')}\n"
    
    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print_log(f"架构章程Markdown文件已保存到 {output_path}", level="info")

def _list_to_markdown(items: List[str]) -> str:
    """将列表转换为Markdown列表格式"""
    if not items:
        return "- 未指定"
    return "\n".join([f"- {item}" for item in items])

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="全局架构推理应用")
    parser.add_argument("-i", "--input", type=str, default="data/input", help="输入文档目录")
    parser.add_argument("-o", "--output", type=str, default="data/output/architecture", help="输出目录")
    
    args = parser.parse_args()
    await run_pipeline(args.input, args.output)

if __name__ == "__main__":
    asyncio.run(main()) 