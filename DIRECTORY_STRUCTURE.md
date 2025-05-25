# Expeta 项目目录结构

## 核心模块

- **apps/** - 应用层模块，包含各种运行应用的脚本
- **common/** - 通用功能模块，提供跨系统使用的工具和功能
- **document_processing/** - 文档处理模块，负责解析和处理输入文档
- **knowledge/** - 知识管理模块，处理向量存储和实体管理
- **llm_services/** - LLM服务模块，提供大语言模型接口和服务
- **reasoning/** - 推理模块，包含全局推理和局部推理功能
- **prompt_templates/** - 提示词模板，存储与LLM交互的提示模板
- **dependency/** - 依赖管理模块，处理系统组件之间的依赖关系分析和管理

## 工具和脚本

- **scripts/** - 辅助脚本集合，按功能分类
  - **database/** - 数据库管理脚本，用于Qdrant向量数据库的配置和管理
  - **testing/** - 测试脚本，用于测试系统各个组件
  - **logging/** - 日志管理脚本，用于系统日志记录和迁移
  - **utils/** - 通用工具脚本，提供各种辅助功能

- **tools/** - 系统工具集合，按功能分类
  - **testing/** - 测试工具，辅助系统测试和验证
  - **system/** - 系统级工具，包含主要运行脚本和管理工具

## 测试

- **tests/** - 测试套件，包含单元测试和集成测试

## 数据

- **data/** - 数据目录
  - **input/** - 输入数据
  - **output/** - 输出结果
  - **qdrant/** - Qdrant本地存储（如果使用）

## 文档

- **README.md** - 项目主要说明
- **README_ARCH_FILLER.md** - 架构填充器功能说明
- **README_LOGGING_MIGRATION.md** - 日志迁移说明
- **DIRECTORY_STRUCTURE.md** - 本文件，目录结构说明 