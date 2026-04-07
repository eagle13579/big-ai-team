import os
import sys
import json
import logging
import datetime
from typing import Dict, Any, Optional, Callable
from contextvars import ContextVar
from loguru import logger

# 上下文变量
request_id_var = ContextVar("request_id", default=None)
session_id_var = ContextVar("session_id", default=None)
user_id_var = ContextVar("user_id", default=None)


class LoggingConfig:
    """日志配置类"""
    def __init__(self):
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {extra[request_id]} | {message}"
        self.json_format = '{"timestamp":"{time}","level":"{level}","logger":"{name}","function":"{function}","line":{line},"request_id":"{extra.get(\"request_id\", \"-\")}","session_id":"{extra.get(\"session_id\", \"-\")}","user_id":"{extra.get(\"user_id\", \"-\")}","message":"{message}"}'

    def setup(self):
        """设置日志"""
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台处理器
        logger.add(
            sys.stdout,
            level=self.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            colorize=True
        )
        
        # 添加文件处理器（文本格式）
        logger.add(
            os.path.join(self.log_dir, f"agent_{datetime.datetime.now().strftime('%Y%m%d')}.log"),
            level=self.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="10 MB",
            compression="zip",
            encoding="utf-8"
        )
        



class LogContext:
    """日志上下文管理器"""
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.old_values = {}

    def __enter__(self):
        # 保存旧值
        if "request_id" in self.kwargs:
            self.old_values["request_id"] = request_id_var.get()
            request_id_var.set(self.kwargs["request_id"])
        if "session_id" in self.kwargs:
            self.old_values["session_id"] = session_id_var.get()
            session_id_var.set(self.kwargs["session_id"])
        if "user_id" in self.kwargs:
            self.old_values["user_id"] = user_id_var.get()
            user_id_var.set(self.kwargs["user_id"])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复旧值
        for key, value in self.old_values.items():
            if key == "request_id":
                request_id_var.set(value)
            elif key == "session_id":
                session_id_var.set(value)
            elif key == "user_id":
                user_id_var.set(value)


class SensitiveDataFilter:
    """敏感数据过滤器"""
    SENSITIVE_FIELDS = ["password", "token", "api_key", "secret", "credit_card"]
    
    @staticmethod
    def mask_sensitive_data(data: Any) -> Any:
        """脱敏敏感数据"""
        if isinstance(data, dict):
            return {k: SensitiveDataFilter.mask_sensitive_data(v) if k.lower() in SensitiveDataFilter.SENSITIVE_FIELDS else v for k, v in data.items()}
        elif isinstance(data, list):
            return [SensitiveDataFilter.mask_sensitive_data(item) for item in data]
        else:
            return data


def get_logger(name: Optional[str] = None) -> Callable:
    """获取日志记录器"""
    def logger_with_context(message, **kwargs):
        # 添加上下文信息
        extra = {
            "request_id": request_id_var.get(),
            "session_id": session_id_var.get(),
            "user_id": user_id_var.get()
        }
        # 脱敏敏感数据
        kwargs = SensitiveDataFilter.mask_sensitive_data(kwargs)
        # 调用 loguru logger
        logger.bind(**extra).info(message, **kwargs)
    
    return logger_with_context


def get_structured_logger(name: Optional[str] = None):
    """获取结构化日志记录器"""
    def structured_logger(level: str, message: str, **kwargs):
        extra = {
            "request_id": request_id_var.get(),
            "session_id": session_id_var.get(),
            "user_id": user_id_var.get()
        }
        # 脱敏敏感数据
        kwargs = SensitiveDataFilter.mask_sensitive_data(kwargs)
        # 构建结构化消息
        structured_data = {
            "message": message,
            **kwargs
        }
        # 调用 loguru logger
        logger_method = getattr(logger.bind(**extra), level.lower())
        logger_method(json.dumps(structured_data))
    
    return structured_logger


# 初始化日志配置
logging_config = LoggingConfig()
logging_config.setup()

# 导出
__all__ = [
    "logger",
    "LogContext",
    "get_logger",
    "get_structured_logger",
    "SensitiveDataFilter",
    "request_id_var",
    "session_id_var",
    "user_id_var"
]