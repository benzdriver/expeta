"""
Knowledge package for Expeta.
Provides vector storage, entity management, reasoning memory, and context retrieval functionality.
"""

from knowledge.vector_store import (
    get_qdrant_client,
    clean_collection,
    init_collection,
    init_all_collections,
    create_vector_store,
    get_vector_store
)

from knowledge.entity_storage import (
    store_entity,
    update_entity,
    retrieve_entity,
    retrieve_similar_entities,
    detect_entity_conflicts
)

from knowledge.reasoning_memory import (
    store_reasoning,
    retrieve_related_reasoning,
    retrieve_entity_reasoning_history,
    extract_decisions_from_qa
)

from knowledge.context_retrieval import (
    build_context_for_round,
    retrieve_base_context,
    get_goal_specific_context,
    retrieve_decision_history
)

# 初始化函数，可在应用启动时调用
def initialize_knowledge_system():
    """
    初始化知识系统，包括创建所有向量集合。
    在应用启动时调用此函数可确保所有必要的集合已存在。
    
    Returns:
        bool: 初始化是否成功
    """
    return init_all_collections()
