#!/usr/bin/env python3
"""
初始化Qdrant数据库脚本。
创建所有必要的集合，并检查连接状态。
"""

import os
import sys
import argparse
from pathlib import Path
import shutil
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledge.vector_store import init_all_collections, get_qdrant_client, clean_collection, init_collection
from knowledge.config import ALL_COLLECTIONS, QDRANT_PATH

def reset_local_db():
    """重置本地Qdrant数据库文件"""
    if os.path.exists(QDRANT_PATH):
        print(f"🧹 重置本地数据库路径: {QDRANT_PATH}")
        try:
            # 尝试删除锁文件
            lock_file = os.path.join(QDRANT_PATH, ".lock")
            if os.path.exists(lock_file):
                os.remove(lock_file)
                print(f"  - 已删除锁文件: {lock_file}")
            
            # 尝试删除集合目录
            for collection in ALL_COLLECTIONS:
                coll_dir = os.path.join(QDRANT_PATH, collection)
                if os.path.exists(coll_dir):
                    shutil.rmtree(coll_dir)
                    print(f"  - 已删除集合目录: {coll_dir}")
            
            time.sleep(0.5)  # 短暂等待确保文件系统操作完成
            return True
        except Exception as e:
            print(f"❌ 重置本地数据库失败: {e}")
            return False
    else:
        print(f"✅ 本地数据库路径不存在，将创建新路径: {QDRANT_PATH}")
        os.makedirs(QDRANT_PATH, exist_ok=True)
        return True

def initialize_db(force_recreate: bool = False):
    """初始化数据库集合"""
    print("🚀 开始初始化Qdrant数据库...")
    
    # 如果需要强制重建，先重置本地数据库
    if force_recreate:
        if not reset_local_db():
            print("⚠️ 本地数据库重置失败，继续尝试初始化...")
    
    # 检查Qdrant连接
    try:
        client = get_qdrant_client()
        print(f"✅ 成功连接到Qdrant服务")
        
        # 获取现有集合
        try:
            collections = client.get_collections().collections
            existing_collections = [c.name for c in collections]
            print(f"📊 现有集合: {existing_collections}")
        except Exception as e:
            print(f"❌ 获取集合列表失败: {e}")
            existing_collections = []
    except Exception as e:
        print(f"❌ 连接Qdrant失败: {e}")
        return False
    
    # 逐个初始化每个集合
    print("🔄 开始初始化集合...")
    for collection_name in ALL_COLLECTIONS:
        # 清理现有集合（如果需要）
        if force_recreate and collection_name in existing_collections:
            print(f"  - 清理集合: {collection_name}")
            clean_collection(collection_name)
        
        # 初始化集合
        print(f"  - 初始化集合: {collection_name}")
        success = init_collection(collection_name)
        if not success:
            print(f"    ❌ 初始化集合失败: {collection_name}")
        else:
            print(f"    ✅ 集合已就绪: {collection_name}")
    
    # 再次获取集合列表，确认初始化结果
    try:
        collections = client.get_collections().collections
        print(f"📊 初始化后的集合列表: {[c.name for c in collections]}")
        return True
    except Exception as e:
        print(f"❌ 获取集合列表失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="初始化Qdrant数据库")
    parser.add_argument("--force", "-f", action="store_true", help="强制重建所有集合（清除现有数据）")
    parser.add_argument("--reset", "-r", action="store_true", help="重置本地数据库（删除所有文件）")
    args = parser.parse_args()
    
    if args.reset:
        reset_local_db()
    
    initialize_db(force_recreate=args.force)

if __name__ == "__main__":
    main() 