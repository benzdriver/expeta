"""
Knowledge模块的集中配置，管理向量存储、集合名称和路径等配置项。
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from common.logger import Logger

# 加载.env文件
load_dotenv()

# Qdrant配置 - 从环境变量加载
QDRANT_HOST = os.environ.get("QDRANT_HOST")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
QDRANT_PATH = "data/qdrant"  # 用于备用

# 创建Knowledge模块的logger实例
logger = Logger(name="knowledge")

# 向量存储集合配置 - 统一命名规范
DOCS_COLLECTION = os.getenv("QDRANT_DOCS_COLLECTION", "doc_index")
ENTITY_COLLECTION = os.getenv("QDRANT_ENTITY_COLLECTION", "entity_summaries")
REASONING_COLLECTION = os.getenv("QDRANT_REASONING_COLLECTION", "reasoning_log")
GLOBAL_DECISIONS_COLLECTION = os.getenv("QDRANT_GLOBAL_DECISIONS_COLLECTION", "global_decisions")

# 集合列表，用于初始化
ALL_COLLECTIONS = [
    DOCS_COLLECTION,
    ENTITY_COLLECTION,
    REASONING_COLLECTION,
    GLOBAL_DECISIONS_COLLECTION
]

# Qdrant连接配置

# 文档分块配置
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# 向量嵌入配置 
EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_SIZE = 1536  # 默认向量维度

# 输出路径
OUTPUT_PATH = Path("data/output/v2/smart_modules_final")

# 向量检索配置
DEFAULT_TOP_K = 5  # 默认检索数量 