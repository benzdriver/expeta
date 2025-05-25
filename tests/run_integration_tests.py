from common import print_log
#!/usr/bin/env python
"""
集成测试运行脚本
提供一个方便的方式来运行所有或特定模块的集成测试
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def run_tests(module=None, verbose=False, skip_knowledge=True):
    """
    运行集成测试
    
    Args:
        module: 指定要测试的模块，为None时测试所有模块
        verbose: 是否显示详细输出
        skip_knowledge: 是否跳过知识库测试
    """
    # 设置项目根目录
    root_dir = Path(__file__).parent.parent.absolute()
    
    # 设置命令基础部分
    cmd = ["pytest"]
    if verbose:
        cmd.append("-v")
    
    # 添加skips
    if skip_knowledge and module != "knowledge":
        cmd.append("-k")
        cmd.append("not test_knowledge.py")
    
    # 设置测试目录
    if module:
        test_path = Path(__file__).parent / "integration" / f"test_{module}.py"
        if not test_path.exists():
            print_log(f"错误: 找不到测试模块 {module}")
            return 1
        cmd.append(str(test_path))
    else:
        cmd.append(str(Path(__file__).parent / "integration"))
    
    # 设置环境变量
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root_dir)
    
    # 打印当前环境与命令
    print_log(f"项目根目录: {root_dir}")
    print_log(f"PYTHONPATH: {env['PYTHONPATH']}")
    print_log(f"运行命令: {' '.join(cmd)}")
    
    # 运行测试
    result = subprocess.run(cmd, env=env)
    return result.returncode

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行ThinkForward AI集成测试")
    parser.add_argument("--module", "-m", help="测试特定模块 (llm_services, document_processing, knowledge, reasoning, apps)")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细输出")
    parser.add_argument("--include-knowledge", action="store_true", help="包含知识库测试(可能需要额外配置)")
    
    args = parser.parse_args()
    
    # 运行测试
    return run_tests(args.module, args.verbose, not args.include_knowledge)

if __name__ == "__main__":
    sys.exit(main()) 