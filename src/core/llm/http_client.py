import httpx
import hashlib
import json
from typing import Dict, Any, Optional, AsyncGenerator
from .logger import logger


class HTTPClientManager:
    """HTTP 客户端管理器，实现连接池和缓存"""
    
    def __init__(self):
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._cache: Dict[str, Any] = {}
    
    async def get_client(self, base_url: str) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if base_url not in self._clients:
            self._clients[base_url] = httpx.AsyncClient(
                base_url=base_url,
                timeout=30.0,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20
                )
            )
            logger.debug(f"Created new HTTP client for {base_url}")
        return self._clients[base_url]
    
    async def close_all(self):
        """关闭所有 HTTP 客户端"""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()
        logger.debug("Closed all HTTP clients")
    
    def _generate_cache_key(self, url: str, method: str, data: Optional[Dict[str, Any]] = None) -> str:
        """生成缓存键"""
        key = f"{method}:{url}"
        if data:
            key += f":{hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()}"
        return key
    
    def get_from_cache(self, url: str, method: str, data: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """从缓存获取数据"""
        key = self._generate_cache_key(url, method, data)
        if key in self._cache:
            logger.debug(f"Cache hit for {url}")
            return self._cache[key]
        logger.debug(f"Cache miss for {url}")
        return None
    
    def set_to_cache(self, url: str, method: str, data: Optional[Dict[str, Any]] = None, value: Any = None):
        """设置缓存数据"""
        key = self._generate_cache_key(url, method, data)
        self._cache[key] = value
        logger.debug(f"Cached data for {url}")
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        logger.debug("Cleared cache")


# 全局 HTTP 客户端管理器实例
http_client_manager = HTTPClientManager()
