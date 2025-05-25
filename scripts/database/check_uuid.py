#!/usr/bin/env python3
"""
检查Qdrant中特定UUID的数据或状态
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# 导入项目依赖
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse, ApiException
from common.logger import Logger

# 导入配置
from knowledge.config import (
    QDRANT_HOST, 
    QDRANT_PORT, 
    QDRANT_API_KEY, 
    QDRANT_PATH,
    ALL_COLLECTIONS
)

# 创建日志器
logger = Logger("qdrant_check")

def search_uuid_in_collections(uuid_str, client=None):
    """
    在所有集合中搜索特定UUID
    
    Args:
        uuid_str: 要搜索的UUID字符串
        client: Qdrant客户端实例，如果为None则创建
        
    Returns:
        dict: 搜索结果
    """
    logger.log(f"🔍 开始搜索UUID: {uuid_str}", role="system")
    
    results = {}
    
    try:
        # 如果未提供客户端，创建一个
        if client is None:
            if QDRANT_HOST and QDRANT_API_KEY:
                logger.log(f"🌥️ 连接Qdrant云服务: {QDRANT_HOST}", level="debug", role="system")
                client = QdrantClient(
                    host=QDRANT_HOST,
                    port=QDRANT_PORT,
                    api_key=QDRANT_API_KEY,
                    timeout=30,
                    prefer_grpc=False
                )
            else:
                logger.log(f"💻 使用本地Qdrant: {QDRANT_PATH}", level="debug", role="system")
                Path(QDRANT_PATH).parent.mkdir(parents=True, exist_ok=True)
                client = QdrantClient(path=QDRANT_PATH)
            
        # 获取所有集合
        try:
            collections = client.get_collections().collections
            collection_names = [c.name for c in collections]
            logger.log(f"📊 发现 {len(collection_names)} 个集合: {', '.join(collection_names)}", role="system")
        except Exception as e:
            logger.log(f"❌ 获取集合列表失败: {str(e)}", level="error", role="system")
            logger.log("⚠️ 尝试使用预定义的集合列表", level="warning", role="system")
            collection_names = ALL_COLLECTIONS
        
        # 在每个集合中搜索UUID
        for collection_name in collection_names:
            try:
                logger.log(f"🔎 在集合 '{collection_name}' 中搜索", level="debug", role="system")
                
                # 尝试通过ID搜索点
                try:
                    point = client.retrieve(
                        collection_name=collection_name,
                        ids=[uuid_str]
                    )
                    if point and len(point) > 0:
                        logger.log(f"✅ 在集合 '{collection_name}' 中找到匹配ID: {uuid_str}", role="system")
                        results[collection_name] = {
                            "by_id": point
                        }
                        continue
                except Exception as e:
                    logger.log(f"⚠️ 通过ID搜索失败: {str(e)}", level="debug", role="system")
                
                # 尝试通过过滤器搜索
                try:
                    # 构建搜索过滤器 - 尝试在各种可能的字段中查找
                    filter_expr = {
                        "$or": [
                            {"uuid": {"$eq": uuid_str}},
                            {"id": {"$eq": uuid_str}},
                            {"metadata.uuid": {"$eq": uuid_str}},
                            {"metadata.id": {"$eq": uuid_str}},
                            {"payload.uuid": {"$eq": uuid_str}},
                            {"payload.id": {"$eq": uuid_str}}
                        ]
                    }
                    
                    # 执行搜索
                    search_result = client.scroll(
                        collection_name=collection_name,
                        filter=filter_expr,
                        limit=10
                    )
                    
                    if search_result and search_result[0] and len(search_result[0]) > 0:
                        logger.log(f"✅ 在集合 '{collection_name}' 中找到 {len(search_result[0])} 个匹配记录", role="system")
                        if collection_name not in results:
                            results[collection_name] = {}
                        results[collection_name]["by_filter"] = search_result[0]
                except Exception as e:
                    logger.log(f"⚠️ 通过过滤器搜索失败: {str(e)}", level="debug", role="system")
                
            except Exception as e:
                logger.log(f"❌ 搜索集合 '{collection_name}' 时出错: {str(e)}", level="error", role="system")
        
        # 总结搜索结果
        if not results:
            logger.log(f"⚠️ 在所有集合中未找到UUID: {uuid_str}", level="warning", role="system")
        else:
            logger.log(f"✅ 在 {len(results)} 个集合中找到匹配记录", role="system")
            for collection, data in results.items():
                logger.log(f"  - {collection}: 发现 {sum(len(v) for v in data.values())} 个匹配", role="system")
        
        return results
        
    except Exception as e:
        logger.log(f"❌ 搜索过程出错: {str(e)}", level="error", role="system")
        return {}

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="检查Qdrant中特定UUID的状态")
    parser.add_argument("uuid", help="要检查的UUID")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    parser.add_argument("--local", "-l", action="store_true", help="强制使用本地Qdrant")
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.logger.setLevel("DEBUG")
    
    # 如果指定使用本地存储
    if args.local:
        original_host = os.environ.get("QDRANT_HOST")
        os.environ["QDRANT_HOST"] = ""
        logger.log("⚠️ 强制使用本地Qdrant存储", level="warning", role="system")
    
    # 搜索UUID
    results = search_uuid_in_collections(args.uuid)
    
    # 恢复环境变量
    if args.local and original_host:
        os.environ["QDRANT_HOST"] = original_host
    
    # 返回状态码
    return 0 if results else 1

if __name__ == "__main__":
    sys.exit(main()) 