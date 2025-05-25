from common import print_log
import json
from pathlib import Path
import re
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Set, Tuple, Optional, Any, Union

class DependencyManager:
    """管理模块依赖关系的类，提供实时更新和循环检测功能"""
    
    # 架构层次定义（由低到高）
    ARCHITECTURE_LAYERS = [
        "infrastructure",    # 基础设施层
        "data",              # 数据层
        "domain",            # 领域模型层
        "service",           # 服务层
        "application",       # 应用层
        "presentation",      # 展示层
        "testing"            # 测试层
    ]
    
    # 默认的层次依赖规则：键是依赖方，值是可以依赖的层
    DEFAULT_LAYER_RULES = {
        "infrastructure": ["infrastructure"],
        "data": ["infrastructure", "data"],
        "domain": ["infrastructure", "domain"],
        "service": ["infrastructure", "data", "domain", "service"],
        "application": ["infrastructure", "data", "domain", "service", "application"],
        "presentation": ["infrastructure", "data", "domain", "service", "application", "presentation"],
        "testing": ["infrastructure", "data", "domain", "service", "application", "presentation", "testing"]
    }
    
    def __init__(self, graph_path="data/output/dependency_graph.json"):
        self.graph_path = Path(graph_path)
        self.graph = self._load_graph()
        self._ensure_nx_graph()
        self.layer_rules = self.DEFAULT_LAYER_RULES.copy()
    
    def _load_graph(self):
        """加载或初始化依赖图"""
        if self.graph_path.exists():
            try:
                return json.loads(self.graph_path.read_text())
            except Exception as e:
                print_log(f"加载依赖图失败: {e}，创建新图")
        return {}
    
    def _ensure_nx_graph(self):
        """确保NetworkX图已创建并与当前依赖图同步"""
        self.digraph = nx.DiGraph()
        
        # 添加节点
        for module in self.graph:
            self.digraph.add_node(module)
        
        # 添加边
        for module, data in self.graph.items():
            for dep in data.get("depends_on", []):
                if dep in self.graph:  # 确保依赖存在
                    self.digraph.add_edge(module, dep)
    
    def save(self):
        """保存依赖图到文件"""
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.graph_path, 'w') as f:
            json.dump(self.graph, f, indent=2)
    
    def infer_layer(self, module_name: str) -> str:
        """根据模块名称或其他特征推断模块所在的架构层次"""
        # 已有明确定义的情况
        if module_name in self.graph and "layer" in self.graph[module_name]:
            return self.graph[module_name]["layer"]
        
        # 根据命名规则推断
        module_lower = module_name.lower()
        
        # 测试层检测
        if any(pattern in module_lower for pattern in ["test", "spec", "mock"]):
            return "testing"
        
        # 其他层次检测
        layer_patterns = {
            "infrastructure": ["config", "util", "helper", "constant", "infrastructure"],
            "data": ["repository", "dao", "entity", "model", "data"],
            "domain": ["domain", "model", "entity", "value", "aggregate"],
            "service": ["service", "manager", "provider", "factory"],
            "application": ["application", "app", "use-case", "usecase", "interactor"],
            "presentation": ["controller", "view", "presenter", "ui", "page", "component", "screen"]
        }
        
        for layer, patterns in layer_patterns.items():
            if any(pattern in module_lower for pattern in patterns):
                return layer
        
        # 基于拓扑结构推断
        try:
            in_degree = self.digraph.in_degree(module_name)
            out_degree = self.digraph.out_degree(module_name)
            
            if in_degree == 0 and out_degree > 0:
                return "presentation"  # 入度为0，可能是顶层模块
            elif in_degree > 0 and out_degree == 0:
                return "infrastructure"  # 出度为0，可能是底层模块
        except:
            pass
        
        # 默认返回服务层
        return "service"
    
    def update_module_layer(self, module_name: str, layer: str = None) -> None:
        """更新模块的架构层次"""
        if module_name not in self.graph:
            print_log(f"模块 {module_name} 不存在", level="warning")
            return
        
        if layer is None:
            layer = self.infer_layer(module_name)
        
        if layer not in self.ARCHITECTURE_LAYERS:
            print_log(f"无效的架构层次: {layer}", level="warning")
            return
        
        self.graph[module_name]["layer"] = layer
        self.save()
    
    def add_module(self, module_name, dependencies=None, layer=None):
        """添加新模块到依赖图"""
        if dependencies is None:
            dependencies = []
        
        if module_name not in self.graph:
            self.graph[module_name] = {
                "depends_on": dependencies,
                "depended_by": [],
                "layer": layer or self.infer_layer(module_name)
            }
        else:
            # 更新现有模块的依赖
            current_deps = set(self.graph[module_name].get("depends_on", []))
            current_deps.update(dependencies)
            self.graph[module_name]["depends_on"] = list(current_deps)
            
            # 更新层次信息（如果提供）
            if layer:
                self.graph[module_name]["layer"] = layer
        
        # 更新被依赖关系
        for dep in dependencies:
            if dep in self.graph:
                depended_by = set(self.graph[dep].get("depended_by", []))
                if module_name not in depended_by:
                    depended_by.add(module_name)
                    self.graph[dep]["depended_by"] = list(depended_by)
            else:
                # 如果依赖模块不存在，创建它
                inferred_layer = self.infer_layer(dep)
                self.graph[dep] = {
                    "depends_on": [],
                    "depended_by": [module_name],
                    "layer": inferred_layer
                }
        
        # 更新NetworkX图
        self.digraph.add_node(module_name)
        for dep in dependencies:
            self.digraph.add_node(dep)
            self.digraph.add_edge(module_name, dep)
        
        self.save()
        
        # 检查是否引入了循环依赖和层次违规
        circular_check = self.check_circular_dependencies(module_name)
        layer_check = self.check_layer_violations(module_name)
        
        return {
            "circular_dependency": circular_check,
            "layer_violations": layer_check
        }
    
    def remove_module(self, module_name):
        """从依赖图中移除模块"""
        if module_name in self.graph:
            # 移除被依赖关系
            for dep in self.graph[module_name].get("depends_on", []):
                if dep in self.graph and module_name in self.graph[dep].get("depended_by", []):
                    self.graph[dep]["depended_by"].remove(module_name)
            
            # 移除对此模块的依赖
            for mod, data in self.graph.items():
                if module_name in data.get("depends_on", []):
                    data["depends_on"].remove(module_name)
            
            # 删除模块
            del self.graph[module_name]
            
            # 更新NetworkX图
            if self.digraph.has_node(module_name):
                self.digraph.remove_node(module_name)
            
            self.save()
            return True
        return False
    
    def update_dependencies(self, module_name, new_dependencies):
        """更新模块的依赖，返回是否引入循环依赖和层次违规"""
        if module_name not in self.graph:
            return self.add_module(module_name, new_dependencies)
        
        # 提前分析依赖变更影响
        impact_analysis = self.predict_dependency_impact(module_name, new_dependencies)
        
        # 移除当前依赖关系
        old_dependencies = self.graph[module_name].get("depends_on", [])
        for dep in old_dependencies:
            if dep in self.graph and module_name in self.graph[dep].get("depended_by", []):
                self.graph[dep]["depended_by"].remove(module_name)
                if self.digraph.has_edge(module_name, dep):
                    self.digraph.remove_edge(module_name, dep)
        
        # 添加新依赖关系
        self.graph[module_name]["depends_on"] = new_dependencies
        for dep in new_dependencies:
            if dep in self.graph:
                depended_by = self.graph[dep].get("depended_by", [])
                if module_name not in depended_by:
                    depended_by.append(module_name)
                    self.graph[dep]["depended_by"] = depended_by
            else:
                # 如果依赖模块不存在，创建它
                inferred_layer = self.infer_layer(dep)
                self.graph[dep] = {
                    "depends_on": [],
                    "depended_by": [module_name],
                    "layer": inferred_layer
                }
            self.digraph.add_node(dep)
            self.digraph.add_edge(module_name, dep)
        
        self.save()
        
        # 检查是否引入了循环依赖
        circular_check = self.check_circular_dependencies(module_name)
        layer_check = self.check_layer_violations(module_name)
        
        return {
            "circular_dependency": circular_check,
            "layer_violations": layer_check,
            "impact_analysis": impact_analysis
        }
    
    def check_circular_dependencies(self, start_module=None):
        """检查是否存在循环依赖，如果指定了起始模块，则只检查与该模块相关的循环"""
        try:
            if start_module:
                # 只检查与指定模块相关的循环
                descendants = set(nx.descendants(self.digraph, start_module))
                if descendants:
                    subgraph = self.digraph.subgraph(descendants.union({start_module}))
                    cycles = list(nx.simple_cycles(subgraph))
                else:
                    cycles = []
            else:
                # 检查所有循环
                cycles = list(nx.simple_cycles(self.digraph))
            
            return {
                "has_cycles": len(cycles) > 0,
                "cycles": cycles
            }
        except Exception as e:
            print_log(f"检查循环依赖时出错: {e}")
            return {"has_cycles": False, "cycles": []}
    
    def check_layer_violations(self, module_name=None):
        """检查是否存在层次规则违反，可选择只检查特定模块"""
        violations = []
        
        modules_to_check = [module_name] if module_name else self.graph.keys()
        
        for mod in modules_to_check:
            if mod not in self.graph:
                continue
                
            module_layer = self.graph[mod].get("layer")
            if not module_layer:
                module_layer = self.infer_layer(mod)
                self.graph[mod]["layer"] = module_layer
            
            allowed_layers = self.layer_rules.get(module_layer, [])
            
            for dep in self.graph[mod].get("depends_on", []):
                if dep not in self.graph:
                    continue
                    
                dep_layer = self.graph[dep].get("layer")
                if not dep_layer:
                    dep_layer = self.infer_layer(dep)
                    self.graph[dep]["layer"] = dep_layer
                
                if dep_layer not in allowed_layers:
                    violations.append({
                        "module": mod,
                        "module_layer": module_layer,
                        "dependency": dep,
                        "dependency_layer": dep_layer,
                        "allowed_layers": allowed_layers
                    })
        
        return {
            "has_violations": len(violations) > 0,
            "violations": violations
        }
    
    def find_dependency_path(self, source: str, target: str) -> List[List[str]]:
        """查找从源模块到目标模块的所有依赖路径"""
        if source not in self.graph or target not in self.graph:
            return []
        
        try:
            # 查找所有简单路径
            all_paths = list(nx.all_simple_paths(self.digraph, source, target))
            return all_paths
        except Exception as e:
            print_log(f"查找依赖路径时出错: {e}")
            return []
    
    def predict_dependency_impact(self, module_name: str, new_dependencies: List[str]) -> Dict:
        """预测添加新依赖的影响"""
        if module_name not in self.graph:
            return {"error": "模块不存在"}
        
        # 当前依赖
        current_deps = set(self.graph[module_name].get("depends_on", []))
        new_deps_set = set(new_dependencies)
        
        # 计算添加和移除的依赖
        added_deps = new_deps_set - current_deps
        removed_deps = current_deps - new_deps_set
        
        # 预测循环依赖
        temp_digraph = self.digraph.copy()
        
        # 移除旧依赖
        for dep in removed_deps:
            if temp_digraph.has_edge(module_name, dep):
                temp_digraph.remove_edge(module_name, dep)
        
        # 添加新依赖
        for dep in added_deps:
            if dep not in temp_digraph:
                temp_digraph.add_node(dep)
            temp_digraph.add_edge(module_name, dep)
        
        # 检查循环
        potential_cycles = []
        try:
            cycles = list(nx.simple_cycles(temp_digraph))
            for cycle in cycles:
                if module_name in cycle:
                    potential_cycles.append(cycle)
        except Exception as e:
            print_log(f"预测循环依赖时出错: {e}")
        
        # 层次违规预测
        layer_violations = []
        module_layer = self.graph[module_name].get("layer", self.infer_layer(module_name))
        allowed_layers = self.layer_rules.get(module_layer, [])
        
        for dep in added_deps:
            if dep in self.graph:
                dep_layer = self.graph[dep].get("layer", self.infer_layer(dep))
            else:
                dep_layer = self.infer_layer(dep)
            
            if dep_layer not in allowed_layers:
                layer_violations.append({
                    "dependency": dep,
                    "dependency_layer": dep_layer,
                    "allowed_layers": allowed_layers
                })
        
        return {
            "added_dependencies": list(added_deps),
            "removed_dependencies": list(removed_deps),
            "potential_cycles": potential_cycles,
            "layer_violations": layer_violations
        }
    
    def get_topological_order(self):
        """获取模块的拓扑排序（如果没有循环依赖）"""
        try:
            return list(nx.topological_sort(self.digraph))
        except nx.NetworkXUnfeasible:
            # 有循环依赖，无法进行拓扑排序
            return None
    
    def get_layer_structure(self):
        """获取按层次组织的模块结构"""
        layer_structure = {layer: [] for layer in self.ARCHITECTURE_LAYERS}
        
        # 将所有模块分配到各层
        for module_name, data in self.graph.items():
            layer = data.get("layer")
            if not layer:
                layer = self.infer_layer(module_name)
                self.graph[module_name]["layer"] = layer
            
            if layer in layer_structure:
                layer_structure[layer].append(module_name)
        
        return layer_structure
    
    def get_module_complexity(self, module_name: str) -> Dict:
        """分析模块的复杂性指标"""
        if module_name not in self.graph:
            return {"error": "模块不存在"}
        
        try:
            # 计算入度（被依赖数）和出度（依赖数）
            in_degree = self.digraph.in_degree(module_name)
            out_degree = self.digraph.out_degree(module_name)
            
            # 计算传递依赖
            descendants = list(nx.descendants(self.digraph, module_name))
            ancestors = list(nx.ancestors(self.digraph, module_name))
            
            # 计算重要性（被依赖的模块数）
            importance = len(ancestors)
            
            # 计算依赖复杂度（依赖的模块数）
            dependency_complexity = len(descendants)
            
            return {
                "direct_dependencies": out_degree,
                "direct_dependents": in_degree,
                "transitive_dependencies": dependency_complexity,
                "transitive_dependents": importance,
                "descendants": descendants,
                "ancestors": ancestors
            }
        except Exception as e:
            print_log(f"计算模块复杂性时出错: {e}")
            return {"error": str(e)}
    
    def visualize(self, output_path="data/output/dependency_graph.png", highlight_module=None, show_layers=True):
        """将依赖图可视化并保存为图片，可选择高亮特定模块及其依赖"""
        plt.figure(figsize=(14, 10))
        
        # 使用spring_layout确保节点不重叠
        pos = nx.spring_layout(self.digraph, k=0.15, iterations=50)
        
        # 准备节点颜色
        node_colors = []
        layer_colors = {
            "infrastructure": "lightblue",
            "data": "lightgreen", 
            "domain": "yellow",
            "service": "orange",
            "application": "pink",
            "presentation": "lightcoral",
            "testing": "lightgrey"
        }
        
        # 设置每个节点的颜色
        for node in self.digraph.nodes():
            if highlight_module:
                if node == highlight_module:
                    node_colors.append("red")  # 高亮节点
                elif self.digraph.has_edge(highlight_module, node):
                    node_colors.append("orange")  # 高亮节点的直接依赖
                elif self.digraph.has_edge(node, highlight_module):
                    node_colors.append("green")  # 依赖高亮节点的模块
                else:
                    node_colors.append("lightgrey")  # 其他节点
            elif show_layers:
                layer = self.graph[node].get("layer")
                if not layer:
                    layer = self.infer_layer(node)
                node_colors.append(layer_colors.get(layer, "lightgrey"))
            else:
                node_colors.append("skyblue")
        
        # 绘制节点
        nx.draw_networkx_nodes(
            self.digraph, pos, 
            node_color=node_colors, 
            node_size=1500, 
            alpha=0.8
        )
        
        # 绘制边
        edge_colors = []
        for u, v in self.digraph.edges():
            if highlight_module and (u == highlight_module or v == highlight_module):
                edge_colors.append("red")  # 高亮相关边
            else:
                edge_colors.append("black")
                
        nx.draw_networkx_edges(
            self.digraph, pos, 
            edge_color=edge_colors,
            width=1.5, 
            arrowsize=20,
            arrowstyle='->'
        )
        
        # 添加标签
        nx.draw_networkx_labels(self.digraph, pos, font_size=10)
        
        # 添加图例
        if show_layers:
            layer_patches = []
            import matplotlib.patches as mpatches
            for layer, color in layer_colors.items():
                patch = mpatches.Patch(color=color, label=layer)
                layer_patches.append(patch)
            plt.legend(handles=layer_patches, loc="upper right")
        
        plt.title("Module Dependency Graph")
        plt.axis("off")
        plt.tight_layout()
        
        # 保存图片
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print_log(f"依赖图已保存到 {output_path}", level="info")
        plt.close()
        
        return output_path
    
    def get_dependency_summary(self) -> Dict:
        """获取依赖图的摘要信息"""
        if not self.graph:
            return {"error": "依赖图为空"}
        
        # 基本统计
        module_count = len(self.graph)
        edge_count = self.digraph.number_of_edges()
        
        # 循环依赖
        cycles = self.check_circular_dependencies()
        
        # 层次违规
        layer_violations = self.check_layer_violations()
        
        # 层次分布
        layer_structure = self.get_layer_structure()
        layer_distribution = {layer: len(modules) for layer, modules in layer_structure.items()}
        
        # 复杂度分析
        complexity_metrics = {}
        for module in self.graph:
            in_degree = self.digraph.in_degree(module)
            out_degree = self.digraph.out_degree(module)
            complexity_metrics[module] = {
                "in_degree": in_degree,
                "out_degree": out_degree
            }
        
        # 找出核心模块（最多被依赖的）
        core_modules = sorted(
            [(m, self.digraph.in_degree(m)) for m in self.graph], 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # 找出问题模块（有循环依赖或层次违规的）
        problem_modules = set()
        
        if cycles["has_cycles"]:
            for cycle in cycles["cycles"]:
                problem_modules.update(cycle)
                
        if layer_violations["has_violations"]:
            for violation in layer_violations["violations"]:
                problem_modules.add(violation["module"])
                problem_modules.add(violation["dependency"])
        
        return {
            "module_count": module_count,
            "dependency_count": edge_count,
            "circular_dependencies": cycles,
            "layer_violations": layer_violations,
            "layer_distribution": layer_distribution,
            "core_modules": core_modules,
            "problem_modules": list(problem_modules),
            "complexity_metrics": complexity_metrics
        }
    
    def build_from_modules(self, modules_dir="data/output/modules"):
        """从模块定义目录构建依赖图"""
        modules_dir = Path(modules_dir)
        self.graph = {}
        
        if not modules_dir.exists():
            print_log(f"模块目录不存在: {modules_dir}", level="warning")
            return
            
        # 第一遍: 收集所有模块
        for module_dir in modules_dir.glob("*"):
            if module_dir.is_dir():
                summary_file = module_dir / "full_summary.json"
                if summary_file.exists():
                    try:
                        data = json.loads(summary_file.read_text())
                        module_name = data.get("module_name")
                        if module_name:
                            # 推断模块层次
                            layer = data.get("layer") or data.get("layer_type")
                            if not layer:
                                layer = self.infer_layer(module_name)
                                
                            self.graph[module_name] = {
                                "depends_on": data.get("depends_on", []),
                                "depended_by": [],
                                "target_path": data.get("target_path", ""),
                                "layer": layer
                            }
                    except Exception as e:
                        print_log(f"处理模块 {module_dir.name} 时出错: {e}", level="error")
        
        # 第二遍: 填充 depended_by 字段
        for name, data in self.graph.items():
            for dep in data["depends_on"]:
                if dep in self.graph:
                    if name not in self.graph[dep]["depended_by"]:
                        self.graph[dep]["depended_by"].append(name)
        
        # 更新NetworkX图
        self._ensure_nx_graph()
        self.save()
        
        # 检查并输出摘要
        summary = self.get_dependency_summary()
        print_log(f"从 {len(self.graph)} 个模块构建了依赖图", level="info")
        if summary.get("circular_dependencies", {}).get("has_cycles", False):
            print_log(f"⚠️ 检测到 {len(summary['circular_dependencies']['cycles'])} 个循环依赖", level="warning")
        if summary.get("layer_violations", {}).get("has_violations", False):
            print_log(f"⚠️ 检测到 {len(summary['layer_violations']['violations'])} 个层次违规", level="warning")
        
        return self.graph

# 使用示例
def initialize_dependency_graph():
    """初始化并返回依赖图管理器"""
    manager = DependencyManager()
    manager.build_from_modules()
    return manager 