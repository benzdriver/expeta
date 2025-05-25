from common import print_log
"""
实体摘要更新模块。
基于推理问答结果，更新架构实体摘要，确保架构设计的完整性和一致性。
"""

from typing import Dict, List, Any, Tuple, Optional
import json

from llm_services.executor import run_prompt
from dependency import dependency_manager

async def update_entity_summary(
    entity_name: str,
    current_summary: Dict[str, Any],
    qa_history: List[Dict[str, str]],
    context: str,
    round_goal: str
) -> Dict[str, Any]:
    """
    基于问答历史更新实体架构摘要。
    
    Args:
        entity_name: 实体名称
        current_summary: 当前实体摘要
        qa_history: 问答历史
        context: 上下文信息
        round_goal: 当前推理目标
        
    Returns:
        Dict[str, Any]: 更新后的实体摘要
    """
    # 将当前摘要转为JSON字符串
    current_summary_json = json.dumps(current_summary, ensure_ascii=False, indent=2)
    
    # 格式化问答历史
    qa_text = ""
    for i, qa in enumerate(qa_history):
        qa_text += f"问题 {i+1}: {qa.get('question', '')}\n"
        qa_text += f"回答 {i+1}: {qa.get('answer', '')}\n\n"
    
    # 构建系统提示
    system_prompt = """你是一个精通软件架构的AI助手，专注于架构设计和文档生成。
    
你的任务是基于问答历史和上下文，更新软件模块的架构摘要JSON。

请注意以下关键点：
1. 保持JSON结构的完整性和有效性
2. 只更新与当前推理轮次相关的字段
3. 保留原有的有效信息，避免删除已有的架构细节
4. 确保更新后的架构更加完整、详细和一致
5. 新增信息应基于问答中获得的深入理解
6. 严格遵循系统的分层架构原则，上层组件可以依赖下层，但下层不应依赖上层
7. 避免引入循环依赖，谨慎添加新的depends_on关系
8. 优先使用抽象和接口隔离，而非直接依赖具体实现
9. 确保模块职责边界清晰，不与其他模块职责重叠

请输出完整的更新后JSON，不要包含任何额外解释。"""
    
    # 构建用户提示
    user_prompt = f"""请基于以下问答历史，更新"{entity_name}"模块的架构摘要JSON。

当前推理目标是：{round_goal}

### 当前架构摘要
```json
{current_summary_json}
```

### 问答历史
{qa_text}

### 上下文信息
{context}

### 依赖关系设计指南
在更新模块的depends_on字段时，请特别注意以下几点：
1. 确保依赖方向符合系统分层架构 - 通常是从上层组件依赖下层组件
2. 仔细评估每个新依赖的必要性，只添加真正需要的依赖
3. 优先考虑使用抽象接口而非直接依赖具体实现
4. 避免引入可能导致循环依赖的关系
5. 如果依赖关系较复杂，考虑是否可以通过重构模块边界来简化

请输出完整的更新后JSON，确保JSON结构有效，并且融合了问答中的深入分析。"""

    # 调用LLM更新摘要
    try:
        # 执行LLM请求
        response = await run_prompt(
            system_message=system_prompt,
            user_message=user_prompt,
            return_json=True  # 直接解析为JSON
        )
        
        # 检查返回是否有效
        if isinstance(response, dict) and response:
            # 验证依赖关系
            updated_summary = await validate_dependencies(entity_name, response, current_summary)
            return updated_summary
        else:
            # 如果返回格式不正确，尝试解析文本响应
            try:
                if isinstance(response, str):
                    # 尝试从文本响应中提取JSON
                    json_str = extract_json_from_text(response)
                    parsed_response = json.loads(json_str)
                    # 验证依赖关系
                    updated_summary = await validate_dependencies(entity_name, parsed_response, current_summary)
                    return updated_summary
            except:
                pass
                
            # 如果解析失败，返回原摘要
            print_log(f"摘要更新失败，返回原摘要", level="error")
            return current_summary
        
    except Exception as e:
        print_log(f"摘要更新发生错误: {e}", level="error")
        return current_summary  # 返回原摘要

def extract_json_from_text(text: str) -> str:
    """从文本中提取JSON字符串"""
    # 尝试查找 ```json ... ``` 格式
    import re
    json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    match = re.search(json_pattern, text)
    if match:
        return match.group(1)
    
    # 如果没有找到代码块，尝试直接解析为JSON
    return text 

async def validate_dependencies(
    entity_name: str,
    updated_summary: Dict[str, Any],
    current_summary: Dict[str, Any]
) -> Dict[str, Any]:
    """
    验证新的依赖关系是否会造成循环依赖或层次违规，如果存在问题则进行调整。

    Args:
        entity_name: 实体名称
        updated_summary: 更新后的摘要
        current_summary: 当前摘要

    Returns:
        Dict[str, Any]: 最终调整后的摘要
    """
    # 获取更新后的依赖列表
    new_dependencies = updated_summary.get("depends_on", [])
    old_dependencies = current_summary.get("depends_on", [])

    # 如果依赖没有变化，直接返回更新后的摘要
    if set(new_dependencies) == set(old_dependencies):
        return updated_summary

    print_log(f"检查 {entity_name} 的依赖关系...", level="info")
    print_log(f"旧依赖: {old_dependencies}", level="debug")
    print_log(f"新依赖: {new_dependencies}", level="debug")

    # 初始化依赖管理器
    dm = dependency_manager.DependencyManager()
    
    # 预测依赖变更的影响
    impact = dm.predict_dependency_impact(entity_name, new_dependencies)
    
    # 分析预测结果
    has_cycles = False
    has_violations = False
    
    if "potential_cycles" in impact and impact["potential_cycles"]:
        has_cycles = True
        cycles = impact["potential_cycles"]
        print_log(f"⚠️ 预测到可能的循环依赖: {cycles}", level="warning")
    
    if "layer_violations" in impact and impact["layer_violations"]:
        has_violations = True
        violations = impact["layer_violations"]
        print_log(f"⚠️ 预测到可能的层次违规: {violations}", level="warning")
    
    # 如果没有问题，更新依赖并返回
    if not has_cycles and not has_violations:
        # 更新依赖
        result = dm.update_dependencies(entity_name, new_dependencies)
        print_log(f"✅ 依赖检查通过，无循环依赖或层次违规", level="info")
        return updated_summary
    
    # 存在问题，尝试修复
    if has_cycles:
        print_log(f"需要修复循环依赖问题", level="info")
        fixed_summary = await fix_circular_dependencies(
            entity_name, 
            updated_summary, 
            impact["potential_cycles"]
        )
        return fixed_summary
    
    if has_violations:
        print_log(f"需要修复层次违规问题", level="info")
        fixed_summary = await fix_layer_violations(
            entity_name, 
            updated_summary, 
            impact["layer_violations"]
        )
        return fixed_summary
    
    # 兜底方案，返回原始更新
    return updated_summary

async def fix_circular_dependencies(
    entity_name: str,
    updated_summary: Dict[str, Any],
    cycles: List[List[str]]
) -> Dict[str, Any]:
    """
    修复循环依赖，通过LLM重新评估依赖关系。
    
    Args:
        entity_name: 实体名称
        updated_summary: 更新后的摘要
        cycles: 检测到的循环依赖列表
        
    Returns:
        Dict[str, Any]: 修复后的摘要
    """
    # 初始化依赖管理器获取更多上下文
    dm = dependency_manager.DependencyManager()
    
    # 获取层次信息
    layer = None
    if entity_name in dm.graph:
        layer = dm.graph[entity_name].get("layer")
    if not layer:
        layer = dm.infer_layer(entity_name)
    
    # 获取可以依赖的层次
    allowed_layers = dm.layer_rules.get(layer, [])
    
    # 分析循环中每个模块的层次
    cycle_analysis = []
    for cycle in cycles:
        cycle_info = []
        for module in cycle:
            module_layer = "未知"
            if module in dm.graph:
                module_layer = dm.graph[module].get("layer") or dm.infer_layer(module)
            cycle_info.append(f"{module} ({module_layer})")
        cycle_analysis.append(" -> ".join(cycle_info))
    
    # 格式化循环依赖信息
    cycles_text = "\n".join(cycle_analysis)
    
    # 将摘要转为JSON字符串
    summary_json = json.dumps(updated_summary, ensure_ascii=False, indent=2)
    
    system_prompt = """你是一个精通软件架构的AI助手，专注于解决架构依赖问题。
    
你的任务是分析并修复模块依赖中的循环依赖问题。循环依赖是指模块之间互相依赖形成环状结构，
这在架构设计中是一种反模式，会导致代码紧耦合、难以测试和维护。

请仔细分析循环依赖路径，并按照以下原则修复问题：
1. 遵循架构分层原则，上层模块可以依赖下层模块，但下层模块不应依赖上层
2. 尽量减少对模块职责的影响
3. 可以移除不必要的依赖
4. 考虑引入抽象层或接口打破循环
5. 调整模块边界和职责
6. 保持架构的整体合理性和层次结构

请修改JSON摘要中的depends_on字段，返回修复后的完整JSON结构。"""
    
    user_prompt = f"""我检测到模块 "{entity_name}" 的依赖关系中存在循环依赖问题。

### 模块层次信息
- 当前模块: {entity_name} (层次: {layer})
- 该层次允许依赖的层: {', '.join(allowed_layers)}

### 循环依赖路径（带层次信息）
{cycles_text}

### 当前模块摘要
```json
{summary_json}
```

请分析这些循环依赖，并修改模块的depends_on列表以消除循环依赖。
你需要考虑模块的职责和层次，以最小的架构影响解决问题。
遵循分层架构原则，确保每个模块只依赖允许的层次。

返回修复后的完整JSON摘要，确保修改后的依赖关系不会产生新的循环。"""

    try:
        # 调用LLM修复循环依赖
        fixed_summary = await run_prompt(
            system_message=system_prompt,
            user_message=user_prompt,
            return_json=True
        )
        
        if isinstance(fixed_summary, dict) and fixed_summary:
            print_log(f"✅ 循环依赖已修复", level="info")
            
            # 再次验证修复结果
            new_deps = fixed_summary.get("depends_on", [])
            impact = dm.predict_dependency_impact(entity_name, new_deps)
            
            if impact.get("potential_cycles"):
                print_log(f"⚠️ 循环依赖修复不完全，但已改善", level="warning")
            
            return fixed_summary
        else:
            print_log(f"修复循环依赖失败，返回原摘要", level="error")
            return updated_summary
            
    except Exception as e:
        print_log(f"修复循环依赖时出错: {e}", level="error")
        return updated_summary

async def fix_layer_violations(
    entity_name: str,
    updated_summary: Dict[str, Any],
    violations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    修复层次违规问题，通过LLM重新评估依赖关系。
    
    Args:
        entity_name: 实体名称
        updated_summary: 更新后的摘要
        violations: 检测到的层次违规列表
        
    Returns:
        Dict[str, Any]: 修复后的摘要
    """
    # 初始化依赖管理器获取更多上下文
    dm = dependency_manager.DependencyManager()
    
    # 获取层次信息
    layer = None
    if entity_name in dm.graph:
        layer = dm.graph[entity_name].get("layer")
    if not layer:
        layer = dm.infer_layer(entity_name)
    
    # 获取可以依赖的层次
    allowed_layers = dm.layer_rules.get(layer, [])
    
    # 格式化违规信息
    violations_text = []
    for v in violations:
        dep = v.get("dependency", "未知")
        dep_layer = v.get("dependency_layer", "未知")
        violations_text.append(f"- {dep} (层次: {dep_layer}) - 违反了分层原则，{layer}层不应依赖{dep_layer}层")
    
    violations_text = "\n".join(violations_text)
    
    # 将摘要转为JSON字符串
    summary_json = json.dumps(updated_summary, ensure_ascii=False, indent=2)
    
    system_prompt = """你是一个精通软件架构的AI助手，专注于解决架构分层问题。
    
你的任务是分析并修复模块依赖中的层次违规问题。良好的架构应该遵循分层原则，
上层模块可以依赖下层模块，但下层模块不应依赖上层模块。

请仔细分析层次违规，并按照以下原则修复问题：
1. 严格遵循架构分层原则
2. 尽量减少对模块职责的影响
3. 移除或替换不符合分层规则的依赖
4. 考虑引入抽象层或依赖倒置原则
5. 调整模块边界和职责
6. 保持架构的整体合理性

请修改JSON摘要中的depends_on字段，返回修复后的完整JSON结构。"""
    
    user_prompt = f"""我检测到模块 "{entity_name}" 的依赖关系中存在层次违规问题。

### 模块层次信息
- 当前模块: {entity_name} (层次: {layer})
- 该层次允许依赖的层: {', '.join(allowed_layers)}

### 层次违规问题
{violations_text}

### 当前模块摘要
```json
{summary_json}
```

请分析这些层次违规，并修改模块的depends_on列表以解决问题。
你需要考虑模块的职责和架构分层，以最小的架构影响解决问题。
遵循分层架构原则，确保每个模块只依赖允许的层次。

返回修复后的完整JSON摘要。"""

    try:
        # 调用LLM修复层次违规
        fixed_summary = await run_prompt(
            system_message=system_prompt,
            user_message=user_prompt,
            return_json=True
        )
        
        if isinstance(fixed_summary, dict) and fixed_summary:
            print_log(f"✅ 层次违规已修复", level="info")
            
            # 再次验证修复结果
            new_deps = fixed_summary.get("depends_on", [])
            impact = dm.predict_dependency_impact(entity_name, new_deps)
            
            if impact.get("layer_violations"):
                print_log(f"⚠️ 层次违规修复不完全，但已改善", level="warning")
            
            return fixed_summary
        else:
            print_log(f"修复层次违规失败，返回原摘要", level="error")
            return updated_summary
            
    except Exception as e:
        print_log(f"修复层次违规时出错: {e}", level="error")
        return updated_summary 