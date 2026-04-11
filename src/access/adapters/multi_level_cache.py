import time
import hashlib
from typing import Any, Optional, Dict, List, Tuple

from src.shared.config import settings
from src.shared.logging import logger
from src.shared.cache_config import cache_settings
from .redis_cache import redis_cache


class MultiLevelCache:
    """
    多级缓存实现
    1. 本地内存缓存（一级缓存）
    2. Redis 分布式缓存（二级缓存）
    """
    
    def __init__(self):
        # 初始化本地内存缓存
        self.local_cache = {}
        self.local_expiry = {}
        self.local_cache_size = cache_settings.LOCAL_CACHE_SIZE  # 本地缓存大小限制
        
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        生成优化的缓存键
        1. 使用前缀区分不同类型的缓存
        2. 对参数进行哈希处理，确保键的唯一性和长度合理性
        """
        # 构建键的基本部分
        key_parts = [cache_settings.CACHE_KEY_PREFIX, prefix]
        
        # 添加位置参数
        for arg in args:
            key_parts.append(str(arg))
        
        # 添加关键字参数（按字母顺序排序，确保一致性）
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        # 组合成字符串
        key_string = ":".join(key_parts)
        
        # 对长键进行哈希处理，确保键的长度合理
        if len(key_string) > 100:
            hash_part = hashlib.md5(key_string.encode()).hexdigest()
            key_string = f"{prefix}:{hash_part}"
        
        return key_string
    
    def get(self, prefix: str, *args, **kwargs) -> Optional[Any]:
        """
        获取缓存
        1. 先从本地缓存获取
        2. 如果本地缓存没有，从 Redis 获取
        3. 如果 Redis 有，同步到本地缓存
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(prefix, *args, **kwargs)
        
        # 1. 检查本地缓存
        if cache_key in self.local_cache:
            # 检查是否过期
            if cache_key in self.local_expiry and self.local_expiry[cache_key] < time.time():
                # 删除过期缓存
                del self.local_cache[cache_key]
                del self.local_expiry[cache_key]
            else:
                logger.debug(f"从本地缓存获取: {cache_key}")
                return self.local_cache[cache_key]
        
        # 2. 检查 Redis 缓存
        redis_value = redis_cache.get(cache_key)
        if redis_value is not None:
            logger.debug(f"从 Redis 缓存获取: {cache_key}")
            # 同步到本地缓存（默认 5 分钟过期）
            self._set_local_cache(cache_key, redis_value, 300)
            return redis_value
        
        return None
    
    def set(self, prefix: str, value: Any, ttl: int = 3600, *args, **kwargs) -> bool:
        """
        设置缓存
        1. 同时设置本地缓存和 Redis 缓存
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(prefix, *args, **kwargs)
        
        # 1. 设置本地缓存
        self._set_local_cache(cache_key, value, ttl)
        
        # 2. 设置 Redis 缓存
        redis_success = redis_cache.set(cache_key, value, ttl)
        
        logger.debug(f"设置缓存: {cache_key}, ttl: {ttl}")
        return redis_success
    
    def _set_local_cache(self, key: str, value: Any, ttl: int):
        """
        设置本地缓存，处理缓存大小限制
        """
        # 检查缓存大小，如果超过限制，删除最旧的缓存
        if len(self.local_cache) >= self.local_cache_size:
            # 找到最早过期的键
            oldest_key = min(self.local_expiry, key=lambda k: self.local_expiry.get(k, float('inf')))
            if oldest_key in self.local_cache:
                del self.local_cache[oldest_key]
                del self.local_expiry[oldest_key]
        
        # 设置缓存
        self.local_cache[key] = value
        self.local_expiry[key] = time.time() + ttl
    
    def delete(self, prefix: str, *args, **kwargs) -> bool:
        """
        删除缓存
        1. 同时删除本地缓存和 Redis 缓存
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(prefix, *args, **kwargs)
        
        # 1. 删除本地缓存
        if cache_key in self.local_cache:
            del self.local_cache[cache_key]
            if cache_key in self.local_expiry:
                del self.local_expiry[cache_key]
        
        # 2. 删除 Redis 缓存
        redis_success = redis_cache.delete(cache_key)
        
        logger.debug(f"删除缓存: {cache_key}")
        return redis_success
    
    def delete_pattern(self, pattern: str) -> int:
        """
        删除匹配模式的缓存
        """
        # 删除本地缓存中匹配的键
        local_keys_to_delete = [key for key in self.local_cache if pattern in key]
        for key in local_keys_to_delete:
            del self.local_cache[key]
            if key in self.local_expiry:
                del self.local_expiry[key]
        
        # 删除 Redis 中匹配的键
        redis_deleted = redis_cache.clear_pattern(pattern)
        
        total_deleted = len(local_keys_to_delete) + redis_deleted
        logger.debug(f"删除匹配模式的缓存: {pattern}, 共删除 {total_deleted} 个")
        return total_deleted
    
    def cache_warmup(self, items: List[Tuple[str, Any, int, List[Any], Dict[str, Any]]]) -> int:
        """
        缓存预热
        
        Args:
            items: 预热项列表，每个元素为 (prefix, value, ttl, args, kwargs)
        
        Returns:
            预热成功的数量
        """
        success_count = 0
        
        for prefix, value, ttl, args, kwargs in items:
            if self.set(prefix, value, ttl, *args, **kwargs):
                success_count += 1
        
        logger.info(f"缓存预热完成，成功预热 {success_count} 个项目")
        return success_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        """
        # 清理本地缓存中的过期项
        current_time = time.time()
        expired_local = [key for key, exp in self.local_expiry.items() if exp < current_time]
        for key in expired_local:
            del self.local_cache[key]
            del self.local_expiry[key]
        
        # 获取 Redis 统计信息
        redis_stats = redis_cache.get_stats()
        
        return {
            "local_cache": {
                "item_count": len(self.local_cache),
                "size_limit": self.local_cache_size,
                "expired_count": len(expired_local)
            },
            "redis_cache": redis_stats
        }
    
    def clear_all(self) -> bool:
        """
        清除所有缓存
        """
        # 清除本地缓存
        self.local_cache.clear()
        self.local_expiry.clear()
        
        # 清除 Redis 缓存（谨慎使用）
        # 注意：这里只清除当前项目的缓存，避免影响其他应用
        redis_deleted = redis_cache.clear_pattern("*")
        
        logger.info(f"清除所有缓存，Redis 清除 {redis_deleted} 个键")
        return True


# 单例实例
multi_level_cache = MultiLevelCache()
