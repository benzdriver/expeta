import re
from typing import Dict, List, Tuple, Any
from clarifier_v2.rag_retriever import embedding_retrieve, retrieve_entity_summaries

# 可信度级别定义
CONFIDENCE_LEVELS = {
    "verified": 0.8,    # 高可信度 - 完全接受
    "inferred": 0.5,    # 中等可信度 - 推断但合理
    "needs_verification": 0.2,  # 低可信度 - 需要验证
    "hallucination": 0.0        # 极低可信度 - 可能是幻觉
}

def suggest_naming_corrections(entity_name: str) -> List[str]:
    """为不符合命名规范的实体名称提供修正建议
    
    Args:
        entity_name: 实体名称
        
    Returns:
        suggestions: 命名建议列表
    """
    suggestions = []
    
    # 检查是否缺少后缀
    if re.match(r'^[A-Z][a-zA-Z]*$', entity_name) and not any([
        entity_name.endswith(suffix) for suffix in 
        ["Service", "Repository", "Controller", "Component", "Page", "Model", "Entity"]
    ]):
        # 基于实体名称猜测可能的类型
        if "Service" in entity_name or "Provider" in entity_name:
            suggestions.append(f"{entity_name}Service")
        elif "Repo" in entity_name or "Data" in entity_name or "Store" in entity_name:
            suggestions.append(f"{entity_name}Repository")
        elif "Control" in entity_name or "Api" in entity_name or "Endpoint" in entity_name:
            suggestions.append(f"{entity_name}Controller")
        elif "UI" in entity_name or "View" in entity_name or "Element" in entity_name:
            suggestions.append(f"{entity_name}Component")
        else:
            # 通用建议
            suggestions.append(f"{entity_name}Service")
            suggestions.append(f"{entity_name}Component")
            suggestions.append(f"{entity_name}Entity")
    
    # 检查驼峰命名是否不规范
    if not re.match(r'^[A-Z]', entity_name) and not re.match(r'^use[A-Z]', entity_name):
        # 首字母大写
        corrected = entity_name[0].upper() + entity_name[1:]
        suggestions.append(corrected)
        
        # React Hooks特殊处理
        if "use" in entity_name.lower() and not entity_name.startswith("use"):
            hook_name = "use" + corrected.replace("Use", "")
            suggestions.append(hook_name)
    
    # 检查是否是使用了下划线的蛇形命名法
    if '_' in entity_name:
        # 转换为驼峰命名
        parts = entity_name.split('_')
        camel_case = parts[0].capitalize() + ''.join(p.capitalize() for p in parts[1:])
        suggestions.append(camel_case)
        
        # 可能的类型后缀
        suggestions.append(f"{camel_case}Service")
        suggestions.append(f"{camel_case}Component")
    
    return suggestions

def validate_entity_existence(entity_name: str, all_text: str, entity_summaries: List[Dict]) -> Tuple[float, List[str]]:
    """验证实体存在性，返回可信度评分
    
    Args:
        entity_name: 实体名称
        all_text: 所有文档内容
        entity_summaries: 已有的实体摘要列表
        
    Returns:
        confidence: 可信度评分 (0.0-1.0)
        reasons: 支持理由列表
    """
    confidence = 0.0
    reasons = []
    
    # 第一层：精确匹配 - 检查实体名称是否直接出现在文档中
    if entity_name in all_text:
        confidence += 0.5
        reasons.append("实体名称直接出现在文档中")
    
    # 第二层：向量搜索 - 通过语义相似性查找
    context = embedding_retrieve(entity_name, all_text)
    if len(context) > 100:  # 有足够相关上下文
        confidence += 0.3
        reasons.append("找到语义相关的上下文")
    
    # 第三层：已有实体摘要验证 - 检查是否已在其他摘要中被引用
    references = 0
    for summary in entity_summaries:
        # 检查依赖关系
        if "dependencies" in summary and entity_name in summary.get("dependencies", []):
            references += 1
        
        # 检查backend部分的各个字段
        backend = summary.get("backend", {})
        for section in ["services", "controllers", "repositories"]:
            section_items = backend.get(section, [])
            if isinstance(section_items, list) and entity_name in section_items:
                references += 1
        
        # 检查dtos
        dtos = backend.get("dtos", {})
        if isinstance(dtos, dict) and entity_name in dtos:
            references += 1
    
    if references > 0:
        confidence += min(0.2 * references, 0.4)  # 最多加0.4
        reasons.append(f"被{references}个其他实体引用")
    
    # 第四层：命名规范验证 - 检查命名是否符合项目技术栈规范
    # 后端命名模式
    backend_patterns = [
        r'^[A-Z][a-zA-Z]*Service$',          # 服务层
        r'^[A-Z][a-zA-Z]*Repository$',       # 数据访问层
        r'^[A-Z][a-zA-Z]*Controller$',       # 控制器
        r'^[A-Z][a-zA-Z]*Dto$',              # 数据传输对象
        r'^[A-Z][a-zA-Z]*Entity$',           # 实体类
        r'^[A-Z][a-zA-Z]*Model$'             # 模型类
    ]
    
    # 前端命名模式 (React/Next.js)
    frontend_patterns = [
        r'^[A-Z][a-zA-Z]*Component$',        # React组件
        r'^[A-Z][a-zA-Z]*Page$',             # 页面组件
        r'^[A-Z][a-zA-Z]*Provider$',         # Context提供者
        r'^[A-Z][a-zA-Z]*Context$',          # React Context
        r'^use[A-Z][a-zA-Z]*$',              # React Hooks
        r'^[A-Z][a-zA-Z]*View$',             # 视图组件
        r'^[A-Z][a-zA-Z]*Dialog$',           # 对话框组件
        r'^[A-Z][a-zA-Z]*Modal$',            # 模态框组件
        r'^[A-Z][a-zA-Z]*Card$'              # 卡片组件
    ]
    
    # TypeScript类型定义模式
    type_patterns = [
        r'^I[A-Z][a-zA-Z]*$',                # 接口(Interface)
        r'^T[A-Z][a-zA-Z]*$',                # 类型参数(Type)
        r'^[A-Z][a-zA-Z]*Type$',             # 类型定义
        r'^[A-Z][a-zA-Z]*Interface$'         # 接口定义
    ]
    
    # 状态管理模式
    state_patterns = [
        r'^[A-Z][a-zA-Z]*Store$',            # 状态存储
        r'^[A-Z][a-zA-Z]*Action$',           # Redux Action
        r'^[A-Z][a-zA-Z]*Reducer$',          # Redux Reducer
        r'^[A-Z][a-zA-Z]*State$',            # 状态定义
        r'^[A-Z][a-zA-Z]*Hook$'              # 自定义Hook
    ]
    
    # 检查是否匹配任何模式
    all_patterns = backend_patterns + frontend_patterns + type_patterns + state_patterns
    pattern_types = ["后端", "前端", "类型", "状态管理"]
    
    for pattern in all_patterns:
        if re.match(pattern, entity_name):
            pattern_type = ""
            if pattern in backend_patterns:
                pattern_type = "后端"
            elif pattern in frontend_patterns:
                pattern_type = "前端"
            elif pattern in type_patterns:
                pattern_type = "类型"
            else:
                pattern_type = "状态管理"
                
            confidence += 0.1
            reasons.append(f"命名符合{pattern_type}规范")
            break
    
    return confidence, reasons

def classify_entity(entity_name: str, confidence: float, summary: Dict) -> Tuple[Dict, str]:
    """根据可信度分类和处理实体
    
    Args:
        entity_name: 实体名称
        confidence: 可信度评分
        summary: 实体摘要
        
    Returns:
        enhanced_summary: 处理后的摘要
        status: 实体状态 (verified/inferred/needs_verification/hallucination)
    """
    # 添加验证信息
    if "validation" not in summary:
        summary["validation"] = {}
    
    summary["validation"]["confidence_score"] = confidence
    
    # 检查命名规范性
    # 获取所有命名模式
    backend_patterns = [r'^[A-Z][a-zA-Z]*Service$', r'^[A-Z][a-zA-Z]*Repository$', 
                        r'^[A-Z][a-zA-Z]*Controller$', r'^[A-Z][a-zA-Z]*Dto$',
                        r'^[A-Z][a-zA-Z]*Entity$', r'^[A-Z][a-zA-Z]*Model$']
    frontend_patterns = [r'^[A-Z][a-zA-Z]*Component$', r'^[A-Z][a-zA-Z]*Page$',
                         r'^[A-Z][a-zA-Z]*Provider$', r'^[A-Z][a-zA-Z]*Context$',
                         r'^use[A-Z][a-zA-Z]*$', r'^[A-Z][a-zA-Z]*View$',
                         r'^[A-Z][a-zA-Z]*Dialog$', r'^[A-Z][a-zA-Z]*Modal$',
                         r'^[A-Z][a-zA-Z]*Card$']
    type_patterns = [r'^I[A-Z][a-zA-Z]*$', r'^T[A-Z][a-zA-Z]*$',
                    r'^[A-Z][a-zA-Z]*Type$', r'^[A-Z][a-zA-Z]*Interface$']
    state_patterns = [r'^[A-Z][a-zA-Z]*Store$', r'^[A-Z][a-zA-Z]*Action$',
                     r'^[A-Z][a-zA-Z]*Reducer$', r'^[A-Z][a-zA-Z]*State$',
                     r'^[A-Z][a-zA-Z]*Hook$']
    all_patterns = backend_patterns + frontend_patterns + type_patterns + state_patterns
    
    # 检查命名是否符合任一模式
    naming_valid = any(re.match(pattern, entity_name) for pattern in all_patterns)
    
    if not naming_valid:
        # 生成命名建议
        naming_suggestions = suggest_naming_corrections(entity_name)
        if naming_suggestions:
            summary["validation"]["naming_issue"] = True
            summary["validation"]["naming_suggestions"] = naming_suggestions
            print(f"⚠️ 命名不规范: {entity_name}，建议修改为: {', '.join(naming_suggestions[:3])}")
            
            # 降低命名不规范实体的可信度
            confidence = max(confidence - 0.1, 0)
            summary["validation"]["confidence_score"] = confidence
    
    # 根据可信度分级
    if confidence >= CONFIDENCE_LEVELS["verified"]:
        print(f"✅ 高可信度实体 ({confidence:.2f}): {entity_name}")
        summary["validation"]["confidence_level"] = "verified"
        return summary, "verified"
        
    elif confidence >= CONFIDENCE_LEVELS["inferred"]:
        print(f"🟨 中等可信度实体 ({confidence:.2f}): {entity_name}")
        summary["validation"]["confidence_level"] = "inferred"
        return summary, "inferred"
        
    elif confidence >= CONFIDENCE_LEVELS["needs_verification"]:
        print(f"⚠️ 低可信度实体 ({confidence:.2f}): {entity_name}")
        summary["validation"]["confidence_level"] = "needs_verification"
        return summary, "needs_verification"
        
    else:
        print(f"❌ 不可信实体 ({confidence:.2f}): {entity_name}")
        summary["validation"]["confidence_level"] = "hallucination"
        return summary, "hallucination"

def validate_dependencies(summary: Dict, all_text: str, entity_summaries: List[Dict]) -> Dict:
    """验证依赖关系合理性
    
    Args:
        summary: 实体摘要
        all_text: 所有文档内容
        entity_summaries: 已有的实体摘要列表
        
    Returns:
        validated_summary: 更新后的摘要
    """
    if "dependencies" not in summary or not summary["dependencies"]:
        return summary
        
    dependencies = summary["dependencies"]
    valid_deps = []
    uncertain_deps = []
    invalid_deps = []
    
    for dep in dependencies:
        # 验证每个依赖
        confidence, reasons = validate_entity_existence(dep, all_text, entity_summaries)
        
        if confidence >= CONFIDENCE_LEVELS["inferred"]:
            valid_deps.append(dep)
        elif confidence >= CONFIDENCE_LEVELS["needs_verification"]:
            uncertain_deps.append({
                "name": dep,
                "confidence": confidence,
                "reasons": reasons
            })
        else:
            invalid_deps.append({
                "name": dep,
                "confidence": confidence,
                "reasons": reasons
            })
    
    # 更新依赖列表
    summary["dependencies"] = valid_deps
    
    # 添加验证信息
    if "validation" not in summary:
        summary["validation"] = {}
        
    if uncertain_deps:
        summary["validation"]["uncertain_dependencies"] = uncertain_deps
        
    if invalid_deps:
        summary["validation"]["invalid_dependencies"] = invalid_deps
        
    return summary

def enhance_with_evidence(entity_name: str, all_text: str, summary: Dict) -> Dict:
    """使用文档证据增强摘要
    
    Args:
        entity_name: 实体名称
        all_text: 所有文档内容
        summary: 实体摘要
        
    Returns:
        enhanced_summary: 增强后的摘要
    """
    context = embedding_retrieve(entity_name, all_text)
    
    # 提取最相关的段落
    paragraphs = context.split('\n\n')
    relevant = []
    
    # 按相关性排序
    scored_paragraphs = []
    for p in paragraphs:
        if len(p.strip()) < 10:  # 跳过太短的段落
            continue
            
        score = 0
        if entity_name in p:
            score += 5
            
        # 检查模块名或部分匹配
        parts = entity_name.split('/')
        for part in parts:
            if part and len(part) > 3 and part in p:
                score += 2
                
        # 检查是否包含相关关键词
        keywords = ["service", "controller", "repository", "function", "api", "endpoint"]
        for kw in keywords:
            if kw in p.lower():
                score += 1
                
        if score > 0:
            scored_paragraphs.append((score, p))
    
    # 取得分最高的两段
    scored_paragraphs.sort(reverse=True)
    relevant = [p for _, p in scored_paragraphs[:2]]
    
    if relevant:
        if "validation" not in summary:
            summary["validation"] = {}
            
        summary["validation"]["documentation_evidence"] = relevant
        
    return summary

def analyze_dependency_graph(all_summaries: Dict[str, Dict]) -> Dict:
    """分析整个依赖关系图，检查一致性
    
    Args:
        all_summaries: 所有实体摘要的字典 {entity_name: summary}
        
    Returns:
        分析结果，包含孤立节点、悬空引用和循环依赖
    """
    # 建立实体关系图
    graph = {}
    for entity_name, summary in all_summaries.items():
        graph[entity_name] = {
            "deps": summary.get("dependencies", []),
            "references": []  # 谁依赖了这个实体
        }
    
    # 填充引用信息
    for entity_name, info in graph.items():
        for dep in info["deps"]:
            if dep in graph:
                graph[dep]["references"].append(entity_name)
    
    # 检查孤立节点（没有依赖也没被依赖）
    isolated = [name for name, info in graph.items() 
               if not info["deps"] and not info["references"]]
    
    # 检查悬空引用（依赖了不存在的实体）
    dangling = []
    for name, info in graph.items():
        for dep in info["deps"]:
            if dep not in graph:
                dangling.append((name, dep))
    
    # 发现循环依赖
    cycles = find_cycles(graph)
    
    return {
        "isolated": isolated,
        "dangling": dangling,
        "cycles": cycles,
        "graph": graph
    }

def find_cycles(graph: Dict[str, Dict]) -> List[List[str]]:
    """在依赖图中查找循环依赖
    
    Args:
        graph: 依赖关系图 {entity: {deps: [], references: []}}
        
    Returns:
        循环依赖路径列表
    """
    cycles = []
    visited = set()
    path = []
    
    def dfs(node):
        if node in path:
            # 找到循环，截取循环部分
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
            
        if node in visited:
            return
            
        visited.add(node)
        path.append(node)
        
        for dep in graph.get(node, {}).get("deps", []):
            if dep in graph:
                dfs(dep)
                
        path.pop()
    
    # 对每个节点执行DFS
    for node in graph:
        path = []
        dfs(node)
    
    # 去重
    unique_cycles = []
    seen = set()
    for cycle in cycles:
        # 标准化循环，从最小元素开始
        min_idx = cycle.index(min(cycle))
        norm_cycle = tuple(cycle[min_idx:] + cycle[:min_idx])
        if norm_cycle not in seen:
            seen.add(norm_cycle)
            unique_cycles.append(list(norm_cycle))
    
    return unique_cycles

def apply_naming_correction(entity_name: str, corrected_name: str, entity_summaries: Dict[str, Dict]) -> Dict[str, Dict]:
    """应用命名修正，更新实体名称
    
    Args:
        entity_name: 原实体名称
        corrected_name: 修正后的名称
        entity_summaries: 实体摘要字典 {entity_name: summary}
        
    Returns:
        updated_summaries: 更新后的实体摘要字典
    """
    if entity_name not in entity_summaries:
        print(f"❌ 实体 {entity_name} 未找到，无法应用命名修正")
        return entity_summaries
    
    # 获取原实体摘要
    summary = entity_summaries[entity_name]
    
    # 如果修正后的名称已存在，需要合并
    if corrected_name in entity_summaries:
        print(f"⚠️ 实体 {corrected_name} 已存在，将合并信息")
        
        # 简单实现：保留修正后名称的摘要，但添加原实体的关键信息
        # 在实际应用中，可以实现更复杂的合并逻辑
        merged_summary = entity_summaries[corrected_name]
        
        # 记录合并信息
        if "merged_from" not in merged_summary:
            merged_summary["merged_from"] = []
        merged_summary["merged_from"].append(entity_name)
        
        # 合并依赖关系
        if "dependencies" in summary and summary["dependencies"]:
            if "dependencies" not in merged_summary:
                merged_summary["dependencies"] = []
            merged_summary["dependencies"].extend([dep for dep in summary["dependencies"] 
                                                if dep not in merged_summary["dependencies"]])
        
        # 更新验证信息
        if "validation" in summary:
            if "validation" not in merged_summary:
                merged_summary["validation"] = {}
            
            # 合并验证理由
            if "documentation_evidence" in summary["validation"]:
                if "documentation_evidence" not in merged_summary["validation"]:
                    merged_summary["validation"]["documentation_evidence"] = []
                merged_summary["validation"]["documentation_evidence"].extend(
                    summary["validation"].get("documentation_evidence", [])
                )
        
        # 删除原实体
        del entity_summaries[entity_name]
        
        # 更新引用
        for ent_name, ent_summary in entity_summaries.items():
            if "dependencies" in ent_summary and entity_name in ent_summary["dependencies"]:
                # 替换依赖中的引用
                ent_summary["dependencies"] = [corrected_name if dep == entity_name else dep 
                                             for dep in ent_summary["dependencies"]]
        
        return entity_summaries
        
    # 标准情况：重命名实体
    # 创建新实体
    entity_summaries[corrected_name] = summary
    
    # 添加重命名信息
    entity_summaries[corrected_name]["renamed_from"] = entity_name
    
    # 更新命名验证信息
    if "validation" in entity_summaries[corrected_name]:
        entity_summaries[corrected_name]["validation"]["naming_corrected"] = True
        if "naming_issue" in entity_summaries[corrected_name]["validation"]:
            del entity_summaries[corrected_name]["validation"]["naming_issue"]
        if "naming_suggestions" in entity_summaries[corrected_name]["validation"]:
            del entity_summaries[corrected_name]["validation"]["naming_suggestions"]
    
    # 删除原实体
    del entity_summaries[entity_name]
    
    # 更新其他实体的引用
    for ent_name, ent_summary in entity_summaries.items():
        if "dependencies" in ent_summary and entity_name in ent_summary["dependencies"]:
            # 替换依赖中的引用
            ent_summary["dependencies"] = [corrected_name if dep == entity_name else dep 
                                         for dep in ent_summary["dependencies"]]
    
    print(f"✅ 实体命名已从 {entity_name} 修正为 {corrected_name}")
    return entity_summaries

def auto_correct_entities(entity_summaries: Dict[str, Dict], all_text: str, 
                           remove_hallucinations: bool = True) -> Dict[str, Dict]:
    """自动修正所有实体的命名问题，处理幻觉实体
    
    Args:
        entity_summaries: 实体摘要字典 {entity_name: summary}
        all_text: 所有文档内容
        remove_hallucinations: 是否删除识别为幻觉的实体
        
    Returns:
        corrected_summaries: 修正后的实体摘要
    """
    corrected_summaries = entity_summaries.copy()
    entities_to_remove = []
    entities_to_rename = {}
    
    print("===== 开始自动实体修正 =====")
    
    # 第一遍：评估所有实体
    for entity_name, summary in corrected_summaries.items():
        # 验证实体
        confidence, reasons = validate_entity_existence(entity_name, all_text, list(corrected_summaries.values()))
        updated_summary, status = classify_entity(entity_name, confidence, summary)
        corrected_summaries[entity_name] = updated_summary
        
        # 处理幻觉实体
        if status == "hallucination" and remove_hallucinations:
            entities_to_remove.append(entity_name)
            print(f"🗑️ 标记删除幻觉实体: {entity_name}")
        
        # 收集需要重命名的实体
        elif "validation" in updated_summary and "naming_suggestions" in updated_summary["validation"]:
            # 选择第一个建议
            suggestion = updated_summary["validation"]["naming_suggestions"][0]
            entities_to_rename[entity_name] = suggestion
            print(f"✏️ 标记重命名: {entity_name} -> {suggestion}")
    
    # 第二遍：先执行重命名
    for old_name, new_name in entities_to_rename.items():
        if old_name in corrected_summaries:  # 确保实体还存在（可能已被其他操作删除）
            corrected_summaries = apply_naming_correction(old_name, new_name, corrected_summaries)
    
    # 第三遍：删除幻觉实体
    for entity_name in entities_to_remove:
        if entity_name in corrected_summaries:  # 确保实体还存在（可能已被重命名）
            # 记录删除信息 - 可选的日志记录
            print(f"❌ 删除幻觉实体: {entity_name}")
            
            # 更新依赖关系
            for name, summary in corrected_summaries.items():
                if "dependencies" in summary and entity_name in summary["dependencies"]:
                    summary["dependencies"].remove(entity_name)
                    # 可以添加一个标记，指示有依赖被删除
                    if "validation" not in summary:
                        summary["validation"] = {}
                    if "removed_dependencies" not in summary["validation"]:
                        summary["validation"]["removed_dependencies"] = []
                    summary["validation"]["removed_dependencies"].append(entity_name)
            
            # 删除实体
            del corrected_summaries[entity_name]
    
    print(f"✅ 实体修正完成: 重命名 {len(entities_to_rename)} 个实体, 删除 {len(entities_to_remove)} 个幻觉实体")
    return corrected_summaries

# 更新示例使用
if __name__ == "__main__":
    # 创建一些示例实体摘要
    sample_summaries = {
        "userService": {
            "description": "用户服务模块",
            "dependencies": ["authHandler", "userRepo", "fakeEntity"]
        },
        "authHandler": {
            "description": "认证处理模块",
            "dependencies": ["userService"]
        },
        "userRepo": {
            "description": "用户数据库访问模块",
            "dependencies": []
        },
        "fakeEntity": {
            "description": "这是一个虚构的实体，在文档中找不到",
            "dependencies": []
        }
    }
    
    # 验证实体名称
    all_text = "这是一个包含userService和authHandler的示例文档内容，也提到了userRepo"
    
    print("==== 原始实体状态 ====")
    for name, summary in sample_summaries.items():
        confidence, reasons = validate_entity_existence(name, all_text, list(sample_summaries.values()))
        print(f"实体: {name}, 可信度: {confidence:.2f}")
    
    print("\n==== 自动修正所有实体 ====")
    # 自动修正，包括删除幻觉实体
    corrected_summaries = auto_correct_entities(sample_summaries, all_text, remove_hallucinations=True)
    
    print("\n==== 修正后实体状态 ====")
    for name, summary in corrected_summaries.items():
        print(f"实体: {name}")
        print(f"  描述: {summary.get('description', '无描述')}")
        print(f"  依赖: {', '.join(summary.get('dependencies', []))}")
        if "renamed_from" in summary:
            print(f"  重命名自: {summary['renamed_from']}")
        if "validation" in summary and "removed_dependencies" in summary["validation"]:
            print(f"  已移除的依赖: {', '.join(summary['validation']['removed_dependencies'])}")
        print("") 