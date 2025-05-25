# 测试脚本

此目录包含用于测试系统各个组件的脚本。

## 脚本说明

### run_tests.sh
运行测试套件的主脚本，支持各种测试模式和组件。

用法:
```bash
# 运行所有测试
./scripts/testing/run_tests.sh

# 测试数据库连接
./scripts/testing/run_tests.sh --test-db

# 测试知识存储
./scripts/testing/run_tests.sh --knowledge list

# 测试特定组件
./scripts/testing/run_tests.sh --component <组件名称>
```

### test_components.py
测试系统各个组件功能的Python脚本，支持分段测试各模块。

用法:
```bash
python scripts/testing/test_components.py --help
```

### test_logger.py
测试日志系统功能的脚本，验证日志记录是否正常工作。

用法:
```bash
python scripts/testing/test_logger.py
``` 