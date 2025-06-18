# Expeta 项目总结

## 项目概述

Expeta 是一个基于大语言模型（LLM）的智能软件架构分析系统。它能够自动分析软件需求文档，生成架构决策、设计模式建议和详细的模块设计方案。

## 核心功能

### 1. 文档分析和实体发现
- 自动识别文档中的软件实体（API端点、服务、仓储层、模型等）
- 支持大型文档的分块处理
- 智能分类和去重

### 2. 全局架构推理
- 系统类型分析（Web应用、微服务、桌面应用等）
- 架构风格确定（分层架构、微服务、事件驱动等）
- 全局约束和设计原则生成
- 模块指导原则制定

### 3. 局部模块推理
- 为每个实体生成详细设计
- 多轮推理优化设计质量
- 生成前端组件、后端服务、API接口等
- 测试计划和依赖关系分析

### 4. 依赖管理
- 实时依赖图构建和维护
- 循环依赖检测
- 架构层次违规检查
- 依赖影响分析和可视化

### 5. 知识管理
- 基于 Qdrant 向量数据库的文档和实体存储
- 支持云端和本地存储模式
- 上下文检索和推理记忆管理
- 嵌入向量生成和相似性搜索

## 技术架构

### 主要技术栈
- **Python 3.x** - 主要开发语言
- **OpenAI GPT-4** - 核心推理引擎
- **LangChain** - LLM 应用开发框架
- **Qdrant** - 向量数据库
- **NetworkX** - 依赖图分析
- **FastAPI** - API 服务框架
- **Matplotlib** - 数据可视化

### 项目结构

```
expeta/
├── apps/                      # 应用入口点
│   ├── run_full_pipeline.py   # 完整流水线执行
│   ├── run_global_reasoning.py # 全局推理执行
│   └── run_local_reasoning.py  # 局部推理执行
│
├── document_processing/       # 文档处理模块
│   ├── entity_discovery.py    # 实体发现和识别
│   ├── content_analyzer.py    # 内容分析
│   └── initial_summarizer.py  # 初始摘要生成
│
├── reasoning/                 # 推理引擎
│   ├── global_reasoning/      # 全局架构推理
│   └── local_reasoning/       # 局部模块推理
│
├── knowledge/                 # 知识管理
│   ├── vector_store.py        # 向量存储管理
│   ├── entity_storage.py      # 实体存储
│   └── context_retrieval.py   # 上下文检索
│
├── llm_services/              # LLM 服务
│   ├── executor.py            # LLM 执行器
│   └── client_factory.py      # 客户端工厂
│
├── dependency/                # 依赖管理
│   └── dependency_manager.py  # 依赖图管理
│
├── common/                    # 通用功能
│   ├── logger.py              # 日志管理
│   └── json_utils.py          # JSON 工具
│
└── data/                      # 数据目录
    ├── input/                 # 输入文档
    ├── output/                # 输出结果
    └── qdrant/                # 本地向量存储
```

## 工作流程

1. **输入阶段**
   - 用户将需求文档（Markdown格式）放入 `data/input` 目录
   - 系统自动加载并合并所有文档

2. **文档处理**
   - 分析文档内容，提取关键信息
   - 识别软件实体（模块、服务、API等）
   - 对大文档进行智能分块

3. **全局推理**
   - 分析系统类型和特征
   - 确定适合的架构风格
   - 生成全局约束和设计原则
   - 制定模块设计指导方针

4. **局部推理**
   - 为每个实体构建上下文
   - 执行多轮问答推理
   - 生成详细的模块设计
   - 分析依赖关系

5. **输出生成**
   - JSON格式的结构化数据
   - Markdown格式的可读文档
   - 依赖关系图和架构图
   - 测试计划和实施指南

## 特色功能

- **智能分块处理**：支持超大文档的自动分块和并行处理
- **多轮推理优化**：通过迭代改进设计质量
- **层次化架构检查**：自动检测和防止架构违规
- **可扩展的模板系统**：支持自定义提示词模板
- **灵活的存储方案**：支持云端和本地向量存储
- **实时依赖分析**：动态构建和更新依赖关系图

## 使用方法

### 完整流水线运行
```bash
python apps/run_full_pipeline.py
```

### 仅运行全局推理
```bash
python apps/run_global_reasoning.py
```

### 仅运行局部推理
```bash
python apps/run_local_reasoning.py
```

### 环境配置
1. 复制 `.env.example` 到 `.env`
2. 配置必要的环境变量（OpenAI API Key、Qdrant 连接等）
3. 安装依赖：`pip install -r requirements.txt`

## 输出示例

系统会在 `data/output` 目录生成：
- `system_analysis.json` - 系统分析结果
- `architectural_charter.json` - 架构章程
- `architectural_charter.md` - 架构章程（可读格式）
- `entities/` - 每个实体的详细设计文档
- `dependency_graph.png` - 依赖关系可视图

## 使用场景

- 软件架构设计自动化
- 需求文档到设计文档的转换
- 架构一致性检查
- 依赖关系分析和优化
- 技术决策辅助
- 团队协作和知识共享

## 项目状态

项目正在积极开发中，主要功能已经实现并可以使用。未来计划包括：
- 支持更多的架构模式
- 增强的可视化功能
- 更好的多语言支持
- 集成更多的 LLM 提供商
- Web UI 界面开发

## 贡献指南

欢迎贡献代码、文档或建议。请查看项目的贡献指南了解详情。

## 许可证

[待确定]