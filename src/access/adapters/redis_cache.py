import json
from typing import Any

import redis

from src.shared.cache_config import cache_settings
from src.shared.logging import logger


class RedisCacheAdapter:
    """
    Redis 缓存适配器
    提供分布式缓存功能
    """
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(cache_settings.REDIS_URL, decode_responses=True)
            # 测试连接
            self.redis_client.ping()
            logger.info("✅ Redis 连接成功")
        except Exception as e:
            logger.error(f"❌ Redis 连接失败: {str(e)}")
            self.redis_client = None
    
    def get(self, key: str) -> Any | None:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，如果不存在或出错返回 None
        """
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get 错误: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        if not self.redis_client:
            return False
        
        try:
            value_str = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(key, ttl, value_str)
            return True
        except Exception as e:
            logger.error(f"Redis set 错误: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete 错误: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists 错误: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的缓存
        
        Args:
            pattern: 键模式，如 "tool:*"
            
        Returns:
            删除的键数量
        """
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear_pattern 错误: {str(e)}")
            return 0
    
    def clear_tool_cache(self, tool_name: str) -> int:
        """
        清除指定工具的所有缓存
        
        Args:
            tool_name: 工具名称
            
        Returns:
            删除的键数量
        """
        pattern = f"tool:{tool_name}:*"
        return self.clear_pattern(pattern)
    
    def set_with_tags(self, key: str, value: Any, tags: list[str], ttl: int = 3600) -> bool:
        """
        设置带标签的缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            tags: 标签列表
            ttl: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        if not self.redis_client:
            return False
        
        try:
            # 设置主缓存
            success = self.set(key, value, ttl)
            if not success:
                return False
            
            # 设置标签关联
            for tag in tags:
                tag_key = f"tag:{tag}"
                self.redis_client.sadd(tag_key, key)
                # 为标签设置过期时间，比主缓存长一些
                self.redis_client.expire(tag_key, ttl * 2)
            
            return True
        except Exception as e:
            logger.error(f"Redis set_with_tags 错误: {str(e)}")
            return False
    
    def clear_by_tag(self, tag: str) -> int:
        """
        清除指定标签的所有缓存
        
        Args:
            tag: 标签名称
            
        Returns:
            删除的键数量
        """
        if not self.redis_client:
            return 0
        
        try:
            tag_key = f"tag:{tag}"
            keys = self.redis_client.smembers(tag_key)
            if keys:
                # 删除所有关联的缓存键
                deleted = self.redis_client.delete(*keys)
                # 删除标签本身
                self.redis_client.delete(tag_key)
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Redis clear_by_tag 错误: {str(e)}")
            return 0
    
    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息
        """
        if not self.redis_client:
            return {
                "connected": False,
                "info": {}
            }
        
        try:
            info = self.redis_client.info()
            return {
                "connected": True,
                "info": {
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "used_memory_rss": info.get("used_memory_rss_human", "N/A"),
                    "keys": info.get("db0", {}).get("keys", 0),
                    "expired_keys": info.get("expired_keys", 0),
                    "evicted_keys": info.get("evicted_keys", 0)
                }
            }
        except Exception as e:
            logger.error(f"Redis get_stats 错误: {str(e)}")
            return {
                "connected": True,
                "info": {}
            }

# 单例实例
redis_cache = RedisCacheAdapter()