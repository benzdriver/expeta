# Expeta 日志系统迁移指南

## 已完成的工作

1. **改进的日志系统**
   - 重构了 `common/logger.py` 以支持基于时间戳的日志组织
   - 将日志目录从 `data/logs` 移至项目根目录下的 `logs`
   - 添加了单例模式以确保日志记录器实例的一致性
   - 增加了时间戳记录，便于追踪事件顺序

2. **简化的 API**
   - 添加了 `print_log` 函数作为 `print` 的直接替代
   - 创建了默认的全局日志记录器实例 `default_logger`
   - 通过 `common` 包导出了常用功能，使导入更简单

3. **迁移工具**
   - 创建了自动迁移脚本 `scripts/migrate_prints_to_logger.py`
   - 支持干运行模式，可以预览更改而不实际修改文件
   - 针对不同类型的 print 语句（错误、警告、成功等）应用相应的日志级别

4. **示例和测试**
   - 创建了 `scripts/test_logger.py` 以验证日志系统的功能
   - 创建了 `scripts/update_prints_example.py` 作为迁移示例
   - 创建了详细的使用文档 `common/README.md`

## 迁移步骤

要将项目完全迁移到新的日志系统，请按照以下步骤操作：

1. **确保 Python 路径设置正确**
   ```bash
   export PYTHONPATH=$(pwd):$PYTHONPATH
   ```

2. **运行迁移脚本**
   
   先使用干运行模式查看将要更改的内容：
   ```bash
   python scripts/migrate_prints_to_logger.py --directory ./ --dry-run
   ```
   
   确认更改无误后，实际执行迁移：
   ```bash
   python scripts/migrate_prints_to_logger.py --directory ./
   ```
   
   也可以逐个模块进行迁移：
   ```bash
   python scripts/migrate_prints_to_logger.py --directory ./llm_services
   python scripts/migrate_prints_to_logger.py --directory ./knowledge
   python scripts/migrate_prints_to_logger.py --directory ./reasoning
   python scripts/migrate_prints_to_logger.py --directory ./document_processing
   python scripts/migrate_prints_to_logger.py --directory ./apps
   ```

3. **更新导入语句**
   
   在项目的主要入口点（如 `run_expeta.py`）添加：
   ```python
   from common import logger
   ```

4. **手动检查复杂的 print 语句**
   
   自动迁移可能无法处理所有复杂情况，特别是：
   - 多行 print 语句
   - 带有复杂格式化的 print 语句
   - 条件性 print 语句
   
   这些可能需要手动审查和调整。

5. **更新环境变量**
   
   为了确保 Python 路径设置正确，考虑在项目的激活脚本中添加：
   ```bash
   # 添加到 .venv/bin/activate 或等效脚本
   export PYTHONPATH=$(pwd):$PYTHONPATH
   ```

## 测试和验证

迁移后，运行测试日志脚本验证日志系统工作正常：
```bash
python scripts/test_logger.py
```

检查生成的日志文件，确保它们被正确创建在 `logs/[timestamp]/` 目录中。

## 可能遇到的问题

1. **模块导入错误**
   - 确保 `PYTHONPATH` 包含项目根目录
   - 检查 `common/__init__.py` 文件是否存在并正确

2. **日志级别不匹配**
   - 自动迁移可能无法正确推断所有日志的级别
   - 特别注意包含错误信息的 print 语句，它们应该使用 "error" 级别

3. **日志文件权限**
   - 确保应用有权限创建和写入 `logs` 目录
   - 在部署环境中可能需要调整权限或目录位置

## 后续工作

1. **添加更多日志格式选项**
   - 考虑添加 JSON 格式的日志输出，便于机器处理
   - 可以添加不同的格式化器支持不同的日志展示方式

2. **日志轮换**
   - 实现日志文件自动轮换，防止单个文件过大
   - 可以基于文件大小或时间间隔进行轮换

3. **日志分析工具**
   - 开发简单的日志分析和可视化工具
   - 自动汇总错误和警告信息 