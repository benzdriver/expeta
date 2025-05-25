#!/usr/bin/env python3
"""
重置Qdrant API密钥脚本
"""

import os
import sys
import re
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

def update_env_file(new_api_key=None):
    """更新.env文件中的API密钥"""
    env_file = os.path.join(project_root, '.env')
    
    if not os.path.exists(env_file):
        print(f"错误: 未找到.env文件: {env_file}")
        return False
    
    # 读取当前内容
    with open(env_file, 'r') as f:
        content = f.read()
    
    # 查找并替换API密钥
    if new_api_key:
        # 如果提供了新密钥，替换现有密钥
        if 'QDRANT_API_KEY=' in content:
            content = re.sub(r'QDRANT_API_KEY=.*', f'QDRANT_API_KEY={new_api_key}', content)
            print(f"✅ 已更新API密钥为: {'*' * (len(new_api_key) - 8) + new_api_key[-8:]}")
        else:
            content += f"\nQDRANT_API_KEY={new_api_key}\n"
            print(f"✅ 已添加API密钥: {'*' * (len(new_api_key) - 8) + new_api_key[-8:]}")
    else:
        # 注释掉现有密钥
        content = re.sub(r'QDRANT_API_KEY=(.*)', r'# QDRANT_API_KEY=\1', content)
        print("✅ 已注释掉现有API密钥")
    
    # 写回文件
    with open(env_file, 'w') as f:
        f.write(content)
    
    return True

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python reset_qdrant_api.py [新API密钥]")
        print("  如果不提供新密钥，将注释掉现有密钥")
        return 1
    
    new_api_key = sys.argv[1] if len(sys.argv) > 1 else None
    if update_env_file(new_api_key):
        print("✅ 操作完成")
        print("请重启应用以使用新的API密钥")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main()) 