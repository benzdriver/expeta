#!/usr/bin/env python3
"""
Qdrant云配置更新和测试脚本
用于更新API密钥并测试与Qdrant云的连接
"""

import os
import sys
import argparse
import dotenv
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# 导入项目依赖
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse, ApiException
from common.logger import Logger

# 创建日志器
logger = Logger("qdrant_config")

def load_env_config():
    """加载当前环境变量配置"""
    # 加载.env文件
    env_file = os.path.join(project_root, '.env')
    if os.path.exists(env_file):
        dotenv.load_dotenv(env_file)
    
    # 获取当前配置
    config = {
        'QDRANT_HOST': os.environ.get('QDRANT_HOST', ''),
        'QDRANT_PORT': os.environ.get('QDRANT_PORT', '6333'),
        'QDRANT_API_KEY': os.environ.get('QDRANT_API_KEY', '')
    }
    
    return config, env_file

def update_env_config(env_file, new_config):
    """更新.env文件中的配置"""
    # 读取当前.env文件内容
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # 处理每个配置项
    updated_lines = []
    updated_keys = set()
    
    # 更新现有行
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            updated_lines.append(line)
            continue
        
        if '=' in line:
            key, _ = line.split('=', 1)
            key = key.strip()
            
            if key in new_config and new_config[key]:
                updated_lines.append(f"{key}={new_config[key]}")
                updated_keys.add(key)
            else:
                updated_lines.append(line)
    
    # 添加未包含的配置项
    for key, value in new_config.items():
        if key not in updated_keys and value:
            updated_lines.append(f"{key}={value}")
    
    # 写回.env文件
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines) + '\n')
    
    logger.log(f"✅ 已更新配置文件: {env_file}", role="system")

def test_qdrant_connection(config):
    """测试Qdrant连接"""
    host = config.get('QDRANT_HOST')
    port = int(config.get('QDRANT_PORT', 6333))
    api_key = config.get('QDRANT_API_KEY')
    
    if not host:
        logger.log("❌ 未配置QDRANT_HOST，无法测试云连接", level="error", role="system")
        return False
    
    if not api_key:
        logger.log("❌ 未配置QDRANT_API_KEY，无法测试云连接", level="error", role="system")
        return False
    
    logger.log(f"🔌 测试连接到 {host}:{port}...", role="system")
    
    try:
        client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            timeout=30,
            prefer_grpc=False,
            check_compatibility=False  # 跳过版本兼容性检查
        )
        
        # 测试连接
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        logger.log(f"✅ 连接成功! 发现 {len(collection_names)} 个集合", role="system")
        if collection_names:
            logger.log(f"📊 集合列表: {', '.join(collection_names)}", role="system")
        
        return True
    except UnexpectedResponse as e:
        logger.log(f"❌ Qdrant API响应异常: {str(e)}", level="error", role="system")
        
        # 检查是否为认证错误
        if "403" in str(e) or "forbidden" in str(e).lower():
            logger.log("🔑 API密钥可能无效，请检查并更新", level="error", role="system")
        
        return False
    except Exception as e:
        logger.log(f"❌ 连接测试失败: {str(e)}", level="error", role="system")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Qdrant云配置更新和测试工具")
    parser.add_argument("--host", help="设置Qdrant云主机地址")
    parser.add_argument("--port", help="设置Qdrant端口")
    parser.add_argument("--api-key", help="设置Qdrant API密钥")
    parser.add_argument("--test", "-t", action="store_true", help="仅测试连接，不更新配置")
    args = parser.parse_args()
    
    # 加载当前配置
    current_config, env_file = load_env_config()
    
    logger.log("📋 当前Qdrant配置:", role="system")
    logger.log(f"  HOST: {current_config['QDRANT_HOST']}", role="system")
    logger.log(f"  PORT: {current_config['QDRANT_PORT']}", role="system")
    logger.log(f"  API_KEY: {'已配置' if current_config['QDRANT_API_KEY'] else '未配置'}", role="system")
    
    # 如果仅测试连接
    if args.test:
        test_qdrant_connection(current_config)
        return
    
    # 准备新配置
    new_config = {}
    if args.host:
        new_config['QDRANT_HOST'] = args.host
    if args.port:
        new_config['QDRANT_PORT'] = args.port
    if args.api_key:
        new_config['QDRANT_API_KEY'] = args.api_key
    
    # 如果有新配置，更新.env文件
    if new_config:
        logger.log("🔄 更新Qdrant配置...", role="system")
        for key, value in new_config.items():
            if key == 'QDRANT_API_KEY':
                logger.log(f"  {key}: {'*' * (len(value) - 8) + value[-8:] if value else '未设置'}", role="system")
            else:
                logger.log(f"  {key}: {value}", role="system")
        
        # 合并配置
        updated_config = {**current_config, **new_config}
        update_env_config(env_file, updated_config)
        
        # 重新加载环境变量
        for key, value in new_config.items():
            os.environ[key] = value
        
        # 测试连接
        test_qdrant_connection(updated_config)
    else:
        logger.log("ℹ️ 未提供新配置，保持当前设置", role="system")
        test_qdrant_connection(current_config)

if __name__ == "__main__":
    main() 