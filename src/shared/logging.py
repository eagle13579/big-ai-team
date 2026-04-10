import datetime
import json
import os
import sys
import traceback
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Callable, Optional

from loguru import logger

# 上下文变量
request_id_var = ContextVar("request_id", default=None)
session_id_var = ContextVar("session_id", default=None)
user_id_var = ContextVar("user_id", default=None)
task_id_var = ContextVar("task_id", default=None)


class LoggingConfig:
    """日志配置类"""

    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_log_size = os.getenv("MAX_LOG_SIZE", "10 MB")
        self.log_retention = os.getenv("LOG_RETENTION", "7 days")

        # 日志格式
        self.console_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
        )
        self.file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
        )
        self.json_format = '{"timestamp": "{time}", "level": "{level}", "logger": "{name}", "function": "{function}", "line": {line}, "message": "{message}"}'

    def setup(self):
        """设置日志"""
        # 移除默认处理器
        logger.remove()

        # 添加控制台处理器
        logger.add(
            sys.stdout,
            level=self.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            colorize=True,
            backtrace=True,
            diagnose=True,
        )

        # 添加文件处理器（文本格式）
        logger.add(
            str(self.log_dir / f"agent_{datetime.datetime.now().strftime('%Y%m%d')}.log"),
            level=self.log_level,
            format=self.file_format,
            rotation=self.max_log_size,
            retention=self.log_retention,
            compression="zip",
            encoding="utf-8",
            backtrace=True,
            diagnose=True,
        )

        # 添加 JSON 格式日志处理器（用于监控系统）
        logger.add(
            str(self.log_dir / f"agent_{datetime.datetime.now().strftime('%Y%m%d')}.json"),
            level=self.log_level,
            format=self.json_format,
            rotation=self.max_log_size,
            retention=self.log_retention,
            compression="zip",
            encoding="utf-8",
            serialize=True,
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
        if "task_id" in self.kwargs:
            self.old_values["task_id"] = task_id_var.get()
            task_id_var.set(self.kwargs["task_id"])
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
            elif key == "task_id":
                task_id_var.set(value)


class SensitiveDataFilter:
    """敏感数据过滤器"""

    SENSITIVE_FIELDS = [
        "password",
        "token",
        "api_key",
        "secret",
        "credit_card",
        "access_token",
        "refresh_token",
        "secret_key",
        "private_key",
        "ssh_key",
        "passphrase",
        "otp",
        "code",
        "pin",
    ]

    @staticmethod
    def mask_sensitive_data(data: Any) -> Any:
        """脱敏敏感数据"""
        if isinstance(data, dict):
            return {
                k: SensitiveDataFilter._mask_value(v)
                if k.lower() in SensitiveDataFilter.SENSITIVE_FIELDS
                else SensitiveDataFilter.mask_sensitive_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [SensitiveDataFilter.mask_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            # 检查字符串是否包含敏感信息
            for field in SensitiveDataFilter.SENSITIVE_FIELDS:
                if field in data.lower():
                    return "[REDACTED]"
            return data
        else:
            return data

    @staticmethod
    def _mask_value(value: Any) -> str:
        """掩码值"""
        if isinstance(value, str):
            if len(value) <= 4:
                return "****"
            elif len(value) <= 8:
                return value[:2] + "****" + value[-2:]
            else:
                return value[:4] + "****" + value[-4:]
        return "[REDACTED]"


class LoggingMiddleware:
    """日志中间件"""

    async def __call__(self, request, call_next):
        # 生成请求 ID
        import uuid

        request_id = str(uuid.uuid4())

        # 设置上下文
        token = request_id_var.set(request_id)

        try:
            # 记录请求开始
            logger.info(
                f"🚀 请求开始: {request.method} {request.url.path}",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                headers={
                    k: v
                    for k, v in request.headers.items()
                    if k.lower() not in ["authorization", "cookie"]
                },
            )

            # 处理请求
            response = await call_next(request)

            # 记录请求结束
            logger.info(
                f"✅ 请求结束: {request.method} {request.url.path} {response.status_code}",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )

            return response
        except Exception as e:
            # 记录异常
            logger.error(
                f"💥 请求异常: {request.method} {request.url.path}",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                traceback=traceback.format_exc(),
            )
            raise
        finally:
            # 恢复上下文
            request_id_var.reset(token)


def get_logger(name: Optional[str] = None) -> Callable:
    """获取日志记录器"""

    def logger_with_context(message, **kwargs):
        # 添加上下文信息
        extra = {
            "request_id": request_id_var.get(),
            "session_id": session_id_var.get(),
            "user_id": user_id_var.get(),
            "task_id": task_id_var.get(),
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
            "user_id": user_id_var.get(),
            "task_id": task_id_var.get(),
        }
        # 脱敏敏感数据
        kwargs = SensitiveDataFilter.mask_sensitive_data(kwargs)
        # 构建结构化消息
        structured_data = {"message": message, **kwargs}
        # 调用 loguru logger
        logger_method = getattr(logger.bind(**extra), level.lower())
        logger_method(json.dumps(structured_data))

    return structured_logger


def log_exception(exc: Exception, message: str = "未处理的异常"):
    """记录异常"""
    extra = {
        "request_id": request_id_var.get(),
        "session_id": session_id_var.get(),
        "user_id": user_id_var.get(),
        "task_id": task_id_var.get(),
    }
    logger.error(message, error=str(exc), traceback=traceback.format_exc(), **extra)


# 初始化日志配置
logging_config = LoggingConfig()
logging_config.setup()

# 导出
__all__ = [
    "logger",
    "LogContext",
    "LoggingMiddleware",
    "get_logger",
    "get_structured_logger",
    "log_exception",
    "SensitiveDataFilter",
    "request_id_var",
    "session_id_var",
    "user_id_var",
    "task_id_var",
]
