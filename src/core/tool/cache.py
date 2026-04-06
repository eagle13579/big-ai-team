from typing import Dict, Any, Optional, Tuple
import hashlib
import time
import logging

logger = logging.getLogger(__name__)


class ToolCache:
    """
    工具执行结果缓存
    """
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        初始化缓存
        
        Args:
            max_size: 缓存最大容量
            ttl: 缓存过期时间（秒）
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.access_order: list = []

    def _generate_key(self, tool_name: str, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            str: 缓存键
        """
        # 对参数进行排序，确保相同参数生成相同的键
        sorted_args = sorted(kwargs.items())
        args_str = str(sorted_args)
        key = f"{tool_name}:{args_str}"
        # 使用 MD5 生成固定长度的键
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, tool_name: str, **kwargs) -> Optional[Any]:
        """
        获取缓存结果
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            Optional[Any]: 缓存的结果，如果不存在或已过期则返回 None
        """
        key = self._generate_key(tool_name, **kwargs)
        
        if key in self.cache:
            value, timestamp = self.cache[key]
            # 检查是否过期
            if time.time() - timestamp < self.ttl:
                # 更新访问顺序，用于 LRU 缓存
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
                logger.debug(f"Cache hit for tool {tool_name}")
                return value
            else:
                # 过期，删除缓存
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                logger.debug(f"Cache expired for tool {tool_name}")
        
        logger.debug(f"Cache miss for tool {tool_name}")
        return None

    def set(self, tool_name: str, result: Any, **kwargs) -> None:
        """
        设置缓存结果
        
        Args:
            tool_name: 工具名称
            result: 执行结果
            **kwargs: 工具参数
        """
        key = self._generate_key(tool_name, **kwargs)
        
        # 如果缓存已满，删除最久未使用的项
        if len(self.cache) >= self.max_size:
            if self.access_order:
                oldest_key = self.access_order.pop(0)
                if oldest_key in self.cache:
                    del self.cache[oldest_key]
                    logger.debug(f"Cache evicted: {oldest_key}")
        
        # 设置缓存
        self.cache[key] = (result, time.time())
        # 更新访问顺序
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        logger.debug(f"Cache set for tool {tool_name}")

    def clear(self) -> None:
        """
        清空缓存
        """
        self.cache.clear()
        self.access_order.clear()
        logger.info("Cache cleared")

    def get_size(self) -> int:
        """
        获取缓存大小
        
        Returns:
            int: 缓存大小
        """
        return len(self.cache)


# 创建全局缓存实例
tool_cache = ToolCache()