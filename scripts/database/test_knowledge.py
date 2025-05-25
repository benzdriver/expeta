#!/usr/bin/env python3
"""
测试知识库模块功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from langchain_core.documents import Document
from knowledge.config import DOCS_COLLECTION
from knowledge.vector_store import (
    get_qdrant_client,
    create_vector_store,
    get_vector_store,
    clean_collection
)

# 测试数据
TEST_DOCS = [
    Document(
        page_content="这是一个测试文档，用于验证Qdrant云存储功能",
        metadata={"source": "test", "id": "doc1"}
    ),
    Document(
        page_content="Qdrant是一个向量搜索引擎，提供高效的相似度搜索功能",
        metadata={"source": "test", "id": "doc2"}
    ),
    Document(
        page_content="Expeta系统使用向量存储来管理和检索知识库中的文档",
        metadata={"source": "test", "id": "doc3"}
    )
]

def test_connection():
    """测试连接"""
    print("测试Qdrant连接...")
    try:
        client = get_qdrant_client()
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        print(f"✅ 连接成功! 发现 {len(collection_names)} 个集合:")
        for name in collection_names:
            print(f"  - {name}")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return False

def test_create_store():
    """测试创建向量存储"""
    print("\n测试创建向量存储...")
    collection_name = f"{DOCS_COLLECTION}_test"
    
    try:
        # 清理可能存在的集合
        clean_collection(collection_name)
        
        # 创建向量存储
        store = create_vector_store(
            documents=TEST_DOCS,
            collection_name=collection_name,
            recreate=True
        )
        
        if store:
            print(f"✅ 成功创建测试集合: {collection_name}")
            return collection_name
        else:
            print("❌ 创建向量存储失败")
            return None
    except Exception as e:
        print(f"❌ 创建向量存储异常: {str(e)}")
        return None

def test_similarity_search(collection_name):
    """测试相似度搜索"""
    print("\n测试相似度搜索...")
    
    if not collection_name:
        print("⚠️ 跳过搜索测试 (无集合)")
        return
    
    try:
        # 获取向量存储
        store = get_vector_store(collection_name)
        
        if not store:
            print("❌ 获取向量存储失败")
            return
        
        # 执行搜索
        query = "Qdrant向量搜索"
        results = store.similarity_search(query, k=2)
        
        print(f"✅ 搜索成功，找到 {len(results)} 个结果:")
        for i, doc in enumerate(results):
            print(f"\n结果 {i+1}:")
            print(f"  - 内容: {doc.page_content}")
            print(f"  - 来源: {doc.metadata.get('source')}")
            print(f"  - ID: {doc.metadata.get('id')}")
    except Exception as e:
        print(f"❌ 搜索测试异常: {str(e)}")

def main():
    """主函数"""
    print("🧪 知识库模块功能测试")
    print("====================")
    
    # 测试连接
    if not test_connection():
        print("❌ 连接测试失败，无法继续")
        return 1
    
    # 测试创建向量存储
    collection_name = test_create_store()
    
    # 测试相似度搜索
    test_similarity_search(collection_name)
    
    # 清理测试集合
    if collection_name:
        try:
            clean_collection(collection_name)
            print(f"\n✅ 已清理测试集合: {collection_name}")
        except:
            pass
    
    print("\n✅ 测试完成")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 