"""
日志模块
提供统一的日志记录功能
"""

import logging
import os
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

class Logger:
    """
    通用日志记录器，支持控制台和文件输出，并按时间戳组织日志文件
    """
    
    _instances = {}  # 类变量，用于存储已创建的实例
    
    @classmethod
    def get_instance(cls, name: str = "app", level: int = logging.INFO):
        """
        获取Logger实例，确保每个名称只创建一个实例（单例模式）
        
        Args:
            name: 日志记录器名称
            level: 日志级别
            
        Returns:
            Logger: 日志记录器实例
        """
        if name not in cls._instances:
            cls._instances[name] = cls(name, level)
        return cls._instances[name]
    
    def __init__(self, name: str = "app", level: int = logging.INFO):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
        """
        self.name = name
        self.logs = []
        
        # 获取当前时间戳，用于日志文件名
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 确保处理器不会重复添加
        if not self.logger.handlers:
            # 添加控制台handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # 创建日志目录，直接在项目根目录下
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # 创建基于时间戳的日志子目录
            timestamp_dir = log_dir / self.timestamp
            timestamp_dir.mkdir(exist_ok=True)
            
            # 添加文件handler，文件名包含时间戳
            file_handler = logging.FileHandler(timestamp_dir / f"{name}.log")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log(self, message: str, level: str = "info", role: str = "system") -> None:
        """
        记录日志消息
        
        Args:
            message: 日志消息
            level: 日志级别
            role: 消息角色
        """
        # 将消息添加到内存日志
        self.logs.append({
            "role": role,
            "content": message,
            "level": level,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # 记录到logger
        if level == "debug":
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "critical":
            self.logger.critical(message)
        
        # 如果是system、clarifier或user角色的消息，打印到控制台
        if role in ["system", "clarifier", "user"]:
            prefix = {
                "system": "🔧 ",
                "clarifier": "🤖 ",
                "user": "👤 "
            }.get(role, "")
            print(f"{prefix}{message}")
    
    def get_logs(self, role: Optional[str] = None) -> List[Dict[str, str]]:
        """
        获取日志记录
        
        Args:
            role: 过滤的角色
            
        Returns:
            日志记录列表
        """
        if role:
            return [log for log in self.logs if log["role"] == role]
        return self.logs

# 创建默认日志记录器实例，便于直接导入使用
default_logger = Logger.get_instance("expeta")

def log_print(message: str, level: str = "info", role: str = "system"):
    """
    用于替代print函数的日志记录工具
    
    Args:
        message: 日志消息
        level: 日志级别
        role: 消息角色
    """
    default_logger.log(message, level, role) 