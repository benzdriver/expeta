# Expeta 测试套件

Expeta测试套件包含单元测试和集成测试，确保系统各个组件正常工作。

## 测试目录结构

- **unit/** - 单元测试目录，包含对单个模块和组件的测试
- **integration/** - 集成测试目录，测试多个组件共同工作的情况
- **fixtures/** - 测试固件目录，包含测试数据和辅助函数

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行单元测试

```bash
pytest tests/unit/
```

### 运行集成测试

```bash
pytest tests/integration/
```

### 运行特定模块的测试

我们提供了便捷脚本来运行特定模块的测试：

```bash
# 运行依赖管理模块的测试
./scripts/testing/run_tests.sh --dependency test-all

# 创建示例依赖图
./scripts/testing/run_tests.sh --dependency create-graph

# 测试依赖关系推断
./scripts/testing/run_tests.sh --dependency infer-dependencies

# 使用真实API测试依赖推断
./scripts/testing/run_tests.sh --dependency test-real-api
```

## 真实API测试

某些测试需要调用真实的AI API（如OpenAI），这些测试被标记为集成测试并且需要特定环境：

1. 需要设置API密钥环境变量（如OPENAI_API_KEY）
2. 需要网络连接以访问外部API
3. 可能会产生API调用费用

运行真实API测试：

```bash
# 使用标签运行所有真实API测试
pytest -m integration

# 只运行依赖管理的真实API测试
pytest tests/integration/test_dependency_real_api.py
```

## 运行测试前的准备

某些测试可能需要特定的设置才能运行：

1. 数据库测试可能需要先初始化Qdrant数据库
   ```bash
   ./scripts/testing/run_tests.sh --init-db
   ```

2. 确保环境变量正确设置
   ```bash
   source .env
   ```

## 添加新测试

1. 在适当的目录下创建新的测试文件
2. 文件名应以`test_`开头
3. 测试类名应以`Test`开头
4. 测试方法名应以`test_`开头
5. 使用pytest的fixture机制共享测试固件 