from common import print_log
#!/usr/bin/env python
"""
简单的脚本，用于检查模块导入和Python路径
"""

import sys
import os
from pathlib import Path

# 打印Python路径
print_log("Python path:")
for p in sys.path:
    print_log(f"  - {p}")

# 添加项目根目录到路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
print_log(f"\nAdded project root: {root_dir}\n")

# 打印目录内容
print_log(f"Directory contents of {root_dir}:")
for item in sorted(os.listdir(root_dir)):
    print_log(f"  - {item}")

# 尝试导入模块
print_log("\nTrying to import modules:")
try:
    from document_processing.entity_discovery import discover_entities
    print_log("  ✓ document_processing.entity_discovery imported successfully")
except ImportError as e:
    print_log(f"  ✗ Failed to import document_processing.entity_discovery: {e}")

try:
    from llm_services.chat import chat_completion
    print_log("  ✓ llm_services.chat imported successfully")
except ImportError as e:
    print_log(f"  ✗ Failed to import llm_services.chat: {e}")

try:
    from knowledge.vector_store import get_vector_store
    print_log("  ✓ knowledge.vector_store imported successfully")
except ImportError as e:
    print_log(f"  ✗ Failed to import knowledge.vector_store: {e}")

try:
    from reasoning.global_reasoning.system_analyzer import analyze_system
    print_log("  ✓ reasoning.global_reasoning.system_analyzer imported successfully")
except ImportError as e:
    print_log(f"  ✗ Failed to import reasoning.global_reasoning.system_analyzer: {e}")

print_log("\nDone.") 