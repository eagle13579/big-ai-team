import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# 配置日志
logger = logging.getLogger("AceAgent.Adapters")


class AdapterContext(BaseModel):
    """适配器上下文"""

    session_id: str = Field(..., description="会话ID")
    user_id: str | None = Field(None, description="用户ID")
    request_id: str | None = Field(None, description="请求ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    metadata: dict[str, Any] = Field(default_factory=dict, description="元数据")


class AdapterConfig(BaseModel):
    """适配器配置"""

    name: str = Field(..., description="适配器名称")
    platform: str = Field(..., description="平台类型")
    enabled: bool = Field(default=True, description="是否启用")
    timeout: int = Field(default=30, description="超时时间（秒）")
    retries: int = Field(default=3, description="重试次数")
    config: dict[str, Any] = Field(default_factory=dict, description="具体配置")


T = TypeVar("T")


class BaseAdapter(ABC, Generic[T]):
    """适配器基类"""

    def __init__(self, config: AdapterConfig):
        self.config = config
        self.name = config.name
        self.platform = config.platform
        self.enabled = config.enabled
        self.timeout = config.timeout
        self.retries = config.retries
        self._initialized = False

    @abstractmethod
    async def initialize(self, context: AdapterContext | None = None) -> bool:
        """初始化适配器"""
        pass

    @abstractmethod
    async def execute(
        self, operation: str, params: dict[str, Any], context: AdapterContext | None = None
    ) -> T:
        """执行操作"""
        pass

    @abstractmethod
    async def close(self, context: AdapterContext | None = None) -> bool:
        """关闭适配器"""
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """获取适配器状态"""
        pass

    async def health_check(self, context: AdapterContext | None = None) -> dict[str, Any]:
        """健康检查"""
        try:
            # 执行一个简单的操作来检查健康状态
            await self.execute("health_check", {}, context)
            logger.info(f"Health check passed for {self.platform} adapter: {self.name}")
            return {
                "status": "healthy",
                "platform": self.platform,
                "name": self.name,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(
                f"Health check failed for {self.platform} adapter: {self.name}, error: {str(e)}"
            )
            return {
                "status": "unhealthy",
                "platform": self.platform,
                "name": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized

    def _set_initialized(self, value: bool):
        """设置初始化状态"""
        self._initialized = value
