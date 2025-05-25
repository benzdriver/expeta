# Expeta 日志系统

## 概述

Expeta 日志系统提供了一个集中式的、基于时间戳的日志记录解决方案。它支持多种日志级别、日志分类和角色，确保所有组件的日志行为一致。

## 特点

- **集中式管理**：所有项目组件都使用相同的日志系统
- **时间戳组织**：日志按运行实例的时间戳进行组织，方便查找和管理
- **级别控制**：支持 debug、info、warning、error、critical 等多种日志级别
- **控制台和文件输出**：同时输出到控制台和日志文件
- **角色分类**：支持按不同角色（system、user、clarifier等）进行日志分类

## 使用方法

### 基本用法

最简单的用法是使用 `print_log` 函数，它是对 `print` 函数的替代：

```python
from common import print_log

print_log("这是一条日志消息")
```

### 指定日志级别

可以指定不同的日志级别：

```python
print_log("信息消息", level="info")
print_log("警告消息", level="warning")
print_log("错误消息", level="error")
print_log("调试消息", level="debug")
print_log("严重错误", level="critical")
```

### 指定角色

可以指定不同的角色，用于区分日志来源：

```python
print_log("系统消息", role="system")
print_log("用户消息", role="user")
print_log("澄清器消息", role="clarifier")
```

### 直接使用 Logger 实例

如需更多控制，可以直接使用 Logger 实例：

```python
from common import logger

logger.log("这是一条日志消息", level="info", role="system")
```

### 创建模块专用的 Logger

如果需要为特定模块创建专用的 Logger：

```python
from common.logger import Logger

# 创建或获取特定模块的 logger
my_logger = Logger.get_instance("my_module")

# 使用该 logger
my_logger.log("模块专用消息")
```

## 日志位置

日志文件存储在项目根目录的 `logs` 文件夹中。每次程序运行都会创建一个以时间戳命名的子文件夹，其中包含各个模块的日志文件。

## 迁移工具

项目提供了一个自动迁移工具，用于将现有的 `print` 语句转换为使用集中式日志系统：

```bash
python scripts/migrate_prints_to_logger.py --directory ./your_module
```

或使用 `--dry-run` 选项预览更改而不实际修改文件：

```bash
python scripts/migrate_prints_to_logger.py --directory ./your_module --dry-run
```

## 最佳实践

1. **使用恰当的日志级别**：根据消息的重要性选择适当的日志级别
2. **包含上下文信息**：在日志消息中包含足够的上下文信息，使其自包含且有意义
3. **避免敏感信息**：不要记录密码、密钥等敏感信息
4. **避免过度记录**：避免在高频调用的代码中过度记录（除非设置了调试级别）
5. **结构化信息**：对于复杂数据，考虑使用 JSON 格式进行记录 