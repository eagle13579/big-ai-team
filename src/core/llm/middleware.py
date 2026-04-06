from typing import List, Callable, Any, Awaitable, Dict
from .logger import logger


class Middleware:
    """中间件基类"""
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        return request
    
    async def process_response(self, response: Any) -> Any:
        """处理响应"""
        return response
    
    async def process_error(self, error: Exception) -> Exception:
        """处理错误"""
        return error


class MiddlewareManager:
    """中间件管理器"""
    
    def __init__(self):
        self.middlewares: List[Middleware] = []
    
    def add_middleware(self, middleware: Middleware):
        """添加中间件"""
        self.middlewares.append(middleware)
        logger.debug(f"Added middleware: {middleware.__class__.__name__}")
    
    def remove_middleware(self, middleware: Middleware):
        """移除中间件"""
        if middleware in self.middlewares:
            self.middlewares.remove(middleware)
            logger.debug(f"Removed middleware: {middleware.__class__.__name__}")
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        for middleware in self.middlewares:
            try:
                request = await middleware.process_request(request)
            except Exception as e:
                logger.error(f"Middleware {middleware.__class__.__name__} error during request processing: {e}")
        return request
    
    async def process_response(self, response: Any) -> Any:
        """处理响应"""
        for middleware in reversed(self.middlewares):
            try:
                response = await middleware.process_response(response)
            except Exception as e:
                logger.error(f"Middleware {middleware.__class__.__name__} error during response processing: {e}")
        return response
    
    async def process_error(self, error: Exception) -> Exception:
        """处理错误"""
        for middleware in reversed(self.middlewares):
            try:
                error = await middleware.process_error(error)
            except Exception as e:
                logger.error(f"Middleware {middleware.__class__.__name__} error during error processing: {e}")
        return error


# 全局中间件管理器实例
middleware_manager = MiddlewareManager()
