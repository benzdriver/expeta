#!/usr/bin/env python3
"""
配置比较和连接测试脚本
比较环境变量与curl脚本中的配置，并使用不同方式测试连接
"""

import os
import sys
import requests
import dotenv
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

try:
    from qdrant_client import QdrantClient
except ImportError:
    print("❌ 缺少依赖: qdrant_client")
    print("请安装: pip install qdrant-client")
    sys.exit(1)

# 加载环境变量
env_file = os.path.join(project_root, '.env')
if os.path.exists(env_file):
    dotenv.load_dotenv(env_file)

# Curl脚本中的配置
CURL_CONFIG = {
    "host": "c1d98dfd-eab2-4612-8517-987bc2256d34.us-west-2-0.aws.cloud.qdrant.io",
    "port": "6333",
    "api_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.obFWYTIHt2Wf9lUFqJskFvjwt9Xex4biGR4EIjGiOxc"
}

# 环境变量中的配置
ENV_CONFIG = {
    "host": os.environ.get('QDRANT_HOST', ''),
    "port": os.environ.get('QDRANT_PORT', ''),
    "api_key": os.environ.get('QDRANT_API_KEY', '')
}

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_config(title, config):
    """打印配置信息"""
    print(f"\n{title}:")
    print(f"  HOST: {config['host']}")
    print(f"  PORT: {config['port']}")
    
    if config['api_key']:
        masked_key = f"{config['api_key'][:8]}...{config['api_key'][-5:]}"
        print(f"  API_KEY: {masked_key}")
    else:
        print("  API_KEY: 未设置")

def check_configs_match():
    """检查两种配置是否匹配"""
    print("\n配置比较:")
    
    matches = True
    if ENV_CONFIG['host'] != CURL_CONFIG['host']:
        print(f"  ❌ HOST不匹配: {ENV_CONFIG['host']} != {CURL_CONFIG['host']}")
        matches = False
    else:
        print(f"  ✅ HOST匹配")
    
    if ENV_CONFIG['port'] != CURL_CONFIG['port']:
        print(f"  ❌ PORT不匹配: {ENV_CONFIG['port']} != {CURL_CONFIG['port']}")
        matches = False
    else:
        print(f"  ✅ PORT匹配")
    
    if ENV_CONFIG['api_key'] != CURL_CONFIG['api_key']:
        print(f"  ❌ API_KEY不匹配")
        print(f"    环境变量: {ENV_CONFIG['api_key'][:8]}...{ENV_CONFIG['api_key'][-5:] if ENV_CONFIG['api_key'] else ''}")
        print(f"    Curl脚本: {CURL_CONFIG['api_key'][:8]}...{CURL_CONFIG['api_key'][-5:]}")
        matches = False
    else:
        print(f"  ✅ API_KEY匹配")
    
    return matches

def test_with_requests(config):
    """使用requests库测试连接"""
    print(f"\n使用Requests测试 (配置: {config['host']}:{config['port']}):")
    
    try:
        url = f"https://{config['host']}:{config['port']}/collections"
        headers = {"api-key": config['api_key']}
        
        print(f"  请求URL: {url}")
        print(f"  请求头: api-key={config['api_key'][:8]}...{config['api_key'][-5:]}")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ 连接成功!")
            data = response.json()
            collections = data.get("result", {}).get("collections", [])
            if collections:
                collection_names = [c.get('name') for c in collections]
                print(f"  发现 {len(collection_names)} 个集合: {', '.join(collection_names)}")
            return True
        else:
            print(f"  ❌ 连接失败: {response.text}")
            return False
    except Exception as e:
        print(f"  ❌ 请求错误: {str(e)}")
        return False

def test_with_client(config):
    """使用qdrant_client库测试连接"""
    print(f"\n使用QdrantClient测试 (配置: {config['host']}:{config['port']}):")
    
    try:
        print(f"  连接参数:")
        print(f"    host={config['host']}")
        print(f"    port={config['port']}")
        print(f"    api_key={config['api_key'][:8]}...{config['api_key'][-5:]}")
        print(f"    prefer_grpc=False")
        print(f"    check_compatibility=False")
        
        client = QdrantClient(
            host=config['host'],
            port=int(config['port']),
            api_key=config['api_key'],
            timeout=30,
            prefer_grpc=False,
            check_compatibility=False
        )
        
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        print("  ✅ 客户端连接成功!")
        print(f"  发现 {len(collection_names)} 个集合: {', '.join(collection_names)}")
        return True
    except Exception as e:
        print(f"  ❌ 客户端连接错误: {str(e)}")
        return False

def update_env_config():
    """更新环境变量配置，使其与curl脚本一致"""
    print("\n更新环境变量配置...")
    
    os.environ['QDRANT_HOST'] = CURL_CONFIG['host']
    os.environ['QDRANT_PORT'] = CURL_CONFIG['port']
    os.environ['QDRANT_API_KEY'] = CURL_CONFIG['api_key']
    
    # 更新全局变量
    ENV_CONFIG['host'] = CURL_CONFIG['host']
    ENV_CONFIG['port'] = CURL_CONFIG['port']
    ENV_CONFIG['api_key'] = CURL_CONFIG['api_key']
    
    print("✅ 环境变量已更新为curl脚本中的配置")

def main():
    """主函数"""
    print_header("Qdrant配置比较和连接测试")
    
    # 打印两种配置
    print_config("环境变量配置", ENV_CONFIG)
    print_config("Curl脚本配置", CURL_CONFIG)
    
    # 比较配置
    configs_match = check_configs_match()
    
    # 使用环境变量配置测试
    env_requests_ok = test_with_requests(ENV_CONFIG)
    env_client_ok = test_with_requests(ENV_CONFIG)
    
    # 使用curl脚本配置测试
    curl_requests_ok = test_with_requests(CURL_CONFIG)
    curl_client_ok = test_with_client(CURL_CONFIG)
    
    # 如果配置不匹配且curl配置成功
    if not configs_match and (curl_requests_ok or curl_client_ok):
        print("\n检测到配置不匹配，但curl脚本配置可以成功连接。")
        
        # 更新环境变量
        update_env_config()
        
        # 再次测试
        print("\n使用更新后的环境变量重新测试:")
        env_requests_ok = test_with_requests(ENV_CONFIG)
        env_client_ok = test_with_client(ENV_CONFIG)
    
    # 总结
    print_header("测试结果总结")
    print(f"环境变量配置 + Requests: {'✅ 成功' if env_requests_ok else '❌ 失败'}")
    print(f"环境变量配置 + QdrantClient: {'✅ 成功' if env_client_ok else '❌ 失败'}")
    print(f"Curl脚本配置 + Requests: {'✅ 成功' if curl_requests_ok else '❌ 失败'}")
    print(f"Curl脚本配置 + QdrantClient: {'✅ 成功' if curl_client_ok else '❌ 失败'}")
    
    # 永久更新.env文件
    if not configs_match and (curl_requests_ok or curl_client_ok):
        print("\n是否要将curl脚本的配置永久保存到.env文件? (y/N)")
        choice = input("> ").lower()
        
        if choice == 'y':
            try:
                dotenv.set_key(env_file, "QDRANT_HOST", CURL_CONFIG['host'])
                dotenv.set_key(env_file, "QDRANT_PORT", CURL_CONFIG['port'])
                dotenv.set_key(env_file, "QDRANT_API_KEY", CURL_CONFIG['api_key'])
                print(f"✅ 配置已保存到: {env_file}")
            except Exception as e:
                print(f"❌ 保存配置失败: {str(e)}")

if __name__ == "__main__":
    main() 