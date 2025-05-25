#!/usr/bin/env python3
"""
Qdrant诊断命令行工具
提供Qdrant连接测试、配置验证和故障排除功能
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

try:
    # 导入核心诊断模块
    from knowledge.diagnostics import QdrantDiagnostics, run_diagnostics, test_connection
except ImportError as e:
    print(f"❌ 导入诊断模块失败: {str(e)}")
    print("请确保knowledge/diagnostics.py文件存在")
    sys.exit(1)

def main():
    """命令行入口点"""
    parser = argparse.ArgumentParser(description="Qdrant诊断工具")
    parser.add_argument("--quick", "-q", action="store_true", help="只进行快速连接测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细调试信息")
    parser.add_argument("--no-logger", action="store_true", help="使用print输出而非日志系统")
    parser.add_argument("--curl", "-c", action="store_true", help="包含curl命令测试")
    args = parser.parse_args()
    
    # 确定是否使用日志系统
    use_logger = not args.no_logger
    
    if args.quick:
        # 快速测试
        print("🔄 正在进行快速连接测试...")
        connection_ok = test_connection(use_logger=use_logger)
        
        if connection_ok:
            print("✅ 连接测试成功！")
            sys.exit(0)
        else:
            print("❌ 连接测试失败")
            print("使用 --verbose 选项获取详细信息，或运行不带 --quick 选项的命令进行完整诊断")
            sys.exit(1)
    else:
        # 完整诊断
        print("🔍 开始Qdrant完整诊断...")
        
        # 创建诊断工具实例
        diagnostics = QdrantDiagnostics(use_logger=use_logger)
        
        # 如果需要详细模式，设置环境变量
        if args.verbose:
            os.environ["QDRANT_DEBUG_LEVEL"] = "2"
        
        # 运行诊断
        results = diagnostics.run_full_diagnostics()
        
        # 显示结果总结
        all_tests_passed = all(results["tests"].values())
        if all_tests_passed and not results["issues"]:
            print("\n✅ 诊断完成: 未发现问题")
            sys.exit(0)
        else:
            print("\n⚠️ 诊断完成: 发现一些问题")
            sys.exit(1)

if __name__ == "__main__":
    main() 