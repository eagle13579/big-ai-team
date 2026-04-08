from typing import Optional, Dict, Any
from .base import BaseAdapter, AdapterConfig
from .registry import adapter_registry
from .platforms import PlatformType


class AdapterFactory:
    """适配器工厂"""
    
    @staticmethod
    def create_adapter(platform: str, name: str, config: Dict[str, Any]) -> BaseAdapter:
        """创建适配器
        
        Args:
            platform: 平台类型
            name: 适配器名称
            config: 适配器配置
            
        Returns:
            BaseAdapter: 适配器实例
        """
        adapter_config = AdapterConfig(
            name=name,
            platform=platform,
            config=config
        )
        
        return adapter_registry.create_instance(adapter_config)
    
    @staticmethod
    def create_llm_adapter(platform: str, name: str, api_key: str, **kwargs) -> BaseAdapter:
        """创建LLM适配器
        
        Args:
            platform: 平台类型
            name: 适配器名称
            api_key: API密钥
            **kwargs: 其他配置
            
        Returns:
            BaseAdapter: LLM适配器实例
        """
        config = {
            "api_key": api_key,
            **kwargs
        }
        return AdapterFactory.create_adapter(platform, name, config)
    
    @staticmethod
    def create_database_adapter(platform: str, name: str, connection_string: str, **kwargs) -> BaseAdapter:
        """创建数据库适配器
        
        Args:
            platform: 平台类型
            name: 适配器名称
            connection_string: 连接字符串
            **kwargs: 其他配置
            
        Returns:
            BaseAdapter: 数据库适配器实例
        """
        config = {
            "connection_string": connection_string,
            **kwargs
        }
        return AdapterFactory.create_adapter(platform, name, config)
    
    @staticmethod
    def create_cache_adapter(platform: str, name: str, **kwargs) -> BaseAdapter:
        """创建缓存适配器
        
        Args:
            platform: 平台类型
            name: 适配器名称
            **kwargs: 配置
            
        Returns:
            BaseAdapter: 缓存适配器实例
        """
        return AdapterFactory.create_adapter(platform, name, kwargs)
    
    @staticmethod
    def create_storage_adapter(platform: str, name: str, **kwargs) -> BaseAdapter:
        """创建存储适配器
        
        Args:
            platform: 平台类型
            name: 适配器名称
            **kwargs: 配置
            
        Returns:
            BaseAdapter: 存储适配器实例
        """
        return AdapterFactory.create_adapter(platform, name, kwargs)
    
    @staticmethod
    def create_sandbox_adapter(platform: str, name: str, **kwargs) -> BaseAdapter:
        """创建执行沙箱适配器
        
        Args:
            platform: 平台类型
            name: 适配器名称
            **kwargs: 配置
            
        Returns:
            BaseAdapter: 执行沙箱适配器实例
        """
        return AdapterFactory.create_adapter(platform, name, kwargs)
    
    @staticmethod
    def create_monitoring_adapter(platform: str, name: str, **kwargs) -> BaseAdapter:
        """创建监控适配器
        
        Args:
            platform: 平台类型
            name: 适配器名称
            **kwargs: 配置
            
        Returns:
            BaseAdapter: 监控适配器实例
        """
        return AdapterFactory.create_adapter(platform, name, kwargs)
    
    @staticmethod
    def create_messaging_adapter(platform: str, name: str, **kwargs) -> BaseAdapter:
        """创建消息队列适配器
        
        Args:
            platform: 平台类型
            name: 适配器名称
            **kwargs: 配置
            
        Returns:
            BaseAdapter: 消息队列适配器实例
        """
        return AdapterFactory.create_adapter(platform, name, kwargs)
