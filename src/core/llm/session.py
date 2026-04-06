from typing import Dict, List, Optional, Any
from datetime import datetime
from .logger import logger
from . import LLMMessage


class Session:
    """LLM 会话类"""
    
    def __init__(self, session_id: str, model: str = "ace-nova-2026-pro"):
        """
        初始化会话
        
        Args:
            session_id: 会话 ID
            model: 模型名称
        """
        self.session_id = session_id
        self.model = model
        self.messages: List[LLMMessage] = []
        self.created_at = datetime.now()
        self.last_used_at = datetime.now()
        self.metadata: Dict[str, Any] = {}
    
    def add_message(self, message: LLMMessage):
        """添加消息到会话"""
        self.messages.append(message)
        self.last_used_at = datetime.now()
    
    def get_messages(self) -> List[LLMMessage]:
        """获取会话消息"""
        return self.messages
    
    def clear_messages(self):
        """清空会话消息"""
        self.messages.clear()
    
    def update_metadata(self, key: str, value: Any):
        """更新会话元数据"""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取会话元数据"""
        return self.metadata.get(key, default)


class SessionManager:
    """会话管理器"""
    
    def __init__(self, max_sessions: int = 1000, session_ttl: int = 3600):
        """
        初始化会话管理器
        
        Args:
            max_sessions: 最大会话数
            session_ttl: 会话超时时间（秒）
        """
        self.sessions: Dict[str, Session] = {}
        self.max_sessions = max_sessions
        self.session_ttl = session_ttl
    
    def create_session(self, session_id: str, model: str = "ace-nova-2026-pro") -> Session:
        """创建会话"""
        # 检查会话数是否超过限制
        if len(self.sessions) >= self.max_sessions:
            # 清理过期会话
            self._clean_expired_sessions()
            # 如果仍然超过限制，删除最早的会话
            if len(self.sessions) >= self.max_sessions:
                oldest_session_id = min(
                    self.sessions.keys(),
                    key=lambda k: self.sessions[k].created_at
                )
                del self.sessions[oldest_session_id]
                logger.info(f"Deleted oldest session: {oldest_session_id}")
        
        # 创建新会话
        session = Session(session_id, model)
        self.sessions[session_id] = session
        logger.info(f"Created session: {session_id} with model: {model}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        session = self.sessions.get(session_id)
        if session:
            # 检查会话是否过期
            if (datetime.now() - session.last_used_at).total_seconds() > self.session_ttl:
                del self.sessions[session_id]
                logger.info(f"Session expired: {session_id}")
                return None
            # 更新最后使用时间
            session.last_used_at = datetime.now()
        return session
    
    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    def _clean_expired_sessions(self):
        """清理过期会话"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if (current_time - session.last_used_at).total_seconds() > self.session_ttl:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned expired session: {session_id}")
    
    def get_all_sessions(self) -> List[Session]:
        """获取所有会话"""
        # 先清理过期会话
        self._clean_expired_sessions()
        return list(self.sessions.values())
    
    def get_session_count(self) -> int:
        """获取会话数量"""
        # 先清理过期会话
        self._clean_expired_sessions()
        return len(self.sessions)


# 全局会话管理器实例
session_manager = SessionManager()
