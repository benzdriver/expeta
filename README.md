# Expeta

Expeta是一个软件架构分析系统，使用LLM（大语言模型）对文档进行分析，生成架构决策和详细设计。

## 设置

1. 克隆仓库
2. 创建虚拟环境:
   ```
   python -m venv .venv
   source .venv/bin/activate  # 在Windows上: .venv\Scripts\activate
   ```
3. 安装依赖:
   ```
   pip install -r requirements.txt
   ```
4. 创建一个`.env`文件，添加OpenAI API密钥:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## 输入数据

将您的输入文档（Markdown文件）放在`data/input`目录中。

## 使用方法

Expeta提供了一个简单的命令行界面，可以运行不同类型的推理:

### 运行完整推理流水线

运行完整的架构推理，包括全局推理和局部推理:

```bash
python tools/system/run_expeta.py full -i data/input -o data/output/architecture_full
```

### 仅运行全局架构推理

只生成系统级别的架构决策和约束:

```bash
python tools/system/run_expeta.py global -i data/input -o data/output/architecture
```

### 为特定实体运行局部推理

为特定组件或模块生成详细设计:

```bash
python tools/system/run_expeta.py local -e "UserService" -i data/input -o data/output/entity
```

## 模块结构

Expeta采用模块化设计，主要包含以下组件:

- **document_processing/**: 文档处理模块
  - `entity_discovery.py`: 实体发现
  - `content_analyzer.py`: 内容分析
  - `initial_summarizer.py`: 初始摘要生成

- **reasoning/**: 推理模块
  - **global_reasoning/**: 全局架构推理
    - `system_analyzer.py`: 系统分析
    - `constraints_generator.py`: 约束生成
    - `global_chain.py`: 全局推理链
  - **local_reasoning/**: 局部模块推理
    - `context_builder.py`: 上下文构建
    - `question_generators.py`: 问题生成
    - `answer_generators.py`: 回答生成
    - `summary_updaters.py`: 摘要更新
    - `local_chain.py`: 局部推理链

- **knowledge/**: 知识管理模块
  - `vector_store.py`: 向量存储
  - `entity_storage.py`: 实体存储
  - `context_retrieval.py`: 上下文检索
  - `reasoning_memory.py`: 推理记忆

- **llm_services/**: LLM服务模块
  - `executor.py`: 执行接口
  - `client_factory.py`: 客户端工厂
  - `chat.py`: 对话服务
  - `rag.py`: 检索增强生成

- **apps/**: 应用脚本
  - `run_global_reasoning.py`: 全局推理应用
  - `run_local_reasoning.py`: 局部推理应用
  - `run_full_pipeline.py`: 完整流水线应用

## 输出结果

系统将生成:

### 全局架构输出
- 系统分析报告 (`system_analysis.json`)
- 架构风格建议 (`architecture_style.json`)
- 架构章程 (`architecture_charter.json` 和 `architecture_charter.md`)
- 模块指导原则 (在 `module_guidelines/` 目录)

### 实体架构输出
- 实体全面摘要 (`full_summary.json`)
- 详细架构文档 (`architecture.md`)
- 依赖关系图

### 辅助文件
- 架构图 (`architecture_diagram.md`)
- 索引页面 (`index.md`)

## 工作流程

1. **文档处理**: 分析文档内容，识别实体和关键信息
2. **全局推理**: 确定系统类型、架构风格和全局约束
3. **局部推理**: 为每个实体生成详细设计，包括组件、接口和依赖关系
4. **输出生成**: 创建结构化JSON和可读性强的Markdown文档

## 目录结构

请参阅 [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md) 了解完整的项目目录结构。

### 核心模块

- **apps/**: 应用层模块，包含各种运行应用的脚本
- **document_processing/**: 文档处理模块，负责解析和处理输入文档
- **knowledge/**: 知识管理模块，处理向量存储和实体管理
- **reasoning/**: 推理模块，包含全局推理和局部推理功能
- **llm_services/**: LLM服务模块，提供大语言模型接口

### 工具和脚本

- **tools/**: 系统工具，按功能分类
  - **system/**: 系统运行工具
  - **dependency_management/**: 依赖管理工具
  - **testing/**: 测试工具

- **scripts/**: 辅助脚本，按功能分类
  - **database/**: 数据库管理脚本
  - **testing/**: 测试脚本
  - **logging/**: 日志管理脚本