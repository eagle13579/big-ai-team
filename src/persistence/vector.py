
import numpy as np
from sqlalchemy.orm import Session

from .models import Memory


class VectorManager:
    """向量管理器"""

    def __init__(self, db: Session):
        self.db = db

    def generate_embedding(self, text: str) -> list[float] | None:
        """生成文本嵌入向量"""
        # 这里应该集成实际的嵌入模型，如OpenAI的API
        # 暂时返回随机向量作为示例
        try:
            # 模拟1536维向量
            return list(np.random.rand(1536).astype(float))
        except Exception:
            return None

    def get_similar_memories(self, query_text: str, limit: int = 10) -> list[Memory]:
        """获取相似记忆"""
        # 生成查询向量
        query_embedding = self.generate_embedding(query_text)
        if not query_embedding:
            return []

        # 使用向量搜索
        return (
            self.db.query(Memory)
            .filter(Memory.embedding.isnot(None))
            .order_by(Memory.embedding.cosine_distance(query_embedding))
            .limit(limit)
            .all()
        )

    def update_embedding(self, memory_id: str, embedding: list[float]) -> bool:
        """更新记忆的嵌入向量"""
        memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
        if memory:
            memory.embedding = embedding
            self.db.commit()
            return True
        return False

    def batch_update_embeddings(self, memory_ids: list[str]) -> int:
        """批量更新嵌入向量"""
        updated_count = 0
        for memory_id in memory_ids:
            memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
            if memory and not memory.embedding:
                embedding = self.generate_embedding(memory.content)
                if embedding:
                    memory.embedding = embedding
                    updated_count += 1
        if updated_count > 0:
            self.db.commit()
        return updated_count
