from loguru import logger
import sys
from typing import Optional


class LLMLogger:
    """LLM 日志管理类"""
    
    @staticmethod
    def setup(level: str = "INFO"):
        """设置日志配置"""
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台处理器
        logger.add(
            sys.stdout,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            colorize=True
        )
        
        # 添加文件处理器
        logger.add(
            "logs/llm.log",
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="10 MB",
            compression="zip"
        )
    
    @staticmethod
    def get_logger(name: Optional[str] = None):
        """获取日志记录器"""
        if name:
            return logger.bind(name=name)
        return logger


# 导出日志记录器
logger = LLMLogger.get_logger("llm")
