from common import print_log
#!/usr/bin/env python
"""
检查测试fixture是否能正确加载
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir))
print_log(f"项目根目录: {root_dir}")

# 打印Python路径
print_log("\nPython路径:")
for p in sys.path:
    print_log(f"  - {p}")

# 尝试导入测试fixture
print_log("\n尝试导入测试fixture:")
try:
    from tests.fixtures.conftest import mock_llm, sample_input_files, test_data_dir
    print_log("  ✓ 成功导入conftest中的fixture")
except ImportError as e:
    print_log(f"  ✗ 导入conftest中的fixture失败: {e}")

try:
    from tests.fixtures.mock_models import MockLLM, PREDEFINED_RESPONSES
    print_log("  ✓ 成功导入mock_models模块")
except ImportError as e:
    print_log(f"  ✗ 导入mock_models模块失败: {e}")

# 尝试导入应用模块
print_log("\n尝试导入应用模块:")
try:
    from document_processing.entity_discovery import discover_entities
    print_log("  ✓ 成功导入document_processing.entity_discovery模块")
except ImportError as e:
    print_log(f"  ✗ 导入document_processing.entity_discovery模块失败: {e}")

try:
    from apps.run_global_reasoning import run_pipeline
    print_log("  ✓ 成功导入apps.run_global_reasoning模块")
except ImportError as e:
    print_log(f"  ✗ 导入apps.run_global_reasoning模块失败: {e}")

print_log("\n完成") 