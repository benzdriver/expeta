# Clarifier系统测试指南

## 概述

本指南详细说明了如何运行Clarifier系统的完整测试套件，确保所有组件正常工作并达到>95%的代码覆盖率。

## 环境准备

### 1. 激活虚拟环境

```bash
cd /Users/ziyanzhou/Projects/expeta
source .venv/bin/activate
```

### 2. 安装测试依赖

```bash
python -m pip install pytest pytest-asyncio pytest-cov
```

### 3. 设置Python路径

```bash
export PYTHONPATH=/Users/ziyanzhou/Projects/expeta:$PYTHONPATH
```

## 快速开始

### 运行所有测试并生成覆盖率报告

```bash
python clarifier/tests/run_tests_with_coverage.py
```

### 检查测试覆盖状态

```bash
python clarifier/tests/check_coverage.py
```

## 测试文件结构

```
clarifier/tests/
├── conftest.py                              # Pytest配置和fixtures
├── test_blind_spot_detector.py              # 盲点检测器测试 (20+ tests)
├── test_version_manager.py                  # 版本管理器测试 (20+ tests)
├── test_impact_analyzer.py                  # 影响分析器测试 (16+ tests)
├── test_refactoring_engine.py               # 重构引擎测试 (15+ tests)
├── test_clarifier_integration.py            # 集成测试 (9+ tests)
├── test_clarifier_orchestrator_real_data.py # 真实数据测试 (12+ tests)
├── test_all_components.py                   # 完整组件测试 (5+ tests)
├── run_tests_with_coverage.py               # 测试运行脚本
└── check_coverage.py                        # 覆盖率检查脚本
```

## 分类测试运行

### 1. 单元测试

#### 测试盲点检测器
```bash
python -m pytest clarifier/tests/test_blind_spot_detector.py -v
```

主要测试内容：
- 所有12种盲点类型检测
- 模式匹配准确性
- AI分析集成
- 性能和边界情况

#### 测试版本管理器
```bash
python -m pytest clarifier/tests/test_version_manager.py -v
```

主要测试内容：
- 版本创建和管理
- 分支和合并操作
- 回滚功能
- 版本搜索和统计

#### 测试影响分析器
```bash
python -m pytest clarifier/tests/test_impact_analyzer.py -v
```

主要测试内容：
- 依赖图构建
- 变更影响分析
- 工作量估算
- 循环依赖检测

#### 测试重构引擎
```bash
python -m pytest clarifier/tests/test_refactoring_engine.py -v
```

主要测试内容：
- 四种重构策略（增量、一次性、并行、特性开关）
- 执行和验证
- 回滚机制
- 风险评估

### 2. 集成测试

#### 基础集成测试
```bash
python -m pytest clarifier/tests/test_clarifier_integration.py -v
```

#### 真实数据测试
```bash
python -m pytest clarifier/tests/test_clarifier_orchestrator_real_data.py -v
```

使用的真实PRD文件：
- `/data/input/requirement-md.md` - ThinkForward AI移民平台需求
- `/data/input/technical-architecture.md` - 技术架构文档

#### 完整系统测试
```bash
python -m pytest clarifier/tests/test_all_components.py -v
```

### 3. 性能测试

```bash
python -m pytest clarifier/tests/test_all_components.py::TestClarifierPerformance -v -m slow
```

## 单个测试运行

### 运行特定测试类
```bash
python -m pytest clarifier/tests/test_blind_spot_detector.py::TestBlindSpotDetector -v
```

### 运行特定测试方法
```bash
python -m pytest clarifier/tests/test_version_manager.py::TestVersionManager::test_create_branch -v
```

### 带详细输出运行
```bash
python -m pytest clarifier/tests/test_clarifier_integration.py -v -s
```

## 测试标记

使用pytest标记运行特定类型的测试：

```bash
# 只运行慢速测试
python -m pytest -m slow -v

# 跳过慢速测试
python -m pytest -m "not slow" -v

# 只运行集成测试
python -m pytest -m integration -v

# 只运行使用真实API的测试
python -m pytest -m real_api -v
```

## 覆盖率报告

### 生成命令行覆盖率报告
```bash
python -m coverage run -m pytest clarifier/tests
python -m coverage report --show-missing
```

### 生成HTML覆盖率报告
```bash
python -m coverage html
# 报告位置：clarifier/tests/htmlcov/index.html
```

### 查看特定文件的覆盖率
```bash
python -m coverage report --include="clarifier/core/blind_spot_detector.py"
```

## 调试失败的测试

### 1. 显示详细错误信息
```bash
python -m pytest clarifier/tests/test_name.py -v --tb=long
```

### 2. 在第一个失败处停止
```bash
python -m pytest clarifier/tests -x
```

### 3. 进入调试模式
```bash
python -m pytest clarifier/tests/test_name.py --pdb
```

### 4. 显示print输出
```bash
python -m pytest clarifier/tests/test_name.py -s
```

## 常见问题解决

### 1. 导入错误

如果遇到导入错误，确保：
```bash
# 在项目根目录
cd /Users/ziyanzhou/Projects/expeta
export PYTHONPATH=$PWD:$PYTHONPATH
```

### 2. Logger导入问题

确保所有文件使用正确的logger导入：
```python
from common.logger import Logger
logger = Logger.get_instance("clarifier")
```

### 3. 异步测试问题

确保异步测试使用正确的装饰器：
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

### 4. 真实PRD文件缺失

如果真实PRD文件不存在，测试会使用备用内容。确保以下文件存在：
- `/data/input/requirement-md.md`
- `/data/input/technical-architecture.md`

## 测试最佳实践

### 1. 测试隔离
每个测试应该独立运行，不依赖其他测试的状态。

### 2. 使用Fixtures
利用pytest fixtures管理测试数据：
```python
@pytest.fixture
def sample_prd():
    return "测试PRD内容"
```

### 3. 参数化测试
对于相似的测试场景使用参数化：
```python
@pytest.mark.parametrize("input,expected", [
    ("case1", "result1"),
    ("case2", "result2")
])
def test_parametrized(input, expected):
    assert process(input) == expected
```

### 4. 清理资源
使用fixture的teardown功能清理测试资源：
```python
@pytest.fixture
def temp_file():
    file = create_temp_file()
    yield file
    file.cleanup()
```

## 持续集成配置

### GitHub Actions示例

```yaml
name: Clarifier Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests with coverage
      run: |
        python clarifier/tests/run_tests_with_coverage.py
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v1
```

## 测试检查清单

在提交代码前，确保完成以下检查：

- [ ] 所有测试通过 (`pytest clarifier/tests`)
- [ ] 代码覆盖率 > 95% (`python clarifier/tests/check_coverage.py`)
- [ ] 无警告信息 (`pytest clarifier/tests -W error`)
- [ ] 真实数据测试通过
- [ ] 性能测试在合理时间内完成
- [ ] 新功能有对应的测试
- [ ] 测试文档已更新

## 添加新测试

当添加新功能时，请遵循以下步骤：

1. **创建测试文件**：在 `clarifier/tests/` 目录下创建 `test_<feature_name>.py`

2. **编写测试类**：
```python
class TestNewFeature:
    @pytest.fixture
    def setup_data(self):
        # 准备测试数据
        return test_data
    
    def test_basic_functionality(self, setup_data):
        # 测试基本功能
        assert feature_works(setup_data)
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        # 测试异步功能
        result = await async_feature()
        assert result is not None
```

3. **运行新测试**：
```bash
python -m pytest clarifier/tests/test_new_feature.py -v
```

4. **检查覆盖率**：
```bash
python -m coverage run -m pytest clarifier/tests/test_new_feature.py
python -m coverage report
```

## 性能基准

预期的测试运行时间：

- 单元测试：< 10秒
- 集成测试：< 20秒
- 真实数据测试：< 30秒
- 完整测试套件：< 60秒
- 大型PRD处理测试：< 30秒/PRD

## 总结

Clarifier测试套件提供了全面的测试覆盖，确保系统的可靠性和正确性。通过遵循本指南，你可以：

1. 快速运行完整测试套件
2. 针对特定组件进行测试
3. 生成和分析覆盖率报告
4. 调试失败的测试
5. 添加新的测试用例

记住：良好的测试是高质量软件的基础。保持测试覆盖率>95%，确保Clarifier系统的稳定性和可靠性。