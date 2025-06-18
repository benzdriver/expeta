# Expeta架构推理系统迁移计划

## 目录

1. [迁移策略概述](#1-迁移策略概述)
2. [迁移准备工作](#2-迁移准备工作)
3. [分阶段迁移计划](#3-分阶段迁移计划)
4. [兼容性管理](#4-兼容性管理)
5. [测试与验证](#5-测试与验证)
6. [回滚策略](#6-回滚策略)
7. [迁移后清理](#7-迁移后清理)

## 1. 迁移策略概述

为确保平稳过渡到新架构，采用渐进式迁移策略，保证在迁移过程中系统功能持续可用。迁移将从底层服务开始，逐步向上层应用迁移，并使用适配器模式确保新旧代码的兼容性。

### 核心原则
- **功能持续性**: 迁移过程中保持系统可用
- **增量迁移**: 小批量功能迁移，及时验证
- **双轨运行**: 关键功能同时支持新旧实现，直到新实现稳定
- **向后兼容**: 使用适配器确保API兼容性
- **彻底测试**: 每个迁移步骤都有对应的自动化测试

## 2. 迁移准备工作

### 2.1 依赖分析

| 现有模块 | 新架构位置 | 依赖关系 | 复杂度 |
|---------|-----------|----------|--------|
| llm_v2/executor.py | llm_services/executor.py | 低 | 低 |
| llm_v2/client_factory.py | llm_services/client_factory.py | 低 | 低 |
| memory/vector_store.py | knowledge/vector_store.py | 中 | 中 |
| memory/entity_storage.py | knowledge/entity_storage.py | 中 | 中 |
| memory/smart_arch.py | reasoning/local_reasoning/* | 高 | 高 |
| clarifier_v2/entity_discovery.py | document_processing/entity_discovery.py | 中 | 中 |
| clarifier_v2/structured_summarizer.py | document_processing/initial_summarizer.py | 高 | 高 |
| clarifier_v2/smart_pipeline.py | reasoning/pipeline.py | 高 | 高 |

### 2.2 初始设置

1. 创建新的目录结构
   ```bash
   mkdir -p reasoning/{global_reasoning,local_reasoning}
   mkdir -p knowledge
   mkdir -p document_processing
   mkdir -p llm_services
   mkdir -p common
   mkdir -p apps
   mkdir -p tests/{unit,integration,fixtures}
   ```

2. 创建初始`__init__.py`文件
   ```bash
   find . -type d -not -path "*/\.*" -not -path "*/data*" -exec touch {}/__init__.py \;
   ```

3. 设置测试环境
   ```
   # 添加测试依赖到requirements.txt
   pytest
   pytest-asyncio
   pytest-mock
   ```

## 3. 分阶段迁移计划

### 3.1 第一阶段：基础服务迁移 (1周)

1. **LLM服务迁移**
   - 将`llm_v2/executor.py` → `llm_services/executor.py`
   - 将`llm_v2/client_factory.py` → `llm_services/client_factory.py`
   - 将`llm_v2/chat.py` → `llm_services/chat.py`
   - 将`llm_v2/rag.py` → `llm_services/rag.py`
   - 更新导入路径，保持API兼容

   ```python
   # 创建兼容层在旧位置
   # llm_v2/executor.py
   from llm_services.executor import run_prompt
   # 导出与原接口相同的函数，保持向后兼容
   ```

2. **通用工具迁移**
   - 创建`common/utils.py`，汇总常用工具函数
   - 创建`common/logger.py`，统一日志处理
   - 创建`common/config.py`，集中配置管理

3. **知识存储迁移**
   - 将`memory/vector_store.py` → `knowledge/vector_store.py`
   - 将`memory/entity_storage.py` → `knowledge/entity_storage.py`
   - 实现`knowledge/reasoning_memory.py`的基础结构
   - 添加兼容层保证现有代码可继续使用

   ```python
   # 创建兼容层
   # memory/vector_store.py
   from knowledge.vector_store import get_vector_store, create_vector_store
   # 导出兼容函数
   ```

### 3.2 第二阶段：文档处理迁移 (1-2周)

1. **实体发现迁移**
   - 将`clarifier_v2/entity_discovery.py` → `document_processing/entity_discovery.py`
   - 重构接口使其更清晰，但保持核心功能不变

2. **内容分析实现**
   - 创建`document_processing/content_analyzer.py`
   - 从`clarifier_v2`相关代码提取并重构文档分析功能

3. **初始摘要生成迁移**
   - 将`clarifier_v2/structured_summarizer.py`核心逻辑 → `document_processing/initial_summarizer.py`
   - 分离出纯摘要生成逻辑，移除与推理相关的部分

4. **兼容适配器**
   - 在原始位置创建兼容层
   - 确保现有流程仍然可以调用，保持功能一致

### 3.3 第三阶段：推理组件迁移 (2-3周)

1. **局部推理实现**
   - 分析`memory/smart_arch.py`的核心功能
   - 将功能分解到`reasoning/local_reasoning/`下的多个模块：
     - `context_builder.py`：上下文构建
     - `question_generators.py`：问题生成
     - `answer_generators.py`：回答生成
     - `summary_updaters.py`：摘要更新
   - 实现`local_chain.py`集成这些组件

2. **全局推理实现**
   - 创建`reasoning/global_reasoning/system_analyzer.py`
   - 创建`reasoning/global_reasoning/constraints_generator.py`
   - 实现`global_chain.py`集成全局推理流程

3. **推理流水线**
   - 将`clarifier_v2/smart_pipeline.py`核心逻辑迁移到`reasoning/pipeline.py`
   - 扩展为同时支持全局和局部推理

### 3.4 第四阶段：应用脚本迁移 (1周)

1. **应用脚本实现**
   - 创建`apps/run_global_reasoning.py`
   - 创建`apps/run_local_reasoning.py`
   - 创建`apps/run_full_pipeline.py`

2. **迁移主执行脚本**
   - 将`run_clarifier_pipeline.py`的功能迁移到`apps/run_full_pipeline.py`
   - 将`run_smart_arch_filler.py`的功能迁移到`apps/run_local_reasoning.py`

3. **创建新入口点**
   - 在项目根目录保留简单入口点脚本，调用新实现

## 4. 兼容性管理

### 4.1 模块级兼容层

为每个迁移的关键模块创建兼容层，确保现有代码可以继续使用：

```python
# 示例：memory/vector_store.py 兼容层
"""
兼容层 - 请使用新的知识模块
这个模块将在1.0版本后移除
"""
import warnings
from knowledge.vector_store import (
    get_vector_store as _get_vector_store,
    create_vector_store as _create_vector_store
)

def get_vector_store(*args, **kwargs):
    warnings.warn(
        "调用已弃用的模块。请使用 knowledge.vector_store",
        DeprecationWarning, stacklevel=2
    )
    return _get_vector_store(*args, **kwargs)
    
def create_vector_store(*args, **kwargs):
    warnings.warn(
        "调用已弃用的模块。请使用 knowledge.vector_store",
        DeprecationWarning, stacklevel=2
    )
    return _create_vector_store(*args, **kwargs)
```

### 4.2 API兼容性策略

1. **稳定API标记**
   - 在新代码中标记稳定的API
   ```python
   @stable_api
   def function_name():
       """这是一个稳定的API，不会在短期内改变"""
       pass
   ```
   
2. **版本控制**
   - 为关键API添加版本信息
   ```python
   def function_name_v2():
       """新版本的函数实现"""
       pass
   ```

## 5. 测试与验证

### 5.1 测试策略

1. **单元测试**
   - 为每个迁移的模块创建单元测试
   - 确保核心功能与原实现一致

2. **集成测试**
   - 测试模块间集成是否正常工作
   - 测试端到端流程

3. **功能对比测试**
   - 使用相同输入比较新旧实现的输出
   - 确保结果一致或新实现效果更好

### 5.2 验证流程

每个模块迁移后的验证流程：

1. 运行单元测试确保功能正确
2. 运行集成测试确保与其他模块交互正常
3. 在隔离环境中运行端到端测试
4. 对比新旧实现结果
5. 代码审查确保质量
6. 文档更新反映变更

## 6. 回滚策略

### 6.1 模块级回滚

每个模块迁移时：
1. 保留原始代码
2. 使用兼容层连接新旧实现
3. 如出现问题，在兼容层切换回原实现

```python
# 带回滚功能的兼容层示例
USE_NEW_IMPLEMENTATION = True  # 控制开关

def get_vector_store(*args, **kwargs):
    if USE_NEW_IMPLEMENTATION:
        try:
            from knowledge.vector_store import get_vector_store as new_impl
            return new_impl(*args, **kwargs)
        except Exception as e:
            logger.error(f"新实现失败，回滚到旧版本: {e}")
            # 回退到旧实现
    
    # 原始实现
    # 旧代码...
```

### 6.2 全局回滚

如果多个模块出现问题，需要完全回滚：
1. 恢复入口点脚本使用旧实现
2. 关闭所有兼容层中的新实现开关
3. 记录失败原因，修复后再次尝试迁移

## 7. 迁移后清理

### 7.1 代码清理

1. **移除兼容层**
   - 全部迁移完成并稳定运行后，移除临时兼容层
   - 更新所有导入使用新路径

2. **移除未使用代码**
   - 清理重构过程中产生的冗余或废弃代码
   - 运行静态分析工具识别未使用的代码

### 7.2 文档更新

1. **API文档**
   - 更新API文档反映新结构
   - 标注已弃用的API

2. **架构文档**
   - 更新设计文档反映新架构
   - 提供新旧架构映射关系图

3. **使用示例**
   - 提供新架构下的代码示例
   - 更新教程和指南 