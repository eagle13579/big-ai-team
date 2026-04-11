from typing import Any

import redis

from ..shared.config import settings


class ContextManager:
    """上下文管理器"""

    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def set_context(self, session_id: str, context: dict[str, Any]) -> bool:
        """设置会话上下文"""
        try:
            self.redis_client.hset(f"context:{session_id}", mapping=context)
            # 设置过期时间为24小时
            self.redis_client.expire(f"context:{session_id}", 86400)
            return True
        except Exception:
            return False

    def get_context(self, session_id: str) -> dict[str, Any] | None:
        """获取会话上下文"""
        try:
            context = self.redis_client.hgetall(f"context:{session_id}")
            return context if context else None
        except Exception:
            return None

    def update_context(self, session_id: str, key: str, value: Any) -> bool:
        """更新上下文值"""
        try:
            self.redis_client.hset(f"context:{session_id}", key, value)
            return True
        except Exception:
            return False

    def delete_context(self, session_id: str) -> bool:
        """删除会话上下文"""
        try:
            self.redis_client.delete(f"context:{session_id}")
            return True
        except Exception:
            return False

    def get_hot_memory(self, session_id: str) -> dict[str, Any] | None:
        """获取热记忆"""
        return self.get_context(session_id)

    def set_hot_memory(self, session_id: str, memory: dict[str, Any]) -> bool:
        """设置热记忆"""
        return self.set_context(session_id, memory)
