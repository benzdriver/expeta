"""
依赖管理模块。
负责系统组件之间的依赖关系分析和管理，支持依赖图生成、循环依赖检测和层次违规检查。
"""

from dependency.dependency_manager import DependencyManager
from dependency.dependency_inference import build_initial_dependency_graph

__all__ = ["DependencyManager", "build_initial_dependency_graph"] 