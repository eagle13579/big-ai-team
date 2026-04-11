from collections.abc import Callable
from typing import Any

from src.shared.logging import logger

from .multi_level_cache import multi_level_cache


class CacheManager:
    """
    缓存管理器
    提供高级缓存操作功能，包括：
    1. 缓存键管理
    2. 缓存策略配置
    3. 缓存装饰器
    4. 缓存失效策略
    """
    
    def __init__(self):
        self.cache_prefixes = {
            "tool": "tool",
            "api": "api",
            "data": "data",
            "model": "model"
        }
    
    def get_cache_key(self, category: str, *args, **kwargs) -> str:
        """
        获取缓存键
        """
        prefix = self.cache_prefixes.get(category, "default")
        return multi_level_cache._generate_cache_key(prefix, *args, **kwargs)
    
    def get(self, category: str, *args, **kwargs) -> Any | None:
        """
        获取缓存
        """
        prefix = self.cache_prefixes.get(category, "default")
        return multi_level_cache.get(prefix, *args, **kwargs)
    
    def set(self, category: str, value: Any, ttl: int = 3600, *args, **kwargs) -> bool:
        """
        设置缓存
        """
        prefix = self.cache_prefixes.get(category, "default")
        return multi_level_cache.set(prefix, value, ttl, *args, **kwargs)
    
    def delete(self, category: str, *args, **kwargs) -> bool:
        """
        删除缓存
        """
        prefix = self.cache_prefixes.get(category, "default")
        return multi_level_cache.delete(prefix, *args, **kwargs)
    
    def delete_category(self, category: str) -> int:
        """
        删除指定类别的所有缓存
        """
        from src.shared.cache_config import cache_settings
        prefix = self.cache_prefixes.get(category, "default")
        pattern = f"{cache_settings.CACHE_KEY_PREFIX}:{prefix}:*"
        return multi_level_cache.delete_pattern(pattern)
    
    def cache(self, category: str, ttl: int = 3600):
        """
        缓存装饰器
        用于装饰函数，自动缓存函数返回值
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # 生成缓存键
                self.get_cache_key(category, *args, **kwargs)
                
                # 尝试从缓存获取
                cached_value = multi_level_cache.get(category, *args, **kwargs)
                if cached_value is not None:
                    logger.debug(f"从缓存获取函数结果: {func.__name__}")
                    return cached_value
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 缓存结果
                multi_level_cache.set(category, result, ttl, *args, **kwargs)
                logger.debug(f"缓存函数结果: {func.__name__}")
                
                return result
            return wrapper
        return decorator
    
    def cache_warmup(self, items: list[dict[str, Any]]) -> int:
        """
        缓存预热
        
        Args:
            items: 预热项列表，每个元素包含：
                - category: 缓存类别
                - value: 缓存值
                - ttl: 过期时间
                - args: 位置参数
                - kwargs: 关键字参数
        
        Returns:
            预热成功的数量
        """
        warmup_items = []
        for item in items:
            category = item.get("category", "default")
            value = item.get("value")
            ttl = item.get("ttl", 3600)
            args = item.get("args", [])
            kwargs = item.get("kwargs", {})
            
            prefix = self.cache_prefixes.get(category, "default")
            warmup_items.append((prefix, value, ttl, args, kwargs))
        
        return multi_level_cache.cache_warmup(warmup_items)
    
    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息
        """
        return multi_level_cache.get_cache_stats()
    
    def clear_all(self) -> bool:
        """
        清除所有缓存
        """
        return multi_level_cache.clear_all()


# 单例实例
cache_manager = CacheManager()
