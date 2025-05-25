"""
依赖推断模块
根据模块描述、职责和功能自动推断可能的依赖关系。
结合LLM分析、层级规则和模式匹配，提供全面的依赖关系预测。
"""

from typing import Dict, List, Any, Set, Tuple, Optional
import json
import re
from pathlib import Path

from common import print_log
from llm_services.executor import run_prompt
from dependency import dependency_manager

class DependencyInference:
    """依赖关系推断器，综合使用多种方法推断模块间的依赖关系"""
    
    def __init__(self):
        self.dm = dependency_manager.DependencyManager()
        
    async def infer_dependencies_from_modules(
        self, 
        modules: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        从模块列表中推断所有可能的依赖关系
        
        Args:
            modules: 模块列表，每个模块包含name、description、responsibilities等字段
            
        Returns:
            Dict[str, Dict[str, Any]]: 模块名到依赖信息的映射，包含显式、推断和层级依赖
        """
        dependency_map = {}
        
        # 第一步：从明确指定的依赖开始
        for module in modules:
            module_name = module.get("name", "")
            if not module_name:
                continue
                
            # 获取明确指定的依赖
            explicit_deps = module.get("depends_on", [])
            
            # 初始化依赖信息
            dependency_map[module_name] = {
                "explicit_dependencies": explicit_deps,
                "inferred_dependencies": [],
                "layer_based_dependencies": [],
                "final_dependencies": [],  # 将在合并阶段填充
                "confidence_scores": {}    # 每个依赖的置信度
            }
            
            # 为明确依赖分配高置信度
            for dep in explicit_deps:
                dependency_map[module_name]["confidence_scores"][dep] = 1.0  # 最高置信度
        
        # 第二步：根据描述推断依赖
        inferred_dependencies = await self._infer_dependencies_from_descriptions(modules)
        for module_name, inferred_deps in inferred_dependencies.items():
            if module_name in dependency_map:
                dependency_map[module_name]["inferred_dependencies"] = inferred_deps
                # 为推断依赖分配中等置信度
                for dep in inferred_deps:
                    if dep not in dependency_map[module_name]["confidence_scores"]:
                        dependency_map[module_name]["confidence_scores"][dep] = 0.7  # 中等置信度
        
        # 第三步：基于层级规则推断依赖
        layer_dependencies = await self._infer_dependencies_from_layers(modules)
        for module_name, layer_deps in layer_dependencies.items():
            if module_name in dependency_map:
                dependency_map[module_name]["layer_based_dependencies"] = layer_deps
                # 为层级依赖分配低等置信度
                for dep in layer_deps:
                    if dep not in dependency_map[module_name]["confidence_scores"]:
                        dependency_map[module_name]["confidence_scores"][dep] = 0.5  # 低等置信度
        
        # 第四步：合并所有依赖并应用置信度过滤
        for module_name, deps_info in dependency_map.items():
            # 合并所有来源的依赖
            all_deps = set(deps_info["explicit_dependencies"])
            all_deps.update(deps_info["inferred_dependencies"])
            all_deps.update(deps_info["layer_based_dependencies"])
            
            # 移除自身
            if module_name in all_deps:
                all_deps.remove(module_name)
            
            # 应用置信度过滤（可选）
            # final_deps = {dep for dep in all_deps if deps_info["confidence_scores"].get(dep, 0) >= 0.5}
            
            # 添加到最终依赖
            deps_info["final_dependencies"] = list(all_deps)
        
        return dependency_map
    
    async def validate_and_optimize_dependencies(
        self, 
        dependency_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        验证和优化依赖关系，解决循环依赖和层次违规
        
        Args:
            dependency_map: 模块名到依赖信息的映射
            
        Returns:
            Dict[str, List[str]]: 模块名到最终依赖列表的映射
        """
        optimized_deps = {}
        
        # 先创建一个临时的依赖图进行分析
        temp_dm = dependency_manager.DependencyManager()
        
        # 添加所有模块到临时依赖图
        for module_name, deps_info in dependency_map.items():
            final_deps = deps_info["final_dependencies"]
            temp_dm.add_module(module_name, final_deps)
        
        # 检测问题
        circular_check = temp_dm.check_circular_dependencies()
        layer_check = temp_dm.check_layer_violations()
        
        # 如果存在问题，进行自动修复
        has_issues = (circular_check.get("has_cycles", False) or 
                      layer_check.get("has_violations", False))
        
        if has_issues:
            print_log("检测到依赖问题，正在进行自动修复...", level="info")
            # 优先保留高置信度依赖，移除低置信度依赖中可能导致问题的部分
            for module_name, deps_info in dependency_map.items():
                # 按置信度排序依赖
                sorted_deps = sorted(
                    [(dep, deps_info["confidence_scores"].get(dep, 0)) 
                     for dep in deps_info["final_dependencies"]],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                # 逐步添加依赖，确保不引入问题
                optimal_deps = []
                for dep, score in sorted_deps:
                    # 尝试添加依赖
                    test_deps = optimal_deps + [dep]
                    
                    # 预测添加此依赖的影响
                    impact = temp_dm.predict_dependency_impact(module_name, test_deps)
                    
                    # 如果不会引入问题，或者这是高置信度依赖，则添加
                    has_new_issues = (impact.get("potential_cycles") or 
                                     impact.get("layer_violations"))
                    
                    if not has_new_issues or score >= 0.9:  # 高置信度依赖即使有问题也保留
                        optimal_deps.append(dep)
                
                # 更新为优化后的依赖
                optimized_deps[module_name] = optimal_deps
        else:
            # 如果没有问题，直接使用最终依赖
            for module_name, deps_info in dependency_map.items():
                optimized_deps[module_name] = deps_info["final_dependencies"]
        
        return optimized_deps
    
    async def _infer_dependencies_from_descriptions(
        self, 
        modules: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        根据模块描述推断可能的依赖关系
        
        Args:
            modules: 模块列表
            
        Returns:
            Dict[str, List[str]]: 模块名到推断依赖列表的映射
        """
        result = {}
        module_names = [m.get("name", "") for m in modules if m.get("name")]
        
        # 准备LLM的输入
        modules_json = json.dumps([{
            "name": m.get("name", ""),
            "description": m.get("description", ""),
            "responsibilities": m.get("responsibilities", []),
        } for m in modules if m.get("name")], indent=2, ensure_ascii=False)
        
        system_prompt = """你是一个专门分析软件架构依赖关系的AI专家。
你的任务是分析一组软件模块的描述和职责，推断它们之间可能存在的依赖关系。

依赖关系指的是一个模块在功能上需要使用另一个模块提供的服务、数据或功能。
请注意以下关键点：
1. 只推断有明确证据支持的依赖关系
2. 考虑模块描述中提到的"使用"、"调用"、"依赖"等明确词语
3. 分析模块职责之间的关系，如一个模块需要另一个模块的输出
4. 考虑常见的架构模式，例如UI层依赖服务层，服务层依赖数据层

你的输出应该是一个JSON对象，键为模块名，值为该模块可能依赖的其他模块列表。

必须严格按照以下格式返回：
{
  "模块名1": ["依赖模块1", "依赖模块2"],
  "模块名2": []
}

对于没有依赖的模块，使用空数组[]表示。确保为所有输入的模块返回一个条目，即使没有依赖关系。"""

        user_prompt = f"""请分析以下软件模块的描述和职责，推断它们之间可能存在的依赖关系：

模块列表：
```json
{modules_json}
```

可用的所有模块名称：{", ".join(module_names)}

请仔细分析每个模块的描述和职责，识别模块间可能的依赖关系。
依赖关系是指一个模块在功能上需要使用另一个模块提供的服务或数据。

以JSON格式返回推断的依赖关系，格式如下：
{{
  "模块A": ["模块B", "模块C"],  // 表示模块A依赖于模块B和模块C
  "模块B": ["模块D"],
  "模块C": []  // 没有依赖
}}

注意：
1. 只包含有足够证据支持的依赖关系
2. 模块不能依赖自身
3. 确保所有引用的模块名都在提供的模块列表中
4. 所有模块都必须在JSON结果中出现，没有依赖的模块用空数组表示"""

        try:
            # 调用LLM进行依赖推断
            inferred_deps = await run_prompt(
                system_message=system_prompt,
                user_message=user_prompt,
                return_json=True
            )
            
            if isinstance(inferred_deps, dict):
                result = inferred_deps
                print_log(f"成功从描述中推断出 {len(result)} 个模块的依赖关系", level="info")
            else:
                print_log(f"从描述推断依赖失败：返回格式不正确", level="error")
                # 回退策略：创建一个基本的空依赖图
                result = {module_name: [] for module_name in module_names}
                print_log(f"使用回退策略创建基本依赖图", level="info")
        except Exception as e:
            print_log(f"从描述推断依赖时出错: {e}", level="error")
            # 回退策略：使用简单的文本匹配
            print_log(f"使用简单文本匹配作为回退方案", level="info")
            result = {}
            
            # 为每个模块初始化空依赖列表
            for module in modules:
                module_name = module.get("name", "")
                if module_name:
                    result[module_name] = []
            
            # 使用简单的文本模式匹配寻找依赖
            for module in modules:
                module_name = module.get("name", "")
                description = module.get("description", "")
                
                if not module_name or not description:
                    continue
                
                # 查找描述中可能提到的其他模块名称
                for other_module in modules:
                    other_name = other_module.get("name", "")
                    if other_name and other_name != module_name and other_name in description:
                        # 检查上下文，确认这可能是依赖关系
                        context_words = ["使用", "调用", "依赖", "需要", "基于"]
                        for word in context_words:
                            if word in description and other_name in description.split(word)[1]:
                                result[module_name].append(other_name)
                                break
        
        return result
    
    async def _infer_dependencies_from_layers(
        self, 
        modules: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        基于架构层次规则推断依赖关系
        
        Args:
            modules: 模块列表
            
        Returns:
            Dict[str, List[str]]: 模块名到层级依赖列表的映射
        """
        result = {}
        
        # 为每个模块推断层级
        module_layers = {}
        for module in modules:
            module_name = module.get("name", "")
            if not module_name:
                continue
                
            # 尝试从模块信息获取层级
            layer = module.get("layer", "")
            
            # 如果未指定，使用依赖管理器推断
            if not layer or layer not in self.dm.ARCHITECTURE_LAYERS:
                layer = self.dm.infer_layer(module_name)
                
            module_layers[module_name] = layer
        
        # 按层级对模块进行分组
        layers_to_modules = {}
        for module_name, layer in module_layers.items():
            if layer not in layers_to_modules:
                layers_to_modules[layer] = []
            layers_to_modules[layer].append(module_name)
        
        # 应用层级依赖规则
        for module_name, layer in module_layers.items():
            # 获取此层可以依赖的层
            allowed_layers = self.dm.layer_rules.get(layer, [])
            
            # 从允许的层中随机选择一些模块作为依赖
            # 注意：这是启发式的，实际应用可能需要更复杂的规则
            layer_deps = []
            for allowed_layer in allowed_layers:
                if allowed_layer != layer and allowed_layer in layers_to_modules:
                    # 从每个允许的层最多选择2个模块
                    candidates = layers_to_modules[allowed_layer]
                    for candidate in candidates[:2]:  # 限制每层最多2个依赖
                        if candidate != module_name:
                            layer_deps.append(candidate)
            
            result[module_name] = layer_deps
        
        return result
    
    async def build_initial_dependency_graph(
        self, 
        modules: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        构建初始依赖图的主方法，结合多种推断方式
        
        Args:
            modules: 模块列表
            
        Returns:
            Dict[str, List[str]]: 模块名到依赖列表的映射
        """
        print_log("开始构建初始依赖图...", level="info")
        
        # 第一步：推断所有可能的依赖关系
        dependency_map = await self.infer_dependencies_from_modules(modules)
        
        # 第二步：验证和优化依赖关系
        optimized_deps = await self.validate_and_optimize_dependencies(dependency_map)
        
        # 第三步：更新依赖管理器
        for module_name, deps in optimized_deps.items():
            self.dm.update_dependencies(module_name, deps)
        
        # 可视化依赖图
        try:
            graph_path = self.dm.visualize(show_layers=True)
            print_log(f"初始依赖图可视化已保存到 {graph_path}", level="info")
        except Exception as e:
            print_log(f"依赖图可视化生成失败: {e}", level="warning")
        
        print_log(f"初始依赖图构建完成，共包含 {len(optimized_deps)} 个模块", level="info")
        
        return optimized_deps

# 便捷函数
async def build_initial_dependency_graph(modules: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    便捷函数，构建初始依赖图
    
    Args:
        modules: 模块列表
        
    Returns:
        Dict[str, List[str]]: 模块名到依赖列表的映射
    """
    inference = DependencyInference()
    return await inference.build_initial_dependency_graph(modules) 