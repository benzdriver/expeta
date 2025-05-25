#!/usr/bin/env python3
"""
为Qdrant集合创建必要的索引。
解决403权限错误，使实体查询能正常工作。
"""

import os
import sys
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_collection_indexes():
    """为所有集合创建必要的字段索引"""
    # 导入必要的模块
    if "knowledge.config" in sys.modules:
        del sys.modules["knowledge.config"]
    if "knowledge.vector_store" in sys.modules:
        del sys.modules["knowledge.vector_store"]
    
    from knowledge.vector_store import get_qdrant_client
    from knowledge.config import ALL_COLLECTIONS, ENTITY_COLLECTION, GLOBAL_DECISIONS_COLLECTION
    from qdrant_client.models import PayloadSchemaType
    
    print("🔍 为Qdrant集合创建索引...")
    
    # 获取客户端
    client = get_qdrant_client()
    
    # 显示当前配置
    from knowledge.config import QDRANT_HOST, QDRANT_PORT
    print(f"  连接到: {QDRANT_HOST}:{QDRANT_PORT}")
    
    # 检查集合
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]
    print(f"  现有集合: {collection_names}")
    
    # 为每个集合创建索引
    for collection_name in ALL_COLLECTIONS:
        if collection_name not in collection_names:
            print(f"⚠️ 集合不存在: {collection_name}，跳过")
            continue
        
        print(f"\n📊 处理集合: {collection_name}")
        
        # 创建常用元数据字段的索引
        fields_to_index = [
            # 基本元数据索引
            {"field_name": "metadata.entity_name", "field_type": PayloadSchemaType.TEXT},
            {"field_name": "metadata.entity_type", "field_type": PayloadSchemaType.KEYWORD},
            {"field_name": "metadata.is_entity", "field_type": PayloadSchemaType.BOOL},
            {"field_name": "metadata.description", "field_type": PayloadSchemaType.TEXT},
            
            # 全局决策相关索引
            {"field_name": "metadata.system_name", "field_type": PayloadSchemaType.KEYWORD},
            {"field_name": "metadata.is_global_decision", "field_type": PayloadSchemaType.BOOL},
            {"field_name": "metadata.decision_count", "field_type": PayloadSchemaType.INTEGER},
            
            # 时间戳索引
            {"field_name": "metadata.timestamp", "field_type": PayloadSchemaType.TEXT},
        ]
        
        # 创建索引
        for field in fields_to_index:
            try:
                print(f"  - 创建索引: {field['field_name']} ({field['field_type']})")
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field["field_name"],
                    field_schema=field["field_type"]
                )
                print(f"    ✅ 索引创建成功")
            except Exception as e:
                # 可能索引已存在
                print(f"    ⚠️ 索引创建失败: {e}")
    
    print("\n✅ 所有索引创建完成")
    return True

def test_entity_list():
    """测试实体列表功能"""
    # 重新加载模块以确保最新配置
    if "knowledge.entity_storage" in sys.modules:
        del sys.modules["knowledge.entity_storage"]
        
    from knowledge.entity_storage import list_entities
    
    print("\n🧪 测试实体列表功能...")
    try:
        entities = list_entities()
        print(f"✅ 实体列表测试成功: 找到 {len(entities)} 个实体")
        if entities:
            print(f"  实体列表: {entities}")
    except Exception as e:
        print(f"❌ 实体列表测试失败: {e}")
        return False
    
    return True

def create_test_entity():
    """创建测试实体"""
    from knowledge.entity_storage import store_entity
    
    print("\n📝 创建测试实体...")
    test_entity = {
        "module": "TestModule",
        "description": "这是一个用于测试的实体",
        "details": {
            "purpose": "测试Qdrant云服务连接和索引",
            "type": "测试",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    try:
        result = store_entity("TestEntity", test_entity)
        if result:
            print(f"✅ 测试实体创建成功")
            return True
        else:
            print(f"❌ 测试实体创建失败")
            return False
    except Exception as e:
        print(f"❌ 测试实体创建异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始为Qdrant集合创建索引...")
    
    # 创建索引
    if not create_collection_indexes():
        print("❌ 索引创建失败")
        return 1
        
    # 创建测试实体
    create_test_entity()
    
    # 测试实体列表功能
    test_entity_list()
    
    print("\n🎉 Qdrant云服务索引创建完成!")
    print("您可以运行以下命令进行测试:")
    print("  ./scripts/run_tests.sh --knowledge list")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 