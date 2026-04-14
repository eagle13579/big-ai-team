import hashlib
import json
import os
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from src.shared.config import settings
from src.shared.logging import logger

from .models import Memory


class VectorManager:
    """向量管理器 - 支持 OpenAI Embedding API + 本地回退"""

    EMBEDDING_DIM = 1536
    MAX_CACHE_SIZE = 10000

    def __init__(self, db: Session):
        self.db = db
        self._embedding_cache: dict[str, list[float]] = {}
        self._provider = self._detect_provider()
        self._api_key = self._get_api_key()

        if self._provider == "openai":
            logger.info("📐 VectorManager: 使用 OpenAI Embedding API")
        elif self._provider == "local":
            logger.info("📐 VectorManager: 使用本地 sentence-transformers 回退")
        else:
            logger.warning("📐 VectorManager: 无可用嵌入模型，使用随机向量（仅开发环境）")

    def _detect_provider(self) -> str:
        """检测可用的嵌入提供者"""
        api_key = os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
        if api_key:
            return "openai"

        try:
            import sentence_transformers
            return "local"
        except ImportError:
            pass

        return "mock"

    def _get_api_key(self) -> str:
        """获取 API Key"""
        return os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")

    def _cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def generate_embedding(self, text: str) -> list[float] | None:
        """生成文本嵌入向量"""
        if not text or not text.strip():
            return None

        cache_key = self._cache_key(text)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        embedding = None

        if self._provider == "openai":
            embedding = self._generate_openai_embedding(text)
        elif self._provider == "local":
            embedding = self._generate_local_embedding(text)

        if embedding is None:
            embedding = self._generate_mock_embedding(text)

        if embedding:
            if len(self._embedding_cache) >= self.MAX_CACHE_SIZE:
                oldest_key = next(iter(self._embedding_cache))
                del self._embedding_cache[oldest_key]
            self._embedding_cache[cache_key] = embedding

        return embedding

    def _generate_openai_embedding(self, text: str) -> list[float] | None:
        """使用 OpenAI Embedding API 生成向量"""
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "text-embedding-3-small",
                "input": text,
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                embedding = data["data"][0]["embedding"]

                logger.debug(f"📐 OpenAI Embedding 生成成功，维度: {len(embedding)}")
                return embedding

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ OpenAI Embedding API 返回错误: status={e.response.status_code}")
            return None
        except Exception as e:
            error_msg = str(e)
            if self._api_key and self._api_key in error_msg:
                error_msg = error_msg.replace(self._api_key, "***REDACTED***")
            logger.error(f"❌ OpenAI Embedding API 调用失败: {error_msg}")
            return None

    def _generate_local_embedding(self, text: str) -> list[float] | None:
        """使用本地 sentence-transformers 生成向量"""
        try:
            from sentence_transformers import SentenceTransformer

            if not hasattr(self, "_local_model"):
                self._local_model = SentenceTransformer("all-MiniLM-L6-v2")

            raw_embedding = self._local_model.encode(text, normalize_embeddings=True)
            embedding = raw_embedding.tolist()

            if len(embedding) < self.EMBEDDING_DIM:
                embedding = embedding + [0.0] * (self.EMBEDDING_DIM - len(embedding))
            elif len(embedding) > self.EMBEDDING_DIM:
                embedding = embedding[: self.EMBEDDING_DIM]

            logger.debug(f"📐 本地 Embedding 生成成功，原始维度: {len(raw_embedding)}, 对齐后: {len(embedding)}")
            return embedding

        except Exception as e:
            logger.error(f"❌ 本地 Embedding 生成失败: {e}")
            return None

    def _generate_mock_embedding(self, text: str) -> list[float] | None:
        """Mock 嵌入生成（开发环境回退）- 基于文本哈希的确定性向量"""
        try:
            text_hash = hashlib.sha256(text.encode("utf-8")).digest()
            seed = int.from_bytes(text_hash[:4], byteorder="big")
            rng = np.random.RandomState(seed)
            vector = rng.randn(self.EMBEDDING_DIM).astype(np.float32)
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            return vector.tolist()
        except Exception:
            return None

    def get_similar_memories(self, query_text: str, limit: int = 10) -> list[Memory]:
        """获取相似记忆"""
        query_embedding = self.generate_embedding(query_text)
        if not query_embedding:
            return []

        try:
            return (
                self.db.query(Memory)
                .filter(Memory.embedding.isnot(None))
                .order_by(Memory.embedding.cosine_distance(query_embedding))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []

    def update_embedding(self, memory_id: str, embedding: list[float] | None = None) -> bool:
        """更新记忆的嵌入向量"""
        memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory:
            return False

        if embedding is None:
            embedding = self.generate_embedding(memory.content)

        if embedding:
            memory.embedding = embedding
            self.db.commit()
            return True
        return False

    def batch_update_embeddings(self, memory_ids: list[str] | None = None) -> int:
        """批量更新嵌入向量"""
        query = self.db.query(Memory).filter(Memory.embedding.is_(None))

        if memory_ids:
            query = query.filter(Memory.id.in_(memory_ids))

        memories = query.all()
        updated_count = 0

        for memory in memories:
            embedding = self.generate_embedding(memory.content)
            if embedding:
                memory.embedding = embedding
                updated_count += 1

        if updated_count > 0:
            self.db.commit()

        logger.info(f"📐 批量嵌入更新完成: {updated_count}/{len(memories)}")
        return updated_count

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {
            "provider": self._provider,
            "cache_size": len(self._embedding_cache),
            "embedding_dim": self.EMBEDDING_DIM,
        }
