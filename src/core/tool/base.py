from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Protocol
from pydantic import BaseModel, Field, ValidationError
import logging
from .exceptions import ToolValidationError, ToolExecutionError
from .cache import tool_cache
from .monitoring import MetricsDecorator, monitoring_manager

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    """
    工具执行结果模型
    """
    success: bool
    data: Any = None
    error: Optional[str] = None


class LLMProtocol(Protocol):
    """
    LLM 协议接口
    """
    async def generate(self, prompt: str) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 提示文本
            
        Returns:
            生成的文本
        """
        ...


class BaseTool(ABC):
    """
    工具抽象基类
    """
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    @MetricsDecorator.track_execution
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        pass

    async def _execute_with_validation(self, **kwargs) -> ToolResult:
        """
        执行工具并进行参数验证
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 工具执行结果
        """
        try:
            validated_args = self.args_schema(**kwargs)
            validated_kwargs = validated_args.model_dump()
            
            # 检查缓存
            cached_result = tool_cache.get(self.name, **validated_kwargs)
            if cached_result:
                logger.info(f"Cache hit for tool {self.name}")
                return cached_result
            
            # 缓存未命中，执行工具
            logger.info(f"Executing tool {self.name} with args: {validated_kwargs}")
            result = await self.execute(**validated_kwargs)
            logger.info(f"Tool {self.name} executed successfully: {result.success}")
            
            # 将结果存入缓存
            if result.success:
                tool_cache.set(self.name, result, **validated_kwargs)
            
            return result
        except ValidationError as e:
            error_msg = str(e)
            logger.error(f"Validation error for tool {self.name}: {error_msg}")
            return ToolResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing tool {self.name}: {error_msg}")
            return ToolResult(success=False, error=error_msg)