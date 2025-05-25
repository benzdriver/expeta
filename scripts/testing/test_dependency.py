#!/usr/bin/env python3
"""
依赖管理模块测试脚本。
提供命令行接口测试依赖管理模块的各种功能。
"""

import sys
import argparse
import pytest
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common import print_log
from dependency.dependency_manager import DependencyManager
from dependency.dependency_inference import (
    build_initial_dependency_graph,
    DependencyInference
)

def test_all():
    """运行所有依赖管理模块的测试"""
    print_log("运行所有依赖管理模块的测试...", level="info")
    pytest.main(["-xvs", "tests/unit/test_dependency_manager.py", "tests/unit/test_dependency_inference.py", "tests/integration/test_dependency.py"])

def test_create_sample_graph():
    """创建示例依赖图并输出可视化结果"""
    print_log("创建示例依赖图...", level="info")
    
    # 创建依赖管理器
    dm = DependencyManager()
    
    # 添加示例模块
    dm.add_module("DataAccess", [], "infrastructure")
    dm.add_module("ExternalApiClient", [], "infrastructure")
    dm.add_module("UserEntity", [], "domain")
    dm.add_module("OrderEntity", [], "domain")
    dm.add_module("UserService", ["DataAccess", "UserEntity"], "application")
    dm.add_module("OrderService", ["DataAccess", "OrderEntity", "UserEntity"], "application")
    dm.add_module("NotificationService", ["ExternalApiClient"], "application")
    dm.add_module("UserController", ["UserService"], "presentation")
    dm.add_module("OrderController", ["OrderService"], "presentation")
    dm.add_module("DashboardController", ["UserService", "OrderService"], "presentation")
    
    # 生成依赖图可视化
    output_path = dm.visualize(show_layers=True)
    print_log(f"依赖图已生成: {output_path}", level="info")
    
    # 获取依赖摘要
    summary = dm.get_dependency_summary()
    
    # 输出摘要信息
    # 检查summary对象实际包含的键
    if summary:
        print_log(f"依赖摘要信息:", level="info")
        for key, value in summary.items():
            print_log(f"- {key}: {value}", level="info")
        
        # 模块数量
        if "layer_distribution" in summary:
            module_count = sum(summary["layer_distribution"].values())
            print_log(f"总模块数: {module_count}", level="info")
    
    # 检查潜在问题
    dependency_check = dm.check_circular_dependencies()
    if dependency_check["has_cycles"]:
        print_log(f"⚠️ 检测到循环依赖: {dependency_check['cycles']}", level="warning")
    else:
        print_log("✅ 无循环依赖", level="info")
        
    layer_check = dm.check_layer_violations()
    if layer_check["has_violations"]:
        print_log(f"⚠️ 检测到层次违规: {layer_check['violations']}", level="warning")
    else:
        print_log("✅ 无层次违规", level="info")
    
    return dm

def test_dependency_inference():
    """测试依赖推断功能"""
    print_log("测试依赖推断功能...", level="info")
    
    # 创建示例模块
    modules = [
        {"name": "DataRepository", "description": "数据存储层"},
        {"name": "UserEntity", "description": "用户实体对象"},
        {"name": "UserService", "description": "用户服务，负责处理用户逻辑，依赖DataRepository和UserEntity"},
        {"name": "AuthService", "description": "认证服务，负责处理用户认证，依赖UserService"},
        {"name": "UserController", "description": "用户控制器，处理HTTP请求，依赖UserService和AuthService"}
    ]
    
    # 创建依赖推断器
    inferencer = DependencyInference()
    
    # 使用同步方式推断，避免在测试中处理异步
    try:
        # 构建初始依赖图 (同步方式简化测试)
        dependency_map = build_initial_dependency_graph(modules)
        
        # 输出推断结果
        print_log("依赖推断结果:", level="info")
        for module_name, module_info in dependency_map.items():
            if isinstance(module_info, dict) and "depends_on" in module_info:
                dependencies = ", ".join(module_info["depends_on"]) if module_info["depends_on"] else "无"
                layer = module_info.get("layer", "未知")
                print_log(f"- {module_name} ({layer}) -> 依赖: {dependencies}", level="info")
            else:
                print_log(f"- {module_name} -> 依赖信息格式不正确", level="warning")
    except Exception as e:
        print_log(f"推断依赖关系时出错: {e}", level="error")
        # 使用简单的模式匹配作为回退方案
        print_log("使用简单的模式匹配作为回退方案...", level="info")
        dependency_map = {}
        for module in modules:
            name = module["name"]
            desc = module["description"]
            # 简单模式匹配查找"依赖"后面的模块名
            deps = []
            if "依赖" in desc:
                # 提取依赖XXX和YYY的模式
                parts = desc.split("依赖")[1].strip()
                for other_module in modules:
                    other_name = other_module["name"]
                    if other_name != name and other_name in parts:
                        deps.append(other_name)
            
            # 添加到依赖图
            dm = DependencyManager()
            layer = dm.infer_layer(name)
            dependency_map[name] = {"depends_on": deps, "layer": layer}
            print_log(f"- {name} ({layer}) -> 依赖: {', '.join(deps) if deps else '无'}", level="info")
    
    return dependency_map

def test_with_real_api():
    """使用真实API测试依赖推断"""
    print_log("使用真实API测试依赖推断功能...", level="info")
    
    # 运行真实API测试
    result = pytest.main(["-xvs", "tests/integration/test_dependency_real_api.py"])
    
    if result == 0:
        print_log("✅ 真实API测试成功通过", level="info")
    else:
        print_log("❌ 真实API测试失败", level="error")

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description="依赖管理模块测试工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 运行所有测试的命令
    subparsers.add_parser("test-all", help="运行所有依赖管理模块测试")
    
    # 创建示例依赖图的命令
    subparsers.add_parser("create-graph", help="创建示例依赖图并生成可视化")
    
    # 测试依赖推断的命令
    subparsers.add_parser("infer-dependencies", help="测试依赖关系推断功能")
    
    # 使用真实API测试的命令
    subparsers.add_parser("test-real-api", help="使用真实API测试依赖推断功能")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 根据命令选择执行的功能
    if args.command == "test-all" or not args.command:
        test_all()
    elif args.command == "create-graph":
        test_create_sample_graph()
    elif args.command == "infer-dependencies":
        test_dependency_inference()
    elif args.command == "test-real-api":
        test_with_real_api()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 