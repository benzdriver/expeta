#!/usr/bin/env python3
"""
打印Qdrant配置信息工具
显示所有当前配置的参数及连接信息
"""

import os
import sys
import json
import dotenv
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# 加载环境变量
env_file = os.path.join(project_root, '.env')
if os.path.exists(env_file):
    dotenv.load_dotenv(env_file)

# 读取环境变量
config = {
    "QDRANT_HOST": os.environ.get("QDRANT_HOST", "未设置"),
    "QDRANT_PORT": os.environ.get("QDRANT_PORT", "未设置"),
    "QDRANT_API_KEY": os.environ.get("QDRANT_API_KEY", "未设置"),
    "QDRANT_PATH": os.environ.get("QDRANT_PATH", "data/qdrant"),
}

# 打印配置信息
print("\n" + "=" * 60)
print("  Qdrant配置信息")
print("=" * 60)

print(f"\n主要配置:")
print(f"  QDRANT_HOST: {config['QDRANT_HOST']}")
print(f"  QDRANT_PORT: {config['QDRANT_PORT']}")

if config['QDRANT_API_KEY'] != "未设置":
    masked_key = f"{config['QDRANT_API_KEY'][:8]}...{config['QDRANT_API_KEY'][-5:]}"
    print(f"  QDRANT_API_KEY: {masked_key}")
else:
    print(f"  QDRANT_API_KEY: {config['QDRANT_API_KEY']}")

print(f"  QDRANT_PATH: {config['QDRANT_PATH']}")

# 检查配置类型
print("\n配置类型:")
if config['QDRANT_HOST'] != "未设置" and config['QDRANT_API_KEY'] != "未设置":
    print("  ☁️ 使用Qdrant云服务")
    print(f"  连接URL: https://{config['QDRANT_HOST']}:{config['QDRANT_PORT']}")
else:
    print("  💻 使用本地存储")
    print(f"  存储路径: {config['QDRANT_PATH']}")

# 测试连接
print("\n连接测试:")
try:
    import requests
    if config['QDRANT_HOST'] != "未设置" and config['QDRANT_API_KEY'] != "未设置":
        url = f"https://{config['QDRANT_HOST']}:{config['QDRANT_PORT']}/collections"
        headers = {"api-key": config['QDRANT_API_KEY']}
        
        print(f"  请求: GET {url}")
        print(f"  请求头: api-key={config['QDRANT_API_KEY'][:8]}...{config['QDRANT_API_KEY'][-5:]}")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"  响应状态码: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ 连接成功!")
            data = response.json()
            collections = data.get("result", {}).get("collections", [])
            if collections:
                collection_names = [c.get('name') for c in collections]
                print(f"  发现 {len(collection_names)} 个集合: {', '.join(collection_names)}")
        else:
            print(f"  ❌ 连接失败: {response.text}")
except ImportError:
    print("  ⚠️ 缺少requests模块，无法测试连接")
except Exception as e:
    print(f"  ❌ 测试连接时出错: {str(e)}")

# 检查.env文件
print("\n环境文件:")
if os.path.exists(env_file):
    print(f"  ✅ .env文件存在: {env_file}")
    
    # 读取文件内容
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # 查找配置行
    qdrant_lines = [line.strip() for line in lines if line.strip().startswith("QDRANT_")]
    if qdrant_lines:
        print("  包含以下Qdrant配置:")
        for line in qdrant_lines:
            # 如果是API密钥行，进行掩码处理
            if line.startswith("QDRANT_API_KEY="):
                key = line.split("=", 1)[1].strip("'\"")
                if key:
                    masked = f"QDRANT_API_KEY={key[:8]}...{key[-5:]}"
                    print(f"    {masked}")
                else:
                    print(f"    {line}")
            else:
                print(f"    {line}")
    else:
        print("  ⚠️ 未找到Qdrant相关配置")
else:
    print(f"  ⚠️ .env文件不存在: {env_file}")

# 建议
print("\n建议操作:")
if config['QDRANT_HOST'] != "未设置" and config['QDRANT_API_KEY'] != "未设置":
    print("  ✅ 配置已完成，可以正常使用")
    print("  如需更新配置，请使用:")
    print(f"    python scripts/database/update_qdrant_config.py --help")
else:
    print("  ⚠️ 配置不完整，请设置以下环境变量:")
    if config['QDRANT_HOST'] == "未设置":
        print("    - QDRANT_HOST: Qdrant云服务地址")
    if config['QDRANT_API_KEY'] == "未设置":
        print("    - QDRANT_API_KEY: Qdrant API密钥")
    print("  可以使用以下命令更新配置:")
    print(f"    python scripts/database/update_qdrant_config.py --host YOUR_HOST --port YOUR_PORT --api-key YOUR_API_KEY")

print("\n完成!") 