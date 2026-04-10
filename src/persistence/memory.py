from typing import Any, Optional

from sqlalchemy.orm import Session

from ..shared.schemas import MemoryCreate
from .models import Memory


class MemoryManager:
    """记忆管理器"""

    def __init__(self, db: Session):
        self.db = db

    def create_memory(self, memory: MemoryCreate) -> Memory:
        """创建记忆"""
        db_memory = Memory(
            session_id=memory.session_id,
            user_id=memory.user_id,
            role_name=memory.role_name,
            content=memory.content,
            embedding=memory.embedding,
            metadata=memory.metadata,
        )
        self.db.add(db_memory)
        self.db.commit()
        self.db.refresh(db_memory)
        return db_memory

    def get_memories_by_session(self, session_id: str, limit: int = 100) -> list[Memory]:
        """根据会话ID获取记忆"""
        return (
            self.db.query(Memory)
            .filter(Memory.session_id == session_id)
            .order_by(Memory.created_at.desc())
            .limit(limit)
            .all()
        )

    def search_memories(self, query_embedding: list[float], limit: int = 10) -> list[Memory]:
        """向量搜索记忆"""
        # 使用pgvector的向量相似度搜索
        # 注意：这里需要根据实际的pgvector实现调整
        return (
            self.db.query(Memory)
            .filter(Memory.embedding.isnot(None))
            .order_by(Memory.embedding.cosine_distance(query_embedding))
            .limit(limit)
            .all()
        )

    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """根据ID获取记忆"""
        return self.db.query(Memory).filter(Memory.id == memory_id).first()

    def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[Memory]:
        """更新记忆"""
        memory = self.get_memory_by_id(memory_id)
        if memory:
            if content:
                memory.content = content
            if metadata:
                memory.metadata = metadata
            self.db.commit()
            self.db.refresh(memory)
        return memory

    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        memory = self.get_memory_by_id(memory_id)
        if memory:
            self.db.delete(memory)
            self.db.commit()
            return True
        return False
