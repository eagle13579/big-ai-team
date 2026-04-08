from typing import Dict, Any, Optional, List, Tuple
import redis
import json
from ..shared.config import settings


class Message:
    """消息类"""
    def __init__(self, role: str, content: str, timestamp: float):
        self.role = role
        self.content = content
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建实例"""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"]
        )


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, max_window_size: int = 10, max_tokens: int = 4000):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.max_window_size = max_window_size  # 最大消息窗口大小
        self.max_tokens = max_tokens  # 最大 Token 数
    
    def set_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """设置会话上下文"""
        try:
            self.redis_client.hset(f"context:{session_id}", mapping=context)
            # 设置过期时间为24小时
            self.redis_client.expire(f"context:{session_id}", 86400)
            return True
        except Exception:
            return False
    
    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
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
            # 删除上下文和消息历史
            self.redis_client.delete(f"context:{session_id}")
            self.redis_client.delete(f"messages:{session_id}")
            return True
        except Exception:
            return False
    
    def get_hot_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取热记忆"""
        return self.get_context(session_id)
    
    def set_hot_memory(self, session_id: str, memory: Dict[str, Any]) -> bool:
        """设置热记忆"""
        return self.set_context(session_id, memory)
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """添加消息到历史记录"""
        try:
            import time
            message = Message(role=role, content=content, timestamp=time.time())
            # 将消息添加到 Redis 列表
            self.redis_client.lpush(f"messages:{session_id}", json.dumps(message.to_dict()))
            # 应用滑动窗口
            self._apply_sliding_window(session_id)
            return True
        except Exception:
            return False
    
    def get_message_history(self, session_id: str) -> List[Message]:
        """获取消息历史"""
        try:
            messages = self.redis_client.lrange(f"messages:{session_id}", 0, -1)
            return [Message.from_dict(json.loads(msg)) for msg in reversed(messages)]
        except Exception:
            return []
    
    def get_sliding_window(self, session_id: str) -> List[Message]:
        """获取滑动窗口内的消息"""
        try:
            # 获取当前消息历史
            messages = self.redis_client.lrange(f"messages:{session_id}", 0, self.max_window_size - 1)
            return [Message.from_dict(json.loads(msg)) for msg in reversed(messages)]
        except Exception:
            return []
    
    def _apply_sliding_window(self, session_id: str) -> None:
        """应用滑动窗口"""
        try:
            # 裁剪消息列表，保持在窗口大小内
            self.redis_client.ltrim(f"messages:{session_id}", 0, self.max_window_size - 1)
            # 检查 Token 数
            self._check_token_limit(session_id)
        except Exception:
            pass
    
    def _check_token_limit(self, session_id: str) -> None:
        """检查并限制 Token 数"""
        try:
            messages = self.get_message_history(session_id)
            total_tokens = 0
            valid_messages = []
            
            # 估算 Token 数并保持在限制内
            for msg in messages:
                # 简单估算：每个字符约 0.75 个 Token
                msg_tokens = int(len(msg.content) * 0.75)
                if total_tokens + msg_tokens <= self.max_tokens:
                    total_tokens += msg_tokens
                    valid_messages.append(msg)
                else:
                    break
            
            # 更新消息历史
            if len(valid_messages) < len(messages):
                self.redis_client.delete(f"messages:{session_id}")
                for msg in reversed(valid_messages):
                    self.redis_client.lpush(f"messages:{session_id}", json.dumps(msg.to_dict()))
        except Exception:
            pass
    
    def clear_message_history(self, session_id: str) -> bool:
        """清空消息历史"""
        try:
            self.redis_client.delete(f"messages:{session_id}")
            return True
        except Exception:
            return False
    
    def get_message_count(self, session_id: str) -> int:
        """获取消息计数"""
        try:
            return self.redis_client.llen(f"messages:{session_id}")
        except Exception:
            return 0
    
    def get_last_message(self, session_id: str) -> Optional[Message]:
        """获取最后一条消息"""
        try:
            messages = self.redis_client.lrange(f"messages:{session_id}", 0, 0)
            if messages:
                return Message.from_dict(json.loads(messages[0]))
            return None
        except Exception:
            return None
