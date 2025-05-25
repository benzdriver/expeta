#!/usr/bin/env python3
"""
测试集中式日志系统
"""

from common import logger, print_log
from common.logger import Logger
import time

def test_basic_logging():
    """测试基本日志功能"""
    print_log("=== 测试基本日志功能 ===")
    print_log("这是一条使用print_log的基本消息")
    logger.log("这是一条使用logger实例的基本消息")
    
    # 测试不同日志级别
    print_log("这是一条信息级别消息", level="info")
    print_log("这是一条警告级别消息", level="warning")
    print_log("这是一条错误级别消息", level="error")
    print_log("这是一条调试级别消息", level="debug")
    print_log("这是一条严重错误消息", level="critical")
    
    # 测试不同角色
    print_log("这是一条系统角色消息", role="system")
    print_log("这是一条用户角色消息", role="user")
    print_log("这是一条澄清器角色消息", role="clarifier")

def test_module_specific_logging():
    """测试模块专用日志功能"""
    print_log("\n=== 测试模块专用日志功能 ===")
    
    # 创建模块专用日志记录器
    db_logger = Logger.get_instance("database")
    api_logger = Logger.get_instance("api")
    
    # 记录不同模块的日志
    db_logger.log("数据库连接已建立", level="info")
    api_logger.log("API请求已处理", level="info")
    
    # 测试单例模式
    db_logger2 = Logger.get_instance("database")
    db_logger2.log("单例模式测试 - 应该与第一个数据库日志使用相同的实例")

def test_formatted_logging():
    """测试格式化日志消息"""
    print_log("\n=== 测试格式化日志消息 ===")
    
    # 格式化字符串
    entity_name = "User"
    entity_id = 123
    print_log(f"正在处理实体: {entity_name} (ID: {entity_id})")
    
    # 错误消息
    try:
        result = 1 / 0
    except Exception as e:
        print_log(f"操作失败: {str(e)}", level="error")
    
    # 成功消息
    print_log("操作成功完成", level="info")

def main():
    """主函数"""
    print_log("开始测试日志系统...")
    
    # 运行测试
    test_basic_logging()
    test_module_specific_logging()
    test_formatted_logging()
    
    # 访问日志记录
    print_log("\n=== 获取记录的日志 ===")
    logs = logger.get_logs()
    print_log(f"记录的日志数量: {len(logs)}")
    
    # 输出前3条记录的日志
    print_log("前3条日志:")
    for i, log in enumerate(logs[:3]):
        print_log(f"{i+1}. [{log['level']}] {log['content']} (角色: {log['role']})")
    
    print_log("\n测试完成。日志文件可在 ./logs/ 目录下找到")

if __name__ == "__main__":
    main() 