#!/usr/bin/env python3
"""
Expeta架构分析系统入口脚本。
提供简单的命令行界面运行全局推理、局部推理或完整推理流水线。
"""

import os
import sys
import argparse
import asyncio
import json
from pathlib import Path

# 将项目根目录添加到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from common import print_log

def main():
    # 初始化知识系统，确保所有向量集合存在
    from knowledge import initialize_knowledge_system
    initialize_success = initialize_knowledge_system()
    if not initialize_success:
        print_log("⚠️ 知识系统初始化部分失败，但将继续执行", level="warning")
    else:
        print_log("✅ 知识系统初始化成功", level="info")
        
    # 初始化依赖管理器
    from dependency.dependency_manager import initialize_dependency_graph
    dependency_manager = initialize_dependency_graph()
    
    # 检查现有模块数量
    module_count = len(dependency_manager.graph) if dependency_manager else 0
    
    # 如果没有模块或模块很少，检查是否有初始依赖文件
    if module_count < 3:
        initial_deps_path = Path("data/output/architecture/initial_dependencies.json")
        initial_modules_path = Path("data/output/architecture/initial_modules.json")
        
        if initial_deps_path.exists() and initial_modules_path.exists():
            print_log("找到初始依赖图文件，正在加载...", level="info")
            try:
                # 读取初始模块
                with open(initial_modules_path, "r", encoding="utf-8") as f:
                    modules = json.load(f)
                
                # 从模块构建依赖图
                for module in modules:
                    module_name = module.get("name")
                    depends_on = module.get("depends_on", [])
                    layer = module.get("layer")
                    
                    if module_name:
                        dependency_manager.add_module(module_name, depends_on, layer)
                
                print_log(f"✅ 已从初始模块文件加载 {len(modules)} 个模块", level="info")
                
                # 更新模块计数
                module_count = len(dependency_manager.graph)
            except Exception as e:
                print_log(f"加载初始依赖图失败: {e}", level="warning")
    
    # 生成依赖图可视化
    if module_count > 0:
        try:
            graph_path = dependency_manager.visualize(show_layers=True)
            print_log(f"✅ 依赖图可视化已保存到 {graph_path}", level="info")
            
            # 获取依赖摘要信息
            summary = dependency_manager.get_dependency_summary()
            layer_distribution = summary.get("layer_distribution", {})
            
            print_log(f"✅ 依赖图初始化成功，共加载 {module_count} 个模块", level="info")
            print_log(f"📊 架构层次分布: {layer_distribution}", level="info")
            
            # 检查是否有问题模块
            problem_modules = summary.get("problem_modules", [])
            if problem_modules:
                print_log(f"⚠️ 检测到 {len(problem_modules)} 个问题模块: {problem_modules}", level="warning")
        except Exception as e:
            print_log(f"依赖图可视化生成失败: {e}", level="warning")
    else:
        print_log("⚠️ 依赖图为空，请先运行全局推理生成初始模块", level="warning")
    
    parser = argparse.ArgumentParser(
        description="Expeta架构分析系统 - 智能架构推理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_expeta.py full -i ./docs -o ./output  # 运行完整推理流水线
  python run_expeta.py global -i ./docs            # 仅运行全局架构推理
  python run_expeta.py local -e "UserService"      # 对特定实体运行局部推理
        """
    )
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # full命令 - 运行完整流水线
    full_parser = subparsers.add_parser("full", help="运行完整架构推理流水线")
    full_parser.add_argument("-i", "--input", type=str, default="data/input", help="输入文档目录")
    full_parser.add_argument("-o", "--output", type=str, default="data/output/architecture_full", help="输出目录")
    full_parser.add_argument("-r", "--rounds", type=int, default=4, help="最大推理轮数")
    
    # global命令 - 仅运行全局推理
    global_parser = subparsers.add_parser("global", help="仅运行全局架构推理")
    global_parser.add_argument("-i", "--input", type=str, default="data/input", help="输入文档目录")
    global_parser.add_argument("-o", "--output", type=str, default="data/output/architecture", help="输出目录")
    
    # local命令 - 仅运行局部推理
    local_parser = subparsers.add_parser("local", help="对特定实体运行局部推理")
    local_parser.add_argument("-e", "--entity", type=str, required=True, help="实体名称")
    local_parser.add_argument("-i", "--input", type=str, default="data/input", help="输入文档目录")
    local_parser.add_argument("-o", "--output", type=str, default="data/output/entity", help="输出目录")
    local_parser.add_argument("-r", "--rounds", type=int, default=4, help="最大推理轮数")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "full":
        print_log("🚀 运行完整架构推理流水线...")
        from apps.run_full_pipeline import run_pipeline
        asyncio.run(run_pipeline(args.input, args.output, args.rounds))
        
    elif args.command == "global":
        print_log("🌍 运行全局架构推理...")
        from apps.run_global_reasoning import run_pipeline
        asyncio.run(run_pipeline(args.input, args.output))
        
    elif args.command == "local":
        print_log(f"🧩 为实体 {args.entity} 运行局部推理...")
        
        # 加载文档
        from apps.run_full_pipeline import load_documents
        from apps.run_local_reasoning import process_entity
        all_text = asyncio.run(load_documents(args.input))
        
        if not all_text.strip():
            print_log(f"未找到任何文档内容，请检查输入目录", level="error")
            return
        
        # 创建实体对象
        entity = {"name": args.entity, "type": "Unknown"}
        
        # 运行局部推理
        try:
            # 假设已有全局结果
            global_results = {"constraints": {}}
            
            # 处理实体
            asyncio.run(process_entity(entity, all_text, global_results, args.output, args.rounds))
            print_log(f"实体 {args.entity} 推理完成！输出目录: {args.output}", level="info")
        except Exception as e:
            print_log(f"处理实体时出错: {e}", level="error")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 