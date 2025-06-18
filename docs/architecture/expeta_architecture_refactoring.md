# Expeta 架构推理系统重构方案

## 目录

1. [项目概述](#1-项目概述)
2. [当前架构分析](#2-当前架构分析)
3. [重构目标](#3-重构目标)
4. [推理架构设计](#4-推理架构设计)
5. [LangChain实现方案](#5-langchain实现方案)
6. [项目结构重构](#6-项目结构重构)
7. [实现步骤](#7-实现步骤)
8. [关键优势](#8-关键优势)
9. [总结](#9-总结)

## 1. 项目概述

基于对现有代码分析，Expeta项目已经使用LangChain作为基础架构，实现了一系列智能架构分析功能。本文档提出了将多轮链式推理集成到项目中的重构方案，优化架构设计过程。

## 2. 当前架构分析

### 2.1 关键组件

- **llm_v2**: 已基于LangChain实现的LLM调用封装，包含`executor.py`提供的统一执行接口
- **memory**: 向量存储和实体管理，其中`smart_arch.py`实现了多轮架构推理
- **clarifier_v2**: 实体发现与结构化摘要生成，包含初步的架构分析功能

### 2.2 当前项目结构

```
expeta/
├── run_clarifier_pipeline.py       # 主流程脚本
├── run_smart_arch_filler.py        # 架构填充脚本
├── memory/                         # 记忆管理模块
│   ├── smart_arch.py               # 智能架构填充
│   ├── vector_store.py             # 向量存储
│   ├── entity_storage.py           # 实体存储
│   ├── retrieval.py                # 信息检索
│   └── ...
├── clarifier_v2/                   # 架构分析模块
│   ├── smart_pipeline.py           # 智能流水线
│   ├── structured_summarizer.py    # 结构化摘要
│   ├── entity_discovery.py         # 实体发现
│   ├── rag_retriever.py            # RAG检索
│   └── ... 
├── llm_v2/                         # LLM服务模块
│   ├── executor.py                 # 统一执行接口
│   ├── client_factory.py           # 客户端工厂
│   └── ...
└── ...
```

### 2.3 现有问题

1. **架构推理分散**: 架构分析逻辑分布在不同模块，难以形成连贯的推理链
2. **上下文管理不足**: 每轮推理使用相同上下文，未根据推理目标动态调整
3. **全局/局部决策分离**: 缺乏区分全局架构决策和局部模块设计的机制
4. **知识累积有限**: 未充分利用历史决策和推理过程进行知识积累

## 3. 重构目标

1. 实现基于LangChain的全局/局部分层推理架构
2. 为不同推理目标动态构建上下文
3. 建立架构决策知识库，支持跨模块知识共享
4. 优化项目结构，使流程更清晰、更模块化

## 4. 推理架构设计

### 4.1 多轮链式推理流程

#### 全局架构推理

全局推理关注整体系统层面的架构决策，为所有模块提供一致的指导和约束。

1. **系统类型识别**: 
   - 分析整体系统类型和领域特点
   - 识别主要用户群体和核心用例
   - 确定系统规模和复杂度

2. **技术栈与架构风格确定**: 
   - 确定前后端技术选型
   - 选择合适的架构风格(微服务/单体/前后端分离等)
   - 定义系统层次结构

3. **全局约束生成**: 
   - 制定命名和编码规范
   - 定义接口标准和通信协议
   - 确立安全和性能要求
   - 设定错误处理和日志策略

#### 局部模块推理

局部推理专注于单个模块或组件的设计，但需遵循全局约束。

1. **上下文理解与基础架构识别**
   - 分析模块在系统中的定位和职责
   - 明确模块边界和核心功能
   - 识别用户交互场景
   - 确定模块的主要数据实体

2. **架构模式与最佳实践应用**
   - 应用合适的架构模式和设计模式
   - 设计组件结构和交互方式
   - 规划数据流和状态管理
   - 确定API和接口设计

3. **一致性检查与冲突解决**
   - 检查与全局约束的一致性
   - 验证与相关模块的接口兼容性
   - 识别职责重叠和循环依赖
   - 解决架构冲突和风险点

4. **深度架构精细化**
   - 细化接口规范和参数定义
   - 完善错误处理和异常流程
   - 增强非功能性需求支持
   - 规划扩展点和演进路径

### 4.2 动态上下文构建

每轮推理使用特定上下文:

| 推理轮次 | 核心上下文 | 历史知识检索 | 全局上下文 |
|---------|-----------|------------|-----------|
| 轮次1 | 原始文档、需求描述 | 类似模块的定位决策 | 系统类型、架构风格 |
| 轮次2 | 架构模式库、设计模式参考 | 类似组件的设计决策 | 技术栈、接口标准 |
| 轮次3 | 相关模块信息、依赖描述 | 依赖模块的接口设计 | 命名约定、代码规范 |
| 轮次4 | 技术细节文档、性能考量 | 类似功能的实现细节 | 非功能需求标准 |

### 4.3 记忆与知识积累机制

1. **当前推理链记忆**: 
   - 当前实体多轮推理的问答记录
   - 每轮推理的决策和理由
   - 摘要更新的历史

2. **相关历史决策**: 
   - 从向量库检索的相关历史决策
   - 类似模块的架构设计
   - 之前解决的架构冲突

3. **全局架构约束**: 
   - 从架构章程中提取的规范和标准
   - 技术栈和平台限制
   - 系统级设计决策

## 5. LangChain实现方案

### 5.1 核心组件

```python
# 全局推理链
global_chain = (
    # 输入处理
    RunnablePassthrough.assign(
        documents=lambda x: preprocess_documents(x["documents"])
    )
    # 系统类型分析
    | RunnablePassthrough.assign(
        system_type=lambda x: analyze_system_type_chain.invoke(x)
    )
    # 架构风格确定
    | RunnablePassthrough.assign(
        architecture_style=lambda x: determine_arch_style_chain.invoke(x)
    )
    # 全局约束生成
    | RunnablePassthrough.assign(
        global_constraints=lambda x: generate_constraints_chain.invoke(x)
    )
    # 存储全局决策
    | store_global_decisions
)

# 局部推理链
local_chain = (
    # 初始处理
    RunnablePassthrough.assign(
        initial_summary=lambda x: generate_initial_summary(x["entity"], x["documents"])
    )
    # 构建多轮推理
    | create_reasoning_rounds_chain(max_rounds=4)
)

# 动态上下文构建
def build_context_for_round(entity_name, round_num, round_goal, current_summary, previous_qa):
    # 基础上下文
    base_context = retrieve_base_context(entity_name)
    
    # 全局约束
    global_constraints = retrieve_global_constraints()
    
    # 历史决策
    related_history = retrieve_related_decisions(entity_name, round_goal)
    
    # 目标特定上下文
    goal_specific_context = get_goal_specific_context(round_goal, entity_name)
    
    # 合并上下文
    return format_context(
        base_context, 
        global_constraints, 
        previous_qa, 
        related_history, 
        goal_specific_context,
        current_summary,
        round_num,
        round_goal
    )
```

### 5.2 轮次推理实现

```python
async def run_reasoning_round(module_name, round_num, round_goal, current_summary, all_qa_history):
    # 构建当前轮次上下文
    context = build_context_for_round(
        module_name, 
        round_num, 
        round_goal, 
        current_summary, 
        all_qa_history
    )
    
    # 问题生成链
    question_chain = create_question_chain(round_goal)
    questions = await question_chain.ainvoke({"context": context, "round_num": round_num})
    
    # 问答处理
    round_qa = []
    for question in questions:
        answer_chain = create_answer_chain(round_goal)
        answer = await answer_chain.ainvoke({
            "question": question,
            "context": context
        })
        round_qa.append({"question": question, "answer": answer})
    
    # 更新摘要
    update_chain = create_update_chain(round_goal)
    updated_summary = await update_chain.ainvoke({
        "current_summary": current_summary,
        "qa_history": round_qa,
        "context": context
    })
    
    # 存储推理结果
    store_reasoning_results(
        module_name=module_name,
        round_goal=round_goal,
        qa_history=round_qa,
        updated_summary=updated_summary
    )
    
    return updated_summary, round_qa
```

### 5.3 特定目标的问题生成器

这里是为不同推理目标设计的问题生成器示例:

```python
# 第一轮: 上下文理解与基础架构识别
def create_context_understanding_questions(context, entity_name, round_num):
    prompt = PromptTemplate.from_template(
        """基于以下模块的信息，生成{num_questions}个深入的问题，
        以帮助识别基础架构和核心组件。
        
        模块: {entity_name}
        
        上下文信息:
        {context}
        
        请专注于:
        1. 识别文档中提到的核心功能和责任
        2. 明确系统的基本结构和边界
        3. 理解基础技术栈和架构风格
        4. 探索可能的用户角色和主要用例
        
        生成能引导深入思考以上方面的问题。每个问题应当针对性强，
        能帮助从上下文中提取或推断出关键架构信息。
        """
    )
    
    return prompt | llm | StrOutputParser() | parse_questions

# 第二轮: 架构模式与最佳实践应用
def create_architecture_pattern_questions(context, entity_name, round_num):
    prompt = PromptTemplate.from_template(
        """基于已有信息，生成{num_questions}个关于架构模式和最佳实践应用的深入问题。
        
        模块: {entity_name}
        
        上下文信息:
        {context}
        
        请专注于:
        1. 合适的架构模式和设计方案
        2. 前端组件结构和交互设计
        3. 后端服务分层和职责划分
        4. API设计和数据流动方式
        
        生成能引导思考如何应用合适架构模式的问题，帮助填充具体的组件设计和服务定义。
        """
    )
    
    return prompt | llm | StrOutputParser() | parse_questions
```

## 6. 项目结构重构

根据当前项目结构和重构需求，建议的新项目结构如下:

```
expeta/
├── reasoning/
│   ├── global_reasoning/
│   │   ├── __init__.py
│   │   ├── system_analyzer.py       # 系统类型分析
│   │   ├── constraints_generator.py # 约束生成
│   │   └── global_chain.py          # 全局推理链
│   ├── local_reasoning/
│   │   ├── __init__.py
│   │   ├── context_builder.py       # 上下文构建
│   │   ├── question_generators.py   # 问题生成
│   │   ├── answer_generators.py     # 答案生成
│   │   ├── summary_updaters.py      # 摘要更新
│   │   └── local_chain.py           # 局部推理链
│   ├── __init__.py
│   └── pipeline.py                  # 完整推理流水线
│
├── knowledge/
│   ├── __init__.py
│   ├── vector_store.py              # 向量存储(从memory重构)
│   ├── reasoning_memory.py          # 推理记忆管理
│   ├── entity_storage.py            # 实体存储管理
│   └── context_retrieval.py         # 上下文检索
│
├── document_processing/             # 从clarifier_v2重构
│   ├── __init__.py
│   ├── entity_discovery.py          # 实体发现
│   ├── content_analyzer.py          # 内容分析
│   └── initial_summarizer.py        # 初始摘要生成
│
├── llm_services/                    # 保留现有llm_v2结构
│   ├── __init__.py
│   ├── executor.py                  # 统一执行接口 
│   ├── client_factory.py            # 客户端工厂
│   ├── chat.py                      # 聊天功能
│   └── rag.py                       # RAG功能
│
├── common/
│   ├── __init__.py
│   ├── utils.py                     # 通用工具
│   ├── logger.py                    # 日志工具
│   └── config.py                    # 全局配置
│
├── apps/
│   ├── run_global_reasoning.py      # 全局推理脚本
│   ├── run_local_reasoning.py       # 局部推理脚本
│   └── run_full_pipeline.py         # 完整流水线脚本
│
├── data/
│   ├── input/                       # 输入文档
│   ├── output/
│   │   ├── global_architecture/     # 全局架构决策
│   │   ├── entity_summaries/        # 实体摘要
│   │   └── final_architecture/      # 最终架构设计
│   ├── vector_store/                # 向量存储数据
│   └── logs/                        # 日志文件
│
├── tests/
│   ├── unit/                        # 单元测试
│   ├── integration/                 # 集成测试
│   └── fixtures/                    # 测试固件
│
├── .gitignore
├── requirements.txt
├── pyproject.toml                   # 项目元数据
├── setup.py                         # 安装脚本
└── README.md
```

### 6.1 主要模块功能说明

1. **reasoning/**: 架构推理核心模块
   - **global_reasoning/**: 全局系统架构推理
   - **local_reasoning/**: 局部模块架构推理
   - **pipeline.py**: 整合全局和局部推理的完整流水线

2. **knowledge/**: 知识管理与检索
   - **vector_store.py**: 向量存储接口封装
   - **reasoning_memory.py**: 推理过程记忆管理
   - **entity_storage.py**: 实体摘要存储
   - **context_retrieval.py**: 上下文智能检索

3. **document_processing/**: 文档处理
   - **entity_discovery.py**: 从文档中发现实体
   - **content_analyzer.py**: 文档内容分析
   - **initial_summarizer.py**: 生成初始结构化摘要

4. **llm_services/**: LLM服务封装
   - **executor.py**: 统一的LLM执行接口
   - **client_factory.py**: 模型客户端工厂
   - **chat.py**: 对话功能支持
   - **rag.py**: 检索增强生成功能

## 7. 实现步骤

### 7.1 第一阶段: 基础重构 (1-2周)

1. 重构项目结构，创建新目录结构
2. 将现有功能迁移到新结构，保持基本功能可用
3. 设计并实现知识存储方案
4. 开发上下文检索基础功能

### 7.2 第二阶段: 全局推理实现 (2-3周)

1. 实现系统类型分析链
2. 实现架构风格确定链
3. 实现全局约束生成链
4. 集成全局推理流程
5. 开发全局架构可视化工具

### 7.3 第三阶段: 局部推理增强 (3-4周)

1. 实现动态上下文构建器
2. 为每个推理目标开发专用问题生成器
3. 实现多轮推理管理机制
4. 开发推理记忆和决策存储机制
5. 优化摘要更新逻辑

### 7.4 第四阶段: 集成与测试 (2-3周)

1. 将全局和局部推理集成到统一流水线
2. 开发可视化与分析工具
3. 进行端到端测试和调优
4. 撰写文档和使用指南

## 8. 关键优势

1. **结构化思考**: 通过分层推理提供更系统的架构设计
2. **知识积累**: 构建架构决策库，允许跨模块知识共享
3. **上下文智能**: 为不同推理目标提供最相关上下文
4. **一致性保障**: 全局约束确保系统级一致性
5. **模块化设计**: 重构提高代码可维护性和可扩展性

## 9. 总结

本重构方案利用LangChain框架实现了先进的多轮链式推理架构，将显著提升Expeta的架构设计能力。通过分离全局和局部推理，动态构建上下文，以及建立知识积累机制，系统将能够生成更连贯、更深入的架构设计。

重构后的系统不仅能够产生更高质量的架构文档，还能够作为架构知识库持续积累和改进，为团队提供一致的架构指导。 