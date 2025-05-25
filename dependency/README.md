# 依赖管理模块

此模块是Expeta系统的核心部分，负责分析和管理系统组件之间的依赖关系。

## 功能组件

### dependency_inference.py
推断系统组件之间的依赖关系，分析代码结构和引用关系，构建依赖图。

用法:
```python
from dependency.dependency_inference import DependencyInference

inferencer = DependencyInference()
dependencies = inferencer.analyze_dependencies("path/to/entities")
```

### dependency_manager.py
管理系统依赖关系的核心功能，支持依赖图生成、冲突检测和优化建议。

用法:
```python
from dependency.dependency_manager import DependencyManager

manager = DependencyManager()
manager.build_dependency_graph()
conflicts = manager.detect_conflicts()
```

## 与其他模块的集成

此模块与推理模块紧密集成，为架构分析提供关键输入。依赖关系是架构决策的重要依据，影响系统的解耦和演化能力。 