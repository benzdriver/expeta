#!/usr/bin/env python3
"""
交互式更新Qdrant API密钥工具
"""

import os
import sys
import dotenv
from pathlib import Path
import getpass

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

try:
    from common.logger import Logger
    logger = Logger("api_key_updater")
except ImportError:
    # 如果没有logger模块，使用简单的print函数
    class SimpleLogger:
        def log(self, message, **kwargs):
            print(message)
    logger = SimpleLogger()

def load_env_file():
    """加载.env文件"""
    env_file = os.path.join(project_root, '.env')
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write('# Expeta环境配置\n')
    
    dotenv.load_dotenv(env_file)
    return env_file

def update_api_key(env_file, api_key):
    """更新.env文件中的API密钥"""
    # 读取当前.env文件内容
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # 查找QDRANT_API_KEY行
    api_key_updated = False
    updated_lines = []
    
    for line in lines:
        if line.strip().startswith('QDRANT_API_KEY='):
            updated_lines.append(f'QDRANT_API_KEY={api_key}\n')
            api_key_updated = True
        else:
            updated_lines.append(line)
    
    # 如果没有找到API密钥行，添加一个
    if not api_key_updated:
        updated_lines.append(f'QDRANT_API_KEY={api_key}\n')
    
    # 写回.env文件
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    logger.log(f"✅ API密钥已更新到: {env_file}")

def test_api_key(api_key):
    """测试API密钥是否有效"""
    import requests
    
    host = os.environ.get('QDRANT_HOST', 'c1d98dfd-eab2-4612-8517-987bc2256d34.us-west-2-0.aws.cloud.qdrant.io')
    port = os.environ.get('QDRANT_PORT', '6333')
    
    logger.log(f"🔑 测试API密钥...")
    
    try:
        response = requests.get(
            f"https://{host}:{port}/collections",
            headers={"api-key": api_key},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            collections = data.get("result", {}).get("collections", [])
            collection_names = [c.get('name') for c in collections]
            
            logger.log(f"✅ API密钥有效! 发现 {len(collection_names)} 个集合")
            if collection_names:
                logger.log(f"📊 集合: {', '.join(collection_names)}")
            return True
        else:
            logger.log(f"❌ API密钥无效 (HTTP {response.status_code})")
            logger.log(f"📝 响应: {response.text}")
            return False
    except Exception as e:
        logger.log(f"❌ 测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.log("🔑 Qdrant API密钥更新工具")
    logger.log("========================")
    
    # 加载环境文件
    env_file = load_env_file()
    current_api_key = os.environ.get('QDRANT_API_KEY', '')
    
    # 显示当前配置
    logger.log("\n📋 当前配置:")
    logger.log(f"  - 主机: {os.environ.get('QDRANT_HOST', '未设置')}")
    logger.log(f"  - 端口: {os.environ.get('QDRANT_PORT', '未设置')}")
    
    if current_api_key:
        masked_key = f"{current_api_key[:8]}...{current_api_key[-5:]}"
        logger.log(f"  - API密钥: {masked_key}")
    else:
        logger.log("  - API密钥: 未设置")
    
    # 获取新API密钥
    print("\n请输入新的API密钥 (不改变请直接回车):")
    new_api_key = getpass.getpass("> ")
    
    if not new_api_key:
        if current_api_key:
            logger.log("保持当前API密钥不变")
            sys.exit(0)
        else:
            logger.log("❌ 未提供API密钥，无法继续")
            sys.exit(1)
    
    # 测试新API密钥
    if test_api_key(new_api_key):
        # 更新.env文件
        update_api_key(env_file, new_api_key)
        logger.log("\n✅ API密钥已成功更新并测试通过")
    else:
        logger.log("\n⚠️ API密钥测试失败，是否仍要更新? (y/N)")
        choice = input("> ").lower()
        
        if choice == 'y':
            update_api_key(env_file, new_api_key)
            logger.log("⚠️ API密钥已更新，但测试失败，请检查配置")
        else:
            logger.log("❌ 操作已取消")

if __name__ == "__main__":
    main() 