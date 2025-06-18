# Clarifier测试快速参考

## 🚀 快速命令

### 一键运行所有测试
```bash
./clarifier/run_tests.sh all
```

### 检查测试覆盖率
```bash
./clarifier/run_tests.sh check
```

### 快速测试（跳过慢速）
```bash
./clarifier/run_tests.sh quick
```

## 📋 常用测试命令

### 基础命令
```bash
# 激活虚拟环境
source .venv/bin/activate

# 设置Python路径
export PYTHONPATH=/Users/ziyanzhou/Projects/expeta:$PYTHONPATH

# 运行所有测试
python -m pytest clarifier/tests -v

# 运行并显示print输出
python -m pytest clarifier/tests -v -s

# 在第一个失败处停止
python -m pytest clarifier/tests -x

# 运行特定测试文件
python -m pytest clarifier/tests/test_blind_spot_detector.py -v

# 运行特定测试方法
python -m pytest clarifier/tests/test_version_manager.py::TestVersionManager::test_create_branch -v
```

### 覆盖率命令
```bash
# 运行测试并生成覆盖率
python clarifier/tests/run_tests_with_coverage.py

# 手动生成覆盖率报告
python -m coverage run -m pytest clarifier/tests
python -m coverage report --show-missing
python -m coverage html

# 查看特定文件覆盖率
python -m coverage report --include="clarifier/core/*.py"
```

### 按类型运行测试
```bash
# 单元测试
./clarifier/run_tests.sh unit

# 集成测试  
./clarifier/run_tests.sh integration

# 真实数据测试
./clarifier/run_tests.sh real

# 特定组件测试
./clarifier/run_tests.sh blind      # 盲点检测器
./clarifier/run_tests.sh version    # 版本管理器
./clarifier/run_tests.sh impact     # 影响分析器
./clarifier/run_tests.sh refactor   # 重构引擎
```

### 调试命令
```bash
# 显示详细错误
python -m pytest clarifier/tests/test_name.py -v --tb=long

# 进入调试器
python -m pytest clarifier/tests/test_name.py --pdb

# 只运行失败的测试
python -m pytest clarifier/tests --lf

# 运行上次失败的测试
python -m pytest clarifier/tests --last-failed
```

## 🎯 测试标记

```bash
# 运行慢速测试
python -m pytest -m slow -v

# 跳过慢速测试
python -m pytest -m "not slow" -v

# 只运行集成测试
python -m pytest -m integration -v

# 组合标记
python -m pytest -m "integration and not slow" -v
```

## 📊 预期结果

### 成功输出示例
```
============================= test session starts ==============================
collected 127 items

clarifier/tests/test_blind_spot_detector.py .................... [ 20%]
clarifier/tests/test_version_manager.py .................... [ 40%]
clarifier/tests/test_impact_analyzer.py .................... [ 60%]
clarifier/tests/test_refactoring_engine.py .................... [ 80%]
clarifier/tests/test_clarifier_integration.py ......... [ 90%]
clarifier/tests/test_all_components.py ....... [100%]

============================== 127 passed in 45.32s ==============================

Total Coverage: 98%
```

### 覆盖率目标
- 总体覆盖率: > 95% ✅
- 核心模块覆盖率: > 95% ✅
- 集成测试通过: 100% ✅

## 🔧 故障排除

### 导入错误
```bash
export PYTHONPATH=$PWD:$PYTHONPATH
```

### 依赖缺失
```bash
python -m pip install pytest pytest-asyncio pytest-cov
```

### 清理缓存
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type d -name .pytest_cache -exec rm -rf {} +
```

## 📝 测试检查清单

运行测试前确认：
- [ ] 虚拟环境已激活
- [ ] PYTHONPATH已设置
- [ ] 依赖已安装
- [ ] PRD文件存在于 `/data/input/`

提交代码前确认：
- [ ] 所有测试通过
- [ ] 覆盖率 > 95%
- [ ] 无警告信息
- [ ] 真实数据测试通过

## 🚨 紧急命令

```bash
# 快速验证系统是否正常
python -m pytest clarifier/tests/test_blind_spot_detector.py::TestBlindSpotDetector::test_detect_edge_cases -v

# 运行最小测试集
python -m pytest clarifier/tests -k "not slow and not real_data" -v

# 生成测试报告
python clarifier/tests/run_tests_with_coverage.py > test_report.txt 2>&1
```