# 日志管理脚本

此目录包含与日志系统相关的工具和迁移脚本。

## 脚本说明

### migrate_prints_to_logger.py
将代码中的print语句迁移为使用Logger类的脚本，帮助标准化日志输出。

用法:
```bash
python scripts/logging/migrate_prints_to_logger.py <文件路径>
```

### update_prints_example.py
打印语句迁移的示例脚本，展示如何将print转换为Logger调用。

用法:
```bash
python scripts/logging/update_prints_example.py
``` 