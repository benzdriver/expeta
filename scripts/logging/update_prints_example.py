"""
示例：如何将print语句迁移到集中式日志记录器
"""

# 导入日志记录器
from common import logger, print_log

# 示例1：使用简单的日志记录
print_log("这是一个日志消息")  # 替代 print_log("这是一个日志消息")

# 示例2：使用不同的日志级别
print_log("这是一个信息级别的消息", level="info")
print_log("这是一个警告级别的消息", level="warning")
print_log("这是一个错误级别的消息", level="error")
print_log("这是一个调试级别的消息", level="debug")

# 示例3：使用不同的角色
print_log("这是一个系统消息", role="system")
print_log("这是一个用户消息", role="user")
print_log("这是一个澄清器消息", role="clarifier")

# 示例4：直接使用logger实例
logger.log("这是直接使用logger实例的消息")

# 示例5：迁移带有格式化的print语句
entity_name = "User"
print_log(f"处理实体: {entity_name}")  # 替代 print_log(f"处理实体: {entity_name}")

# 示例6：迁移带有表情符号的print语句
print_log("✅ 操作成功完成")  # 替代 print_log(f"操作成功完成", level="info")

# 示例7：根据上下文设置日志级别
success = False
if success:
    print_log("✅ 操作成功", level="info")
else:
    print_log("❌ 操作失败", level="error")

"""
迁移指南：

1. 替换简单的print语句:
   - 原始代码: print_log("消息")
   - 新代码: print_log("消息")

2. 替换带有格式化的print语句:
   - 原始代码: print_log(f"实体: {name}")
   - 新代码: print_log(f"实体: {name}")

3. 替换错误消息:
   - 原始代码: print_log(f"错误: {e}", level="error")
   - 新代码: print_log(f"错误: {e}", level="error")

4. 替换成功消息:
   - 原始代码: print_log(f"成功", level="info")
   - 新代码: print_log(f"成功", level="info")

5. 批量迁移提示:
   - 使用IDE的搜索替换功能
   - 针对特定模式的print语句，如错误消息或成功提示，设置不同的替换模式
   - 可以使用正则表达式，如 print\("❌ (.+)"\) -> print_log("$1", level="error")
""" 