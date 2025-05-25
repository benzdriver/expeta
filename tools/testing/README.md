# 测试工具

此目录包含辅助测试和验证系统的工具。

## 工具说明

### check_imports.py
检查项目中的导入语句，验证导入的模块是否存在，帮助排查导入错误。

用法:
```bash
python tools/testing/check_imports.py
```

### check_fixtures.py
检查测试固件的完整性，确保所有测试所需的固件都已正确设置。

用法:
```bash
python tools/testing/check_fixtures.py
```

### test_env.py
测试环境变量配置，验证系统所需的环境变量是否已正确设置。

用法:
```bash
python tools/testing/test_env.py
``` 