from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import Memory
from ..shared.schemas import MemoryCreate
from .mempalace_integration import MemPalaceIntegration, MemoryTier


class MemoryManager:
    """记忆管理器 - 世界顶尖AI记忆系统"""
    
    def __init__(self, db: Session, palace_path: str = "~/.mempalace/palace"):
        self.db = db
        self.mempalace = MemPalaceIntegration(palace_path)
    
    def create_memory(self, memory: MemoryCreate) -> Memory:
        """创建记忆"""
        db_memory = Memory(
            session_id=memory.session_id,
            user_id=memory.user_id,
            role_name=memory.role_name,
            content=memory.content,
            embedding=memory.embedding,
            memory_metadata=memory.metadata
        )
        self.db.add(db_memory)
        self.db.commit()
        self.db.refresh(db_memory)
        
        # 同时添加到mempalace
        context = {
            "session_id": memory.session_id,
            "user_id": memory.user_id,
            "role_name": memory.role_name,
            "metadata": memory.metadata
        }
        self.mempalace.add_memory(
            content=memory.content,
            context=context,
            tags=[memory.role_name] if memory.role_name else []
        )
        
        return db_memory
    
    def get_memories_by_session(self, session_id: str, limit: int = 100) -> List[Memory]:
        """根据会话ID获取记忆"""
        return self.db.query(Memory).filter(
            Memory.session_id == session_id
        ).order_by(Memory.created_at.desc()).limit(limit).all()
    
    def search_memories(self, query_embedding: List[float], limit: int = 10) -> List[Memory]:
        """向量搜索记忆"""
        # 使用pgvector的向量相似度搜索
        # 注意：这里需要根据实际的pgvector实现调整
        return self.db.query(Memory).filter(
            Memory.embedding.isnot(None)
        ).order_by(
            Memory.embedding.cosine_distance(query_embedding)
        ).limit(limit).all()
    
    def search_with_mempalace(self, query: str, limit: int = 5, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """使用mempalace搜索记忆（支持上下文感知）"""
        return self.mempalace.search(query, limit, context)
    
    def get_wake_up_context(self, context: Dict[str, Any] = None) -> str:
        """获取mempalace唤醒上下文（支持个性化）"""
        return self.mempalace.get_wake_up_context(context)
    
    def compress_content(self, content: str, memory_tier: MemoryTier = MemoryTier.SHORT_TERM) -> str:
        """使用AAAK压缩内容（支持自适应压缩）"""
        return self.mempalace.compress(content, memory_tier)
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        return self.mempalace.get_memory_summary()
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """根据ID获取记忆"""
        return self.db.query(Memory).filter(Memory.id == memory_id).first()
    
    def update_memory(self, memory_id: str, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[Memory]:
        """更新记忆"""
        memory = self.get_memory_by_id(memory_id)
        if memory:
            if content:
                memory.content = content
            if metadata:
                memory.memory_metadata = metadata
            self.db.commit()
            self.db.refresh(memory)
            
            # 同时更新mempalace中的记忆
            context = {
                "session_id": memory.session_id,
                "user_id": memory.user_id,
                "role_name": memory.role_name,
                "metadata": memory.memory_metadata
            }
            self.mempalace.update_memory(
                memory_id=str(memory.id),
                content=memory.content,
                context=context
            )
        return memory
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        memory = self.get_memory_by_id(memory_id)
        if memory:
            self.db.delete(memory)
            self.db.commit()
            
            # 同时从mempalace中删除记忆
            self.mempalace.delete_memory(str(memory_id))
            return True
        return False
    
    def add_memory_with_context(self, content: str, context: Dict[str, Any], tags: List[str] = None) -> Dict[str, Any]:
        """添加带情境的记忆"""
        return self.mempalace.add_memory(content, context, tags)
    
    def get_contextual_memory(self, context: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """获取与上下文相关的记忆"""
        return self.mempalace.get_contextual_memory(context, limit)
    
    def cleanup_memory(self):
        """清理过期记忆"""
        return self.mempalace.cleanup_memory()
    
    def get_memory_analytics(self) -> Dict[str, Any]:
        """获取记忆分析"""
        return self.mempalace.get_memory_analytics()

