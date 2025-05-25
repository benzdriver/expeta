"""
上下文检索模块。
提供智能上下文构建功能，根据不同的推理目标和阶段，动态组装相关上下文。
结合文档、实体信息和推理历史，构建高质量的推理上下文。
"""
from typing import Dict, List, Optional, Any, Union
import json

from knowledge.config import logger, DEFAULT_TOP_K
from knowledge.vector_store import get_vector_store
from knowledge.entity_storage import retrieve_entity, retrieve_similar_entities
from knowledge.reasoning_memory import retrieve_related_reasoning, retrieve_entity_reasoning_history

async def build_context_for_round(
    entity_name: str,
    round_num: int,
    round_goal: str,
    current_summary: Dict[str, Any],
    previous_qa: List[Dict[str, str]],
    global_constraints: Optional[Dict[str, Any]] = None
) -> str:
    """
    为特定推理轮次构建上下文。
    
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
    # 1. 获取基础上下文
    base_context = retrieve_base_context(entity_name)
    
    # 2. 获取目标特定上下文
    goal_specific_context = get_goal_specific_context(round_goal, entity_name)
    
    # 3. 获取相关历史决策
    related_history = retrieve_decision_history(entity_name, round_goal, round_num)
    
    # 4. 格式化并返回上下文
    return format_context(
        entity_name=entity_name,
        base_context=base_context,
        global_constraints=global_constraints,
        previous_qa=previous_qa,
        related_history=related_history,
        goal_specific_context=goal_specific_context,
        current_summary=current_summary,
        round_num=round_num,
        round_goal=round_goal
    )

def retrieve_base_context(entity_name: str) -> str:
    """
    检索实体的基础上下文信息。
    
    Args:
        entity_name: 实体名称
        
    Returns:
        str: 基础上下文
    """
    # 获取实体本身信息，使用同步方式简化处理
    from knowledge.entity_storage import retrieve_entity_async, retrieve_entity
    
    try:
        # 直接使用同步版本，在集成测试中会被mock替换为异步版本
        entity = retrieve_entity(entity_name)
        
        context_parts = []
        
        if entity:
            # 添加实体基本信息
            context_parts.append(f"【实体信息】\n实体名称: {entity_name}\n")
            
            if "description" in entity:
                context_parts.append(f"实体描述: {entity['description']}\n")
                
            if "module" in entity:
                context_parts.append(f"模块类型: {entity['module']}\n")
        
        return "\n".join(context_parts)
    except Exception as e:
        logger.log(f"❌ 检索基础上下文失败: {e}", level="error", role="memory")
        return f"【实体信息】\n实体名称: {entity_name}\n"

def get_goal_specific_context(round_goal: str, entity_name: str) -> str:
    """
    根据当前推理目标获取特定上下文。
    
    Args:
        round_goal: 推理目标
        entity_name: 实体名称
        
    Returns:
        str: 目标特定上下文
    """
    # 基于目标获取相关实体和信息
    context_parts = []
    
    # 根据不同目标调整检索策略
    if round_goal == "上下文理解与基础架构识别":
        # 检索类似实体
        similar_entities = retrieve_similar_entities(entity_name, top_k=3)
        
        if similar_entities:
            context_parts.append("【类似实体参考】")
            for entity in similar_entities:
                context_parts.append(f"- {entity.get('name', 'unknown')}: {entity.get('description', '')}")
    
    elif round_goal == "架构模式与最佳实践应用":
        # 这里可以检索相关架构模式的知识
        # 从向量库检索与架构模式相关的内容
        context_parts.append("【相关架构模式】")
        context_parts.append("架构模式是解决特定架构问题的成熟解决方案。")
        
    elif round_goal == "一致性检查与冲突解决":
        # 检索相关依赖模块
        # 理想情况下，这里应该从项目分析中提取依赖关系
        context_parts.append("【相关依赖模块】")
        # 这里可以添加检测到的依赖模块信息
        
    elif round_goal == "深度架构精细化":
        # 检索性能、安全性相关的约束和最佳实践
        context_parts.append("【架构优化考量】")
        context_parts.append("在精细化阶段，需要考虑以下因素：")
        context_parts.append("1. 性能优化：识别性能瓶颈并应用适当的优化策略")
        context_parts.append("2. 安全性：确保适当的认证、授权和数据保护机制")
        context_parts.append("3. 可扩展性：设计能够应对增长的架构")
        context_parts.append("4. 可维护性：确保代码和架构易于理解和修改")
    
    return "\n".join(context_parts)

def retrieve_decision_history(entity_name: str, current_goal: str, round_num: int) -> str:
    """
    检索相关的历史决策记录。
    
    Args:
        entity_name: 实体名称
        current_goal: 当前推理目标
        round_num: 当前轮次
        
    Returns:
        str: 格式化的历史决策
    """
    # 获取实体的历史推理记录
    entity_history = retrieve_entity_reasoning_history(entity_name)
    
    # 获取类似目标的相关推理
    related_reasoning = retrieve_related_reasoning(
        query=current_goal,
        top_k=3,
        filter_dict={"reasoning_type": "local"}  # 只检索局部推理
    )
    
    history_parts = []
    
    # 添加实体自身的历史决策
    if entity_history:
        history_parts.append("【之前轮次的关键决策】")
        for record in entity_history:
            if record.get("round_goal") != current_goal:  # 避免重复当前目标的历史
                goal = record.get("round_goal", "未知目标")
                decisions = record.get("decisions", [])
                if decisions:
                    history_parts.append(f"- {goal}:")
                    for i, decision in enumerate(decisions[:3]):  # 限制每个目标最多3个决策
                        history_parts.append(f"  {i+1}. {decision[:100]}...")  # 限制长度
    
    # 添加相关实体的类似决策
    if related_reasoning:
        history_parts.append("\n【类似模块的相关决策】")
        for record in related_reasoning:
            entity = record.get("entity_name", "未知实体")
            if entity != entity_name:  # 避免重复
                goal = record.get("round_goal", "未知目标")
                decisions = record.get("decisions", [])
                if decisions:
                    history_parts.append(f"- {entity}/{goal}:")
                    for i, decision in enumerate(decisions[:2]):  # 限制每个实体最多2个决策
                        history_parts.append(f"  {i+1}. {decision[:100]}...")  # 限制长度
    
    return "\n".join(history_parts)

def retrieve_dependency_information(entity_name: str) -> str:
    """
    检索实体的依赖关系信息，包括依赖层次和潜在的循环依赖风险。
    
    Args:
        entity_name: 实体名称
        
    Returns:
        str: 依赖关系信息
    """
    try:
        # 导入依赖管理器
        from dependency import dependency_manager
        
        # 初始化依赖管理器
        dm = dependency_manager.DependencyManager()
        
        # 检查实体是否在依赖图中
        if entity_name not in dm.graph:
            return "【依赖信息】\n该模块尚未在依赖图中注册。设计时请遵循系统的分层架构，避免循环依赖。"
        
        # 获取依赖和被依赖信息
        depends_on = dm.graph[entity_name].get("depends_on", [])
        depended_by = dm.graph[entity_name].get("depended_by", [])
        
        # 获取层次信息
        layer = dm.graph[entity_name].get("layer")
        if not layer:
            layer = dm.infer_layer(entity_name)
            dm.graph[entity_name]["layer"] = layer
            
        # 获取复杂性指标
        complexity = dm.get_module_complexity(entity_name)
        
        # 检查是否存在循环依赖
        dependency_check = dm.check_circular_dependencies(entity_name)
        has_cycles = dependency_check.get("has_cycles", False)
        cycles = dependency_check.get("cycles", [])
        
        # 检查是否存在层次违规
        layer_check = dm.check_layer_violations(entity_name)
        has_violations = layer_check.get("has_violations", False)
        violations = layer_check.get("violations", [])
        
        # 获取允许依赖的层次
        allowed_layers = dm.layer_rules.get(layer, [])
        
        # 构建依赖信息文本
        info_parts = ["【依赖关系信息】"]
        
        # 添加层次位置
        info_parts.append(f"架构层次位置: {layer}")
        info_parts.append(f"允许依赖的层次: {', '.join(allowed_layers)}")
        
        # 添加复杂性指标
        if isinstance(complexity, dict) and "error" not in complexity:
            info_parts.append(f"\n模块复杂性:")
            info_parts.append(f"- 直接依赖数: {complexity.get('direct_dependencies', 0)}")
            info_parts.append(f"- 被直接依赖数: {complexity.get('direct_dependents', 0)}")
            info_parts.append(f"- 传递依赖数: {complexity.get('transitive_dependencies', 0)}")
            info_parts.append(f"- 传递被依赖数: {complexity.get('transitive_dependents', 0)}")
        
        # 添加依赖列表
        if depends_on:
            info_parts.append("\n依赖模块:")
            for dep in depends_on:
                # 获取依赖的层次
                dep_layer = "未知"
                if dep in dm.graph:
                    dep_layer = dm.graph[dep].get("layer") or dm.infer_layer(dep)
                
                # 检查是否违反层次规则
                layer_violation = dep_layer not in allowed_layers
                violation_mark = " ⚠️" if layer_violation else ""
                
                info_parts.append(f"- {dep} ({dep_layer}){violation_mark}")
        else:
            info_parts.append("\n依赖模块: 无")
        
        # 添加被依赖列表
        if depended_by:
            info_parts.append("\n被依赖模块:")
            for dep in depended_by:
                # 获取依赖方的层次
                dep_layer = "未知"
                if dep in dm.graph:
                    dep_layer = dm.graph[dep].get("layer") or dm.infer_layer(dep)
                info_parts.append(f"- {dep} ({dep_layer})")
        else:
            info_parts.append("\n被依赖模块: 无")
        
        # 添加循环依赖风险警告
        if has_cycles:
            info_parts.append("\n⚠️ 当前存在循环依赖风险:")
            for cycle in cycles:
                info_parts.append(f"- 循环路径: {' -> '.join(cycle)}")
            info_parts.append("\n设计时需要重点解决这些循环依赖问题。")
        
        # 添加层次违规警告
        if has_violations:
            filtered_violations = [v for v in violations if v["module"] == entity_name]
            if filtered_violations:
                info_parts.append("\n⚠️ 当前存在层次违规:")
                for violation in filtered_violations:
                    dep = violation["dependency"]
                    dep_layer = violation["dependency_layer"]
                    info_parts.append(f"- 违规依赖: {dep} ({dep_layer})")
                info_parts.append("\n设计时需要确保依赖符合系统的架构分层规则。")
        
        # 添加依赖设计指导原则
        info_parts.append("\n【依赖设计原则】")
        info_parts.append("1. 遵循自上而下的依赖方向（上层依赖下层，不反向依赖）")
        info_parts.append("2. 核心领域模型不应依赖基础设施或应用层")
        info_parts.append("3. 使用依赖注入或接口抽象来降低耦合度")
        info_parts.append("4. 引入新依赖时考虑其传递依赖影响")
        info_parts.append("5. 在模块边界设计时考虑职责划分，避免职责重叠")
        
        # 添加系统层次结构
        layer_structure = dm.get_layer_structure()
        info_parts.append("\n【系统架构层次】")
        for layer_name in dm.ARCHITECTURE_LAYERS:
            modules = layer_structure.get(layer_name, [])
            if modules:
                module_count = len(modules)
                sample_modules = ", ".join(modules[:3])
                if module_count > 3:
                    sample_modules += f"... (共{module_count}个)"
                info_parts.append(f"- {layer_name}: {sample_modules}")
        
        return "\n".join(info_parts)
    except Exception as e:
        logger.log(f"❌ 检索依赖信息失败: {e}", level="error", role="memory")
        return "【依赖信息】\n获取依赖信息时出错。请确保设计遵循系统分层原则，避免循环依赖。"

def format_context(
    entity_name: str,
    base_context: str,
    global_constraints: Optional[Dict[str, Any]],
    previous_qa: List[Dict[str, str]],
    related_history: str,
    goal_specific_context: str,
    current_summary: Dict[str, Any],
    round_num: int,
    round_goal: str
) -> str:
    """
    格式化完整上下文。
    
    Args:
        entity_name: 实体名称
        base_context: 基础上下文
        global_constraints: 全局约束
        previous_qa: 之前的问答历史
        related_history: 相关历史决策
        goal_specific_context: 目标特定上下文
        current_summary: 当前实体摘要
        round_num: 当前轮次
        round_goal: 当前目标
        
    Returns:
        str: 格式化的完整上下文
    """
    context_parts = []
    
    # 1. 顶部标题
    context_parts.append(f"# {entity_name} - 架构推理 (轮次 {round_num})")
    context_parts.append(f"## 当前目标: {round_goal}\n")
    
    # 2. 基础上下文
    context_parts.append("## 基础信息")
    context_parts.append(base_context)
    
    # 3. 当前实体摘要
    context_parts.append("\n## 当前架构摘要")
    context_parts.append(f"```json\n{current_summary}\n```\n")
    
    # 4. 依赖关系信息
    dependency_info = retrieve_dependency_information(entity_name)
    context_parts.append("\n## 依赖关系分析")
    context_parts.append(dependency_info)
    
    # 5. 目标特定上下文
    if goal_specific_context:
        context_parts.append("\n## 目标相关信息")
        context_parts.append(goal_specific_context)
    
    # 6. 相关历史决策
    if related_history:
        context_parts.append("\n## 相关历史决策")
        context_parts.append(related_history)
    
    # 7. 全局约束
    if global_constraints:
        context_parts.append("\n## 全局架构约束")
        for k, v in global_constraints.items():
            context_parts.append(f"- {k}: {v}")
    
    # 8. 之前轮次问答
    if previous_qa:
        context_parts.append("\n## 之前的推理问答")
        for i, qa in enumerate(previous_qa[-5:]):  # 只显示最近5个问答
            context_parts.append(f"Q{i+1}: {qa.get('question', '')}")
            context_parts.append(f"A{i+1}: {qa.get('answer', '')}")
            context_parts.append("")
    
    return "\n".join(context_parts)

def retrieve_similar_systems(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    collection_name: str = "system_examples",
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    检索与查询相似的系统示例。
    
    Args:
        query: 查询文本，通常是系统描述或问题
        top_k: 返回结果数量
        collection_name: 集合名称
        filter_dict: 过滤条件
        
    Returns:
        List[Dict[str, Any]]: 相似系统列表
    """
    try:
        # 使用向量存储检索相似系统
        vector_store = get_vector_store(collection_name)
        if vector_store is None:
            logger.log(f"⚠️ 系统示例集合不存在: {collection_name}", level="warning", role="memory")
            # 返回默认的示例系统
            return [
                {
                    "name": "移民申请SaaS平台",
                    "description": "为申请人提供加拿大移民申请流程指导、评估和表格处理的智能平台",
                    "architecture_style": "微服务架构",
                    "tech_stack": {
                        "frontend": "Next.js/React",
                        "backend": "Node.js/Express",
                        "database": "MongoDB",
                        "ai": "OpenAI API"
                    },
                    "similarity_score": 0.95
                },
                {
                    "name": "法律顾问匹配平台",
                    "description": "连接法律顾问与需要法律服务的客户的平台",
                    "architecture_style": "服务导向架构",
                    "tech_stack": {
                        "frontend": "Vue.js",
                        "backend": "Python/FastAPI",
                        "database": "PostgreSQL",
                        "ai": "Hugging Face模型"
                    },
                    "similarity_score": 0.85
                }
            ]
            
        # 执行相似度搜索
        results = vector_store.similarity_search_with_score(query, k=top_k, filter=filter_dict)
        
        # 解析结果
        similar_systems = []
        for doc, score in results:
            try:
                system_data = json.loads(doc.page_content)
                system_data["similarity_score"] = float(score)
                similar_systems.append(system_data)
            except Exception as e:
                logger.log(f"❌ 解析系统示例失败: {e}", level="error", role="memory")
                
        return similar_systems
    except Exception as e:
        logger.log(f"❌ 检索系统示例失败: {e}", level="error", role="memory")
        return [] 