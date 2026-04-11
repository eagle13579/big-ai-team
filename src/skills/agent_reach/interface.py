from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')

class BaseReachChannel(ABC):
    """所有 Agent-Reach 渠道的抽象基类"""
    
    name: str
    description: str
    platform_type: str
    capabilities: list
    requires_auth: bool = False
    requires_proxy: bool = False
    
    @abstractmethod
    async def execute(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """执行渠道操作"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证渠道配置是否有效"""
        pass
    
    @abstractmethod
    def check_health(self) -> dict[str, Any]:
        """检查渠道健康状态"""
        pass

class ResultWrapper:
    """结果包装器，将原始输出标准化为 Big-AI-Team 可理解的 Observation 格式"""
    
    @staticmethod
    def wrap_result(channel_name: str, action: str, original_result: Any, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """包装结果
        
        Args:
            channel_name: 渠道名称
            action: 执行的操作
            original_result: 原始执行结果
            metadata: 额外的元数据
            
        Returns:
            标准化的 Observation 格式结果
        """
        if metadata is None:
            metadata = {}
        
        return {
            "status": "success",
            "observation": {
                "content": original_result,
                "metadata": {
                    "channel": channel_name,
                    "action": action,
                    "timestamp": ResultWrapper._get_timestamp(),
                    **metadata
                },
                "sources": ResultWrapper._extract_sources(original_result, channel_name)
            }
        }
    
    @staticmethod
    def wrap_error(channel_name: str, action: str, error_message: str) -> dict[str, Any]:
        """包装错误结果
        
        Args:
            channel_name: 渠道名称
            action: 执行的操作
            error_message: 错误信息
            
        Returns:
            标准化的错误格式结果
        """
        return {
            "status": "error",
            "observation": {
                "message": error_message,
                "metadata": {
                    "channel": channel_name,
                    "action": action,
                    "timestamp": ResultWrapper._get_timestamp()
                }
            }
        }
    
    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    @staticmethod
    def _extract_sources(original_result: Any, channel_name: str) -> list:
        """从原始结果中提取引用源"""
        sources = []
        # 根据不同渠道类型提取源信息
        if channel_name == "twitter":
            if isinstance(original_result, list):
                for item in original_result:
                    if isinstance(item, dict) and "url" in item:
                        sources.append(item["url"])
        elif channel_name == "youtube":
            if isinstance(original_result, dict) and "url" in original_result:
                sources.append(original_result["url"])
        elif channel_name == "web":
            if isinstance(original_result, dict) and "url" in original_result:
                sources.append(original_result["url"])
        return sources

class ChannelConfig(BaseModel):
    """渠道配置模型"""
    name: str = Field(..., description="渠道名称")
    description: str = Field(..., description="渠道描述")
    platform_type: str = Field(..., description="平台类型")
    capabilities: list = Field(default_factory=list, description="渠道能力")
    requires_auth: bool = Field(False, description="是否需要认证")
    requires_proxy: bool = Field(False, description="是否需要代理")
    config: dict[str, Any] = Field(default_factory=dict, description="渠道特定配置")

class ReachAction(BaseModel):
    """Agent-Reach 操作模型"""
    action: str = Field(..., description="执行的操作")
    params: dict[str, Any] = Field(..., description="操作参数")

class ReachResult(BaseModel):
    """Agent-Reach 结果模型"""
    status: str = Field(..., description="执行状态")
    observation: dict[str, Any] = Field(..., description="观察结果")
