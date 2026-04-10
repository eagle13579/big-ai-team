import time
from abc import abstractmethod
from typing import Any, Optional

import redis

from .base import AdapterContext, BaseAdapter
from .registry import adapter_registry


class CacheAdapter(BaseAdapter[dict[str, Any]]):
    """缓存适配器基类"""

    async def execute(
        self, operation: str, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """执行缓存操作"""
        if operation == "get":
            return await self.get(params, context)
        elif operation == "set":
            return await self.set(params, context)
        elif operation == "delete":
            return await self.delete(params, context)
        elif operation == "health_check":
            return await self._health_check(context)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    @abstractmethod
    async def get(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """获取缓存"""
        pass

    @abstractmethod
    async def set(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """设置缓存"""
        pass

    @abstractmethod
    async def delete(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """删除缓存"""
        pass

    async def _health_check(self, context: Optional[AdapterContext] = None) -> dict[str, Any]:
        """健康检查"""
        try:
            await self.set({"key": "health_check", "value": "ok", "ttl": 10}, context)
            result = await self.get({"key": "health_check"}, context)
            if result.get("value") == "ok":
                return {
                    "status": "healthy",
                    "platform": self.platform,
                    "timestamp": context.timestamp.isoformat() if context else None,
                }
            else:
                return {
                    "status": "unhealthy",
                    "platform": self.platform,
                    "error": "Health check failed",
                    "timestamp": context.timestamp.isoformat() if context else None,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "platform": self.platform,
                "error": str(e),
                "timestamp": context.timestamp.isoformat() if context else None,
            }


class RedisAdapter(CacheAdapter):
    """Redis 适配器"""

    def __init__(self, config):
        super().__init__(config)
        self.host = self.config.config.get("host", "localhost")
        self.port = self.config.config.get("port", 6379)
        self.db = self.config.config.get("db", 0)
        self.password = self.config.config.get("password")
        self.client = None

    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )
            # 测试连接
            self.client.ping()
            self._set_initialized(True)
            return True
        except Exception as e:
            raise Exception(f"Failed to initialize Redis adapter: {str(e)}")

    async def get(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """获取缓存"""
        if not self.client:
            await self.initialize(context)

        key = params.get("key")
        if not key:
            raise ValueError("Key is required")

        try:
            value = self.client.get(key)
            return {"value": value}
        except Exception as e:
            raise Exception(f"Get operation failed: {str(e)}")

    async def set(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """设置缓存"""
        if not self.client:
            await self.initialize(context)

        key = params.get("key")
        value = params.get("value")
        ttl = params.get("ttl")

        if not key or value is None:
            raise ValueError("Key and value are required")

        try:
            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)
            return {"success": True}
        except Exception as e:
            raise Exception(f"Set operation failed: {str(e)}")

    async def delete(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """删除缓存"""
        if not self.client:
            await self.initialize(context)

        key = params.get("key")
        if not key:
            raise ValueError("Key is required")

        try:
            result = self.client.delete(key)
            return {"deleted": result > 0}
        except Exception as e:
            raise Exception(f"Delete operation failed: {str(e)}")

    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        if self.client:
            self.client.close()
            self.client = None
        self._set_initialized(False)
        return True

    def get_status(self) -> dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "host": self.host,
            "port": self.port,
            "db": self.db,
        }


class MemoryCacheAdapter(CacheAdapter):
    """内存缓存适配器"""

    def __init__(self, config):
        super().__init__(config)
        self.cache = {}
        self.expiry = {}

    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        self.cache = {}
        self.expiry = {}
        self._set_initialized(True)
        return True

    async def get(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """获取缓存"""
        key = params.get("key")
        if not key:
            raise ValueError("Key is required")

        # 检查是否过期
        if key in self.expiry and self.expiry[key] < time.time():
            del self.cache[key]
            del self.expiry[key]
            return {"value": None}

        return {"value": self.cache.get(key)}

    async def set(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """设置缓存"""
        key = params.get("key")
        value = params.get("value")
        ttl = params.get("ttl")

        if not key or value is None:
            raise ValueError("Key and value are required")

        self.cache[key] = value
        if ttl:
            self.expiry[key] = time.time() + ttl
        else:
            if key in self.expiry:
                del self.expiry[key]

        return {"success": True}

    async def delete(
        self, params: dict[str, Any], context: Optional[AdapterContext] = None
    ) -> dict[str, Any]:
        """删除缓存"""
        key = params.get("key")
        if not key:
            raise ValueError("Key is required")

        deleted = key in self.cache
        if deleted:
            del self.cache[key]
            if key in self.expiry:
                del self.expiry[key]

        return {"deleted": deleted}

    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        self.cache.clear()
        self.expiry.clear()
        self._set_initialized(False)
        return True

    def get_status(self) -> dict[str, Any]:
        """获取适配器状态"""
        # 清理过期项
        current_time = time.time()
        expired_keys = [key for key, exp in self.expiry.items() if exp < current_time]
        for key in expired_keys:
            del self.cache[key]
            del self.expiry[key]

        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "item_count": len(self.cache),
        }


# 注册缓存适配器
adapter_registry.register("redis", RedisAdapter)
adapter_registry.register("memory_cache", MemoryCacheAdapter)
