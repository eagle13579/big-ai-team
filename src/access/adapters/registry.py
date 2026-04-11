
from .base import AdapterConfig, BaseAdapter


class AdapterRegistry:
    """适配器注册中心"""

    def __init__(self):
        # 存储适配器类：{platform_type: adapter_class}
        self._adapters: dict[str, type[BaseAdapter]] = {}
        # 存储适配器实例：{name: adapter_instance}
        self._instances: dict[str, BaseAdapter] = {}

    def register(self, platform: str, adapter_class: type[BaseAdapter]):
        """注册适配器类"""
        self._adapters[platform] = adapter_class

    def unregister(self, platform: str):
        """注销适配器类"""
        if platform in self._adapters:
            del self._adapters[platform]

    def get_adapter_class(self, platform: str) -> type[BaseAdapter] | None:
        """获取适配器类"""
        return self._adapters.get(platform)

    def create_instance(self, config: AdapterConfig) -> BaseAdapter:
        """创建适配器实例"""
        platform = config.platform
        adapter_class = self.get_adapter_class(platform)
        if not adapter_class:
            raise ValueError(f"Adapter for platform {platform} not found")

        instance = adapter_class(config)
        self._instances[config.name] = instance
        return instance

    def get_instance(self, name: str) -> BaseAdapter | None:
        """获取适配器实例"""
        return self._instances.get(name)

    def list_instances(self) -> list[BaseAdapter]:
        """列出所有适配器实例"""
        return list(self._instances.values())

    def list_platforms(self) -> list[str]:
        """列出所有支持的平台"""
        return list(self._adapters.keys())

    def remove_instance(self, name: str):
        """移除适配器实例"""
        if name in self._instances:
            del self._instances[name]

    def clear_instances(self):
        """清除所有适配器实例"""
        self._instances.clear()


# 创建全局适配器注册中心实例
adapter_registry = AdapterRegistry()
