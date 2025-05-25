"""
局部推理上下文构建模块。
为局部架构推理构建特定的上下文，包括实体信息、历史决策和相关知识。
"""

from typing import Dict, List, Optional, Any

from knowledge.context_retrieval import build_context_for_round

async def build_local_reasoning_context(
    entity_name: str,
    round_num: int,
    round_goal: str,
    current_summary: Dict[str, Any],
    previous_qa: List[Dict[str, str]],
    global_constraints: Optional[Dict[str, Any]] = None
) -> str:
    """
    构建局部推理上下文。
    
    Args:
        entity_name: 实体名称
        round_num: 当前轮次序号
        round_goal: 当前轮次目标
        current_summary: 当前实体摘要
        previous_qa: 之前轮次的问答历史
        global_constraints: 全局约束
        
    Returns:
        str: 格式化的上下文字符串
    """
    # 调用通用上下文构建函数
    context = await build_context_for_round(
        entity_name=entity_name,
        round_num=round_num,
        round_goal=round_goal,
        current_summary=current_summary,
        previous_qa=previous_qa,
        global_constraints=global_constraints
    )
    
    # 这里可以添加针对局部推理的特殊上下文增强
    local_specific_info = f"""
## 局部推理指导

在局部架构设计中，应重点关注以下方面：

1. **组件职责**：每个组件应有明确的单一职责
2. **接口设计**：定义清晰的接口和通信方式
3. **依赖关系**：维持合理的依赖关系，避免循环依赖
4. **内聚性**：保持高内聚，相关功能应该集中
5. **可测试性**：确保组件便于单元测试和集成测试

当前目标: {round_goal} (轮次 {round_num})
"""
    
    return context + local_specific_info

# 为兼容测试添加的函数
async def build_reasoning_context(
    entity_name: str,
    entity_summary: Dict[str, Any],
    round_goal: str,
    previous_qa: List[Dict[str, str]] = None,
    global_constraints: Optional[Dict[str, Any]] = None
) -> str:
    """
    构建推理上下文(兼容测试用例)
    
    Args:
        entity_name: 实体名称
        entity_summary: 实体摘要
        round_goal: 推理目标
        previous_qa: 之前的问答历史
        global_constraints: 全局约束
        
    Returns:
        str: 格式化的上下文字符串
    """
    # 调用正式实现
    return await build_local_reasoning_context(
        entity_name=entity_name,
        round_num=1,  # 固定为第一轮
        round_goal=round_goal,
        current_summary=entity_summary,
        previous_qa=previous_qa or [],
        global_constraints=global_constraints
    )

async def build_context(
    entity_name: str,
    entity_summary: Dict[str, Any],
    global_constraints: Optional[Dict[str, Any]] = None
) -> str:
    """
    简化版的上下文构建函数。
    
    Args:
        entity_name: 实体名称
        entity_summary: 实体摘要
        global_constraints: 全局约束
        
    Returns:
        str: 格式化的上下文字符串
    """
    # 使用兼容函数，默认设置为深度架构精细化阶段
    return await build_reasoning_context(
        entity_name=entity_name,
        entity_summary=entity_summary,
        round_goal="深度架构精细化",
        previous_qa=[],
        global_constraints=global_constraints
    ) 