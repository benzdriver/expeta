#!/usr/bin/env python3
"""
强制重置并配置Qdrant云服务。
修复配置文件、环境变量和模块缓存，彻底清理锁定。
"""

import os
import sys
import json
import time
import shutil
import argparse
from dotenv import load_dotenv
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 加载.env文件
load_dotenv()

# Qdrant云配置 - 从环境变量获取
QDRANT_HOST = os.environ.get("QDRANT_HOST")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

def reset_config_py():
    """重写config.py文件中的云设置"""
    if not QDRANT_HOST or not QDRANT_API_KEY:
        print("❌ 错误: 未设置QDRANT_HOST或QDRANT_API_KEY环境变量")
        print("请设置环境变量或在.env文件中添加这些变量")
        return False
        
    config_path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "config.py")
    
    print(f"📝 修改配置文件: {config_path}")
    
    with open(config_path, "r") as f:
        content = f.read()
    
    # 替换环境变量加载行
    new_content = []
    in_config_section = False
    
    for line in content.splitlines():
        # 跳过所有QDRANT环境变量加载行
        if "QDRANT_HOST" in line or "QDRANT_API_KEY" in line or "QDRANT_PORT" in line or "QDRANT_PATH" in line:
            if "=" in line:
                # 这是一个赋值行，我们将替换它
                continue
        
        # 保留其他行
        new_content.append(line)
    
    # 在导入后添加安全的环境变量加载代码
    config_section = '\n# Qdrant配置 - 从环境变量加载\n'
    config_section += 'import os\n'
    config_section += 'from dotenv import load_dotenv\n\n'
    config_section += '# 加载.env文件\n'
    config_section += 'load_dotenv()\n\n'
    config_section += '# Qdrant配置\n'
    config_section += 'QDRANT_HOST = os.environ.get("QDRANT_HOST")\n'
    config_section += 'QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))\n'
    config_section += 'QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")\n'
    config_section += 'QDRANT_PATH = "data/qdrant"  # 用于备用\n'
    
    # 在导入语句后插入配置
    import_end_index = 0
    for i, line in enumerate(new_content):
        if line.startswith("import") or line.startswith("from"):
            import_end_index = i + 1
    
    new_content.insert(import_end_index, config_section)
    
    # 写回文件
    with open(config_path, "w") as f:
        f.write("\n".join(new_content))
    
    print("✅ 已更新config.py以从环境变量加载Qdrant配置")
    return True

def create_test_connection():
    """测试连接并创建测试集合"""
    # 重新加载必要的模块
    if "knowledge.config" in sys.modules:
        del sys.modules["knowledge.config"]
    if "knowledge.vector_store" in sys.modules:
        del sys.modules["knowledge.vector_store"]
    
    # 检查环境变量
    if not QDRANT_HOST or not QDRANT_API_KEY:
        print("❌ 错误: 未设置QDRANT_HOST或QDRANT_API_KEY环境变量")
        return False
    
    # 导入必须在删除模块后执行
    from knowledge.vector_store import get_qdrant_client, init_collection
    from knowledge.config import QDRANT_HOST, QDRANT_API_KEY, QDRANT_PORT
    
    print("\n测试Qdrant云服务连接...")
    print(f"  HOST: {QDRANT_HOST}")
    print(f"  PORT: {QDRANT_PORT}")
    print(f"  API_KEY: {'*' * 10 + QDRANT_API_KEY[-5:] if QDRANT_API_KEY else '未设置'}")
    
    try:
        client = get_qdrant_client()
        print("✅ 成功连接到Qdrant云服务")
        
        # 列出集合
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        print(f"📊 现有集合: {collection_names}")
        
        # 创建测试集合
        test_collection = "test_connection"
        print(f"\n创建测试集合: {test_collection}")
        
        # 删除已存在的测试集合
        try:
            client.delete_collection(test_collection)
            print(f"🧹 已清理已存在的集合: {test_collection}")
        except:
            pass
        
        # 创建集合
        init_result = init_collection(test_collection)
        
        if init_result:
            print(f"✅ 测试集合创建成功")
            return True
        else:
            print(f"❌ 测试集合创建失败")
            return False
    except Exception as e:
        print(f"❌ 连接或创建集合失败: {e}")
        return False

def initialize_collections():
    """初始化所有必要的集合"""
    # 导入必须在前面函数已经删除模块后执行
    from knowledge.vector_store import init_all_collections
    
    print("\n初始化所有必要的集合...")
    success = init_all_collections()
    
    if success:
        print("✅ 所有集合初始化成功")
    else:
        print("❌ 部分集合初始化失败")
    
    return success

def force_clean_env():
    """强制清理环境变量和锁定"""
    # 清理本地Qdrant存储
    qdrant_path = os.path.join(os.path.dirname(__file__), "..", "data", "qdrant")
    
    if os.path.exists(qdrant_path):
        print(f"🧹 清理本地Qdrant存储: {qdrant_path}")
        try:
            shutil.rmtree(qdrant_path, ignore_errors=True)
            time.sleep(1)  # 等待文件系统操作完成
            print("✅ 本地存储清理完成")
        except Exception as e:
            print(f"⚠️ 清理本地存储时出错: {e}")
    
    # 创建空的本地存储目录
    os.makedirs(qdrant_path, exist_ok=True)
    
    # 检查环境变量
    if not QDRANT_HOST or not QDRANT_API_KEY:
        print("⚠️ 警告: 未设置QDRANT_HOST或QDRANT_API_KEY环境变量")
        return False
    
    print("✅ 环境变量已设置")
    return True

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="重置并配置Qdrant云服务")
    parser.add_argument("--host", help="Qdrant云服务主机地址")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant云服务端口")
    parser.add_argument("--key", help="Qdrant API密钥")
    return parser.parse_args()

def main():
    """主函数"""
    print("🚀 强制重置并配置Qdrant云服务...")
    
    # 解析命令行参数
    args = parse_args()
    
    # 如果命令行提供了参数，覆盖环境变量
    global QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY
    if args.host:
        QDRANT_HOST = args.host
        os.environ["QDRANT_HOST"] = QDRANT_HOST
    if args.port:
        QDRANT_PORT = args.port
        os.environ["QDRANT_PORT"] = str(QDRANT_PORT)
    if args.key:
        QDRANT_API_KEY = args.key
        os.environ["QDRANT_API_KEY"] = QDRANT_API_KEY
    
    # 检查必要的环境变量
    if not QDRANT_HOST or not QDRANT_API_KEY:
        print("❌ 错误: 未设置QDRANT_HOST或QDRANT_API_KEY")
        print("请通过以下方式设置:")
        print("1. 在.env文件中添加QDRANT_HOST和QDRANT_API_KEY")
        print("2. 设置环境变量QDRANT_HOST和QDRANT_API_KEY")
        print("3. 使用命令行参数: --host <主机地址> --key <API密钥>")
        return 1
    
    # 强制清理环境变量和锁定
    if not force_clean_env():
        print("⚠️ 环境清理过程中发现问题，但将继续执行")
    
    # 重写config.py文件
    if not reset_config_py():
        return 1
    
    # 测试连接并创建测试集合
    if not create_test_connection():
        print("\n❌ Qdrant云服务配置失败，请检查连接参数")
        return 1
    
    # 初始化所有必要的集合
    initialize_collections()
    
    print("\n🎉 Qdrant云服务配置完成！")
    print("您可以运行以下命令测试配置:")
    print("  ./scripts/run_tests.sh --test-db")
    print("  ./scripts/run_tests.sh --knowledge list")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 