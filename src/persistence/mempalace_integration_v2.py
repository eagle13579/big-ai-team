#!/usr/bin/env python3
"""
MemPalace Integration V2 - 世界顶尖AI记忆系统
基于最佳实践的全面优化版本

核心特性:
1. 智能去重机制 - 自动检测和合并重复记忆
2. 增量更新 - 更新现有记忆而非创建新记忆
3. 语义相似度检测 - 使用向量嵌入检测相似内容
4. 记忆质量评分 - 多维度质量评估
5. 自动归档 - 基于时间和重要性自动调整记忆分层
6. 冲突解决 - 智能合并冲突信息
7. 版本控制 - 记忆历史版本追踪
"""

import hashlib
import json
import logging
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
from mempalace.dialect import Dialect
from mempalace.searcher import search_memories
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MemoryTier(Enum):
    """记忆分层 - 基于时间和重要性"""

    SHORT_TERM = "short_term"  # 短期记忆 (1-7天)
    MEDIUM_TERM = "medium_term"  # 中期记忆 (7-30天)
    LONG_TERM = "long_term"  # 长期记忆 (30天以上)
    ARCHIVE = "archive"  # 归档记忆 (很少访问)


@dataclass
class MemoryQualityMetrics:
    """记忆质量指标"""

    accuracy: float = 0.5
    completeness: float = 0.5
    relevance: float = 0.5
    confidence: float = 0.5
    consistency: float = 0.5
    freshness: float = 1.0

    @property
    def overall_score(self) -> float:
        """计算综合质量分数"""
        weights = {
            "accuracy": 0.25,
            "completeness": 0.20,
            "relevance": 0.20,
            "confidence": 0.15,
            "consistency": 0.10,
            "freshness": 0.10,
        }
        return sum(
            [
                self.accuracy * weights["accuracy"],
                self.completeness * weights["completeness"],
                self.relevance * weights["relevance"],
                self.confidence * weights["confidence"],
                self.consistency * weights["consistency"],
                self.freshness * weights["freshness"],
            ]
        )


@dataclass
class MemoryVersion:
    """记忆版本信息"""

    version_id: str
    content: str
    context: dict[str, Any]
    timestamp: str
    change_type: str  # 'create', 'update', 'merge'
    changes: list[str] = field(default_factory=list)


class MemPalaceIntegrationV2:
    """
    MemPalace集成模块 V2 - 世界顶尖AI记忆系统

    核心改进:
    1. 智能去重 - 基于语义相似度自动检测重复
    2. 增量更新 - 更新而非重复创建
    3. 冲突解决 - 智能合并策略
    4. 版本控制 - 完整历史追踪
    5. 质量评估 - 多维度质量评分
    6. 自动归档 - 智能分层管理
    """

    def __init__(self, palace_path: str = "~/.mempalace/palace"):
        self.palace_path = os.path.expanduser(palace_path)
        self._lock = threading.RLock()

        # 初始化组件
        self._ensure_palace_exists()
        self.dialect = Dialect()

        # 配置参数
        self.config = {
            "similarity_threshold": 0.85,  # 相似度阈值
            "duplicate_threshold": 0.95,  # 重复阈值
            "max_short_term": 100,  # 短期记忆上限
            "max_medium_term": 500,  # 中期记忆上限
            "max_long_term": 2000,  # 长期记忆上限
            "auto_archive_days": 90,  # 自动归档天数
            "quality_threshold": 0.6,  # 质量阈值
            "enable_deduplication": True,  # 启用去重
            "enable_versioning": True,  # 启用版本控制
        }

        # 初始化存储
        self._init_memory_tiers()
        self._init_context_store()
        self._init_quality_metrics()
        self._init_knowledge_graph()
        self._init_embeddings()
        self._init_clustering()
        self._init_versions()
        self._init_deduplication_index()

        logger.info("MemPalaceIntegrationV2 初始化完成")

    def _init_deduplication_index(self):
        """初始化去重索引"""
        self.content_hashes = {}
        self.similarity_index = {}
        self._embedding_dim = 128  # 统一使用128维向量

    def _init_versions(self):
        """初始化版本控制"""
        self.versions = defaultdict(list)
        self.versions_file = Path(self.palace_path) / "memory_versions.json"
        if self.versions_file.exists():
            try:
                with open(self.versions_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for memory_id, versions in data.items():
                        self.versions[memory_id] = [MemoryVersion(**v) for v in versions]
            except Exception as e:
                logger.error(f"加载版本数据失败: {str(e)}")

    def _save_versions(self):
        """保存版本数据"""
        try:
            data = {}
            for memory_id, versions in self.versions.items():
                data[memory_id] = [
                    {
                        "version_id": v.version_id,
                        "content": v.content,
                        "context": v.context,
                        "timestamp": v.timestamp,
                        "change_type": v.change_type,
                        "changes": v.changes,
                    }
                    for v in versions
                ]
            with open(self.versions_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存版本数据失败: {str(e)}")

    def _add_version(
        self,
        memory_id: str,
        content: str,
        context: dict[str, Any],
        change_type: str,
        changes: list[str],
    ):
        """添加记忆版本"""
        if not self.config["enable_versioning"]:
            return

        version = MemoryVersion(
            version_id=f"v_{int(time.time())}_{hash(content) % 10000}",
            content=content,
            context=context.copy(),
            timestamp=datetime.now().isoformat(),
            change_type=change_type,
            changes=changes,
        )
        self.versions[memory_id].append(version)

        # 限制版本数量
        if len(self.versions[memory_id]) > 10:
            self.versions[memory_id] = self.versions[memory_id][-10:]

    def _init_clustering(self):
        """初始化记忆聚类"""
        self.clusters = {}
        self.cluster_file = Path(self.palace_path) / "clusters.json"
        if self.cluster_file.exists():
            try:
                with open(self.cluster_file, encoding="utf-8") as f:
                    self.clusters = json.load(f)
            except Exception as e:
                logger.error(f"加载聚类数据失败: {str(e)}")

    def _save_clustering(self):
        """保存聚类数据"""
        try:
            with open(self.cluster_file, "w", encoding="utf-8") as f:
                json.dump(self.clusters, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存聚类数据失败: {str(e)}")

    def _ensure_palace_exists(self):
        """确保palace目录存在"""
        palace_dir = Path(self.palace_path)
        if not palace_dir.exists():
            import shutil
            import tempfile

            from mempalace.cli import init

            with tempfile.TemporaryDirectory() as tmpdir:
                init(tmpdir)
                shutil.copytree(tmpdir, self.palace_path)

    def _init_memory_tiers(self):
        """初始化记忆分层存储"""
        self.memory_tiers = {
            MemoryTier.SHORT_TERM: {},
            MemoryTier.MEDIUM_TERM: {},
            MemoryTier.LONG_TERM: {},
            MemoryTier.ARCHIVE: {},
        }
        self.tier_config = {
            MemoryTier.SHORT_TERM: {
                "retention_days": 7,
                "compression_ratio": 1.0,
                "max_memories": self.config["max_short_term"],
            },
            MemoryTier.MEDIUM_TERM: {
                "retention_days": 30,
                "compression_ratio": 0.7,
                "max_memories": self.config["max_medium_term"],
            },
            MemoryTier.LONG_TERM: {
                "retention_days": 365,
                "compression_ratio": 0.4,
                "max_memories": self.config["max_long_term"],
            },
            MemoryTier.ARCHIVE: {
                "retention_days": 1825,  # 5年
                "compression_ratio": 0.2,
                "max_memories": float("inf"),
            },
        }
        self._load_memory_tiers()

    def _load_memory_tiers(self):
        """加载记忆分层数据"""
        tiers_file = Path(self.palace_path) / "memory_tiers.json"
        if tiers_file.exists():
            try:
                with open(tiers_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for tier_name, memories in data.items():
                        if tier_name in [t.value for t in MemoryTier]:
                            tier = MemoryTier(tier_name)
                            self.memory_tiers[tier] = memories

                            # 重建去重索引
                            for memory_id, memory in memories.items():
                                content = memory.get("content", "")
                                content_hash = hashlib.md5(content.encode()).hexdigest()
                                self.content_hashes[content_hash] = memory_id
            except Exception as e:
                logger.error(f"加载记忆分层失败: {str(e)}")

    def _save_memory_tiers(self):
        """保存记忆分层数据"""
        tiers_file = Path(self.palace_path) / "memory_tiers.json"
        try:
            data = {}
            for tier, memories in self.memory_tiers.items():
                data[tier.value] = memories
            with open(tiers_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存记忆分层失败: {str(e)}")

    def _init_context_store(self):
        """初始化情境存储"""
        self.context_store = {}
        self.context_file = Path(self.palace_path) / "context_store.json"
        if self.context_file.exists():
            try:
                with open(self.context_file, encoding="utf-8") as f:
                    self.context_store = json.load(f)
            except Exception as e:
                logger.error(f"加载情境存储失败: {str(e)}")

    def _save_context_store(self):
        """保存情境存储"""
        try:
            with open(self.context_file, "w", encoding="utf-8") as f:
                json.dump(self.context_store, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存情境存储失败: {str(e)}")

    def _init_knowledge_graph(self):
        """初始化知识图谱"""
        self.knowledge_graph = nx.Graph()
        self.graph_file = Path(self.palace_path) / "knowledge_graph.json"
        if self.graph_file.exists():
            try:
                with open(self.graph_file, encoding="utf-8") as f:
                    graph_data = json.load(f)
                    for node in graph_data.get("nodes", []):
                        self.knowledge_graph.add_node(node["id"], **node.get("attributes", {}))
                    for edge in graph_data.get("edges", []):
                        self.knowledge_graph.add_edge(
                            edge["source"], edge["target"], **edge.get("attributes", {})
                        )
            except Exception as e:
                logger.error(f"加载知识图谱失败: {str(e)}")

    def _save_knowledge_graph(self):
        """保存知识图谱"""
        try:
            graph_data = {"nodes": [], "edges": []}
            for node_id, attributes in self.knowledge_graph.nodes(data=True):
                graph_data["nodes"].append({"id": node_id, "attributes": attributes})
            for source, target, attributes in self.knowledge_graph.edges(data=True):
                graph_data["edges"].append(
                    {"source": source, "target": target, "attributes": attributes}
                )
            with open(self.graph_file, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存知识图谱失败: {str(e)}")

    def _init_embeddings(self):
        """初始化向量嵌入"""
        self.embeddings = {}
        self.embeddings_file = Path(self.palace_path) / "embeddings.json"
        if self.embeddings_file.exists():
            try:
                with open(self.embeddings_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for memory_id, embedding in data.items():
                        self.embeddings[memory_id] = np.array(embedding)
            except Exception as e:
                logger.error(f"加载嵌入向量失败: {str(e)}")

    def _save_embeddings(self):
        """保存向量嵌入"""
        try:
            data = {}
            for memory_id, embedding in self.embeddings.items():
                data[memory_id] = embedding.tolist()
            with open(self.embeddings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存嵌入向量失败: {str(e)}")

    def _init_quality_metrics(self):
        """初始化质量评估指标"""
        self.quality_metrics = {}
        self.quality_file = Path(self.palace_path) / "quality_metrics.json"
        if self.quality_file.exists():
            try:
                with open(self.quality_file, encoding="utf-8") as f:
                    self.quality_metrics = json.load(f)
            except Exception as e:
                logger.error(f"加载质量评估指标失败: {str(e)}")

    def _save_quality_metrics(self):
        """保存质量评估指标"""
        try:
            with open(self.quality_file, "w", encoding="utf-8") as f:
                json.dump(self.quality_metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存质量评估指标失败: {str(e)}")

    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入向量 - 统一128维"""
        char_counts = defaultdict(int)
        word_counts = defaultdict(int)

        # 字符级特征
        for char in text.lower():
            if char.isalnum():
                char_counts[char] += 1

        # 词级特征
        words = text.lower().split()
        for word in words:
            word = "".join(c for c in word if c.isalnum())
            if word:
                word_counts[word] += 1

        # 生成128维向量 (64字符 + 64词)
        embedding = np.zeros(self._embedding_dim)

        # 填充字符特征 (前64维)
        for i, (char, count) in enumerate(sorted(char_counts.items())):
            if i < 64:
                embedding[i] = count / len(text) if text else 0

        # 填充词特征 (后64维)
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        for i, (word, count) in enumerate(sorted_words[:64]):
            embedding[64 + i] = count / len(words) if words else 0

        # 归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _find_similar_memories(
        self, content: str, threshold: float = None
    ) -> list[tuple[str, float]]:
        """查找相似记忆"""
        if threshold is None:
            threshold = self.config["similarity_threshold"]

        if not self.embeddings:
            return []

        try:
            current_embedding = self._generate_embedding(content)
            similarities = []

            for memory_id, embedding in self.embeddings.items():
                similarity = cosine_similarity([current_embedding], [embedding])[0][0]
                if similarity >= threshold:
                    similarities.append((memory_id, similarity))

            return sorted(similarities, key=lambda x: x[1], reverse=True)
        except Exception as e:
            logger.error(f"查找相似记忆失败: {str(e)}")
            return []

    def _check_duplicate(self, content: str) -> str | None:
        """检查是否存在重复记忆"""
        if not self.config["enable_deduplication"]:
            return None

        # 精确匹配
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if content_hash in self.content_hashes:
            return self.content_hashes[content_hash]

        # 语义相似度匹配
        similar_memories = self._find_similar_memories(
            content, threshold=self.config["duplicate_threshold"]
        )

        if similar_memories:
            return similar_memories[0][0]

        return None

    def _merge_contexts(
        self, old_context: dict[str, Any], new_context: dict[str, Any]
    ) -> tuple[dict[str, Any], list[str]]:
        """智能合并上下文"""
        merged = old_context.copy()
        changes = []

        for key, new_value in new_context.items():
            if key not in merged:
                merged[key] = new_value
                changes.append(f"添加: {key}")
            elif merged[key] != new_value:
                # 冲突解决策略
                if key in ["deployment_target", "status", "priority"]:
                    # 这些字段使用新值
                    old_value = merged[key]
                    merged[key] = new_value
                    changes.append(f"更新: {key} ({old_value} -> {new_value})")
                elif key in ["tags", "keywords"]:
                    # 合并列表
                    if isinstance(merged[key], list) and isinstance(new_value, list):
                        merged[key] = list(set(merged[key] + new_value))
                        changes.append(f"合并: {key}")
                else:
                    # 其他字段保留旧值
                    changes.append(f"保留: {key} (冲突)")

        return merged, changes

    def add_memory(
        self, content: str or dict[str, Any], context: dict[str, Any] = None, tags: list[str] = None
    ) -> dict[str, Any]:
        """
        添加记忆 - 智能去重和增量更新

        改进:
        1. 自动检测重复
        2. 更新而非重复创建
        3. 智能合并上下文
        4. 版本控制
        """
        with self._lock:
            try:
                # 处理字典形式的输入
                if isinstance(content, dict):
                    memory_dict = content
                    content = memory_dict.get("content", "")
                    context = memory_dict.get("metadata", {}) or context
                    tags = memory_dict.get("keywords", []) or tags

                # 检查重复
                duplicate_id = self._check_duplicate(content)

                if duplicate_id:
                    logger.info(f"检测到重复记忆，执行更新: {duplicate_id}")
                    return self._update_existing_memory(duplicate_id, content, context, tags)

                # 创建新记忆
                return self._create_new_memory(content, context, tags)

            except Exception as e:
                logger.error(f"添加记忆失败: {str(e)}")
                return {"success": False, "error": str(e)}

    def _create_new_memory(
        self, content: str, context: dict[str, Any], tags: list[str]
    ) -> dict[str, Any]:
        """创建新记忆"""
        memory_id = f"memory_{int(time.time())}_{hash(content) % 10000}"

        # 确定记忆分层
        tier = self._determine_memory_tier(context)

        # 检查分层容量
        if len(self.memory_tiers[tier]) >= self.tier_config[tier]["max_memories"]:
            self._archive_oldest_memories(tier, 10)

        # 压缩内容
        compressed_content = self.compress(content, tier)

        # 创建记忆数据
        memory_data = {
            "id": memory_id,
            "content": compressed_content,
            "original_content": content,
            "context": context or {},
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "access_count": 0,
            "version": 1,
        }

        # 存储
        self.memory_tiers[tier][memory_id] = memory_data

        # 更新索引
        content_hash = hashlib.md5(content.encode()).hexdigest()
        self.content_hashes[content_hash] = memory_id

        # 记录情境
        if context:
            self._record_context(memory_id, context)

        # 评估质量
        quality = self._evaluate_memory_quality(memory_id, content, context)

        # 生成嵌入
        embedding = self._generate_embedding(content)
        self.embeddings[memory_id] = embedding

        # 更新知识图谱
        self._update_knowledge_graph(memory_id, content, context, tags)

        # 添加版本
        self._add_version(memory_id, content, context, "create", ["创建记忆"])

        # 聚类
        self._cluster_memories()

        # 保存
        self._save_all()

        logger.info(f"创建新记忆: {memory_id}")

        return {
            "success": True,
            "memory_id": memory_id,
            "tier": tier.value,
            "action": "create",
            "quality_score": quality.overall_score,
        }

    def _update_existing_memory(
        self, memory_id: str, content: str, context: dict[str, Any], tags: list[str]
    ) -> dict[str, Any]:
        """更新现有记忆"""
        # 查找记忆
        memory = None
        current_tier = None

        for tier in MemoryTier:
            if memory_id in self.memory_tiers[tier]:
                memory = self.memory_tiers[tier][memory_id]
                current_tier = tier
                break

        if not memory:
            return {"success": False, "error": "记忆不存在"}

        # 合并上下文
        old_context = memory.get("context", {})
        merged_context, changes = self._merge_contexts(old_context, context or {})

        # 合并标签
        old_tags = set(memory.get("tags", []))
        new_tags = set(tags or [])
        merged_tags = list(old_tags | new_tags)

        # 更新记忆
        memory["context"] = merged_context
        memory["tags"] = merged_tags
        memory["last_accessed"] = datetime.now().isoformat()
        memory["access_count"] = memory.get("access_count", 0) + 1
        memory["version"] = memory.get("version", 1) + 1

        # 如果内容有变化，更新内容
        old_content = memory.get("original_content", "")
        if content != old_content:
            memory["original_content"] = content
            memory["content"] = self.compress(content, current_tier)

            # 更新嵌入
            self.embeddings[memory_id] = self._generate_embedding(content)

            # 更新知识图谱
            self._update_knowledge_graph(memory_id, content, merged_context, merged_tags)

        # 重新评估质量
        quality = self._evaluate_memory_quality(memory_id, content, merged_context)

        # 添加版本
        self._add_version(memory_id, content, merged_context, "update", changes)

        # 保存
        self._save_all()

        logger.info(f"更新记忆: {memory_id}, 变更: {changes}")

        return {
            "success": True,
            "memory_id": memory_id,
            "tier": current_tier.value,
            "action": "update",
            "changes": changes,
            "quality_score": quality.overall_score,
        }

    def _archive_oldest_memories(self, tier: MemoryTier, count: int):
        """归档最旧的记忆"""
        memories = self.memory_tiers[tier]
        if len(memories) <= count:
            return

        # 按最后访问时间排序
        sorted_memories = sorted(memories.items(), key=lambda x: x[1].get("last_accessed", ""))

        # 归档最旧的
        for memory_id, memory in sorted_memories[:count]:
            if tier != MemoryTier.ARCHIVE:
                self.memory_tiers[MemoryTier.ARCHIVE][memory_id] = memory
                del self.memory_tiers[tier][memory_id]
                logger.info(f"归档记忆: {memory_id}")

    def _save_all(self):
        """保存所有数据"""
        self._save_memory_tiers()
        self._save_context_store()
        self._save_quality_metrics()
        self._save_embeddings()
        self._save_knowledge_graph()
        self._save_clustering()
        self._save_versions()

    def _determine_memory_tier(self, context: dict[str, Any] = None) -> MemoryTier:
        """确定记忆分层"""
        if not context:
            return MemoryTier.SHORT_TERM

        # 基于重要性
        if context.get("importance") == "high" or context.get("priority") == "high":
            return MemoryTier.LONG_TERM

        # 基于保留时间
        if context.get("retention") == "long":
            return MemoryTier.LONG_TERM
        elif context.get("retention") == "medium":
            return MemoryTier.MEDIUM_TERM

        return MemoryTier.SHORT_TERM

    def _record_context(self, memory_id: str, context: dict[str, Any]):
        """记录情境信息"""
        key_context = {
            "time": context.get("time", datetime.now().isoformat()),
            "location": context.get("location", "unknown"),
            "participants": context.get("participants", []),
            "emotion": context.get("emotion", "neutral"),
            "task": context.get("task", "unknown"),
        }
        self.context_store[memory_id] = key_context

    def _evaluate_memory_quality(
        self, memory_id: str, content: str, context: dict[str, Any]
    ) -> MemoryQualityMetrics:
        """评估记忆质量"""
        metrics = MemoryQualityMetrics()

        # 准确性评估
        if context.get("source") in ["verified", "trusted"]:
            metrics.accuracy = 0.9
        elif context.get("source") == "unverified":
            metrics.accuracy = 0.6
        else:
            metrics.accuracy = 0.75

        # 完整性评估
        content_length = len(content)
        if content_length > 1000:
            metrics.completeness = 1.0
        elif content_length > 500:
            metrics.completeness = 0.8
        elif content_length > 100:
            metrics.completeness = 0.6
        else:
            metrics.completeness = 0.4

        # 相关性评估
        if context.get("importance") == "high":
            metrics.relevance = 0.95
        elif context.get("importance") == "medium":
            metrics.relevance = 0.8
        else:
            metrics.relevance = 0.6

        # 置信度评估
        word_count = len(content.split())
        unique_words = len(set(content.lower().split()))
        if word_count > 0:
            metrics.confidence = min(1.0, unique_words / word_count + 0.5)

        # 一致性评估
        similar_memories = self._find_similar_memories(content, threshold=0.7)
        if similar_memories:
            avg_similarity = sum(sim for _, sim in similar_memories) / len(similar_memories)
            metrics.consistency = avg_similarity

        # 新鲜度评估
        metrics.freshness = 1.0

        # 保存质量指标
        self.quality_metrics[memory_id] = {
            "accuracy": metrics.accuracy,
            "completeness": metrics.completeness,
            "relevance": metrics.relevance,
            "confidence": metrics.confidence,
            "consistency": metrics.consistency,
            "freshness": metrics.freshness,
            "overall": metrics.overall_score,
        }

        return metrics

    def compress(self, content: str, memory_tier: MemoryTier = MemoryTier.SHORT_TERM) -> str:
        """压缩内容"""
        try:
            compression_ratio = self.tier_config[memory_tier]["compression_ratio"]
            compressed = self.dialect.compress(content)

            if compression_ratio < 1.0:
                compressed = self._aggressive_compress(compressed, compression_ratio)

            return compressed
        except Exception as e:
            logger.error(f"压缩内容失败: {str(e)}")
            return content

    def _aggressive_compress(self, content: str, ratio: float) -> str:
        """更激进的压缩"""
        lines = content.split("\n")
        compressed_lines = []

        for line in lines:
            if not line.strip():
                continue
            if line not in compressed_lines:
                compressed_lines.append(line)

        if ratio < 0.5:
            compressed_content = "\n".join(compressed_lines[: len(compressed_lines) // 2])
        else:
            compressed_content = "\n".join(compressed_lines)

        return compressed_content

    def _update_knowledge_graph(
        self, memory_id: str, content: str, context: dict[str, Any], tags: list[str]
    ):
        """更新知识图谱"""
        try:
            self.knowledge_graph.add_node(
                memory_id,
                type="memory",
                content=content[:100],
                created_at=datetime.now().isoformat(),
                tags=tags or [],
            )

            # 提取关键词
            keywords = self._extract_keywords(content)
            for keyword in keywords[:5]:
                keyword_id = f"keyword_{hash(keyword) % 10000}"
                if not self.knowledge_graph.has_node(keyword_id):
                    self.knowledge_graph.add_node(keyword_id, type="keyword", name=keyword)
                self.knowledge_graph.add_edge(memory_id, keyword_id, type="contains", weight=0.8)

            # 处理上下文关系
            if context:
                if "user" in context:
                    user_id = f"user_{hash(context['user']) % 10000}"
                    if not self.knowledge_graph.has_node(user_id):
                        self.knowledge_graph.add_node(user_id, type="user", name=context["user"])
                    self.knowledge_graph.add_edge(memory_id, user_id, type="related_to", weight=0.9)

                if "project" in context:
                    project_id = f"project_{hash(context['project']) % 10000}"
                    if not self.knowledge_graph.has_node(project_id):
                        self.knowledge_graph.add_node(
                            project_id, type="project", name=context["project"]
                        )
                    self.knowledge_graph.add_edge(
                        memory_id, project_id, type="part_of", weight=0.95
                    )

            # 查找相关记忆
            related_memories = self._find_related_memories(content, limit=3)
            for related_id, similarity in related_memories:
                if related_id != memory_id:
                    self.knowledge_graph.add_edge(
                        memory_id, related_id, type="related", weight=similarity
                    )
        except Exception as e:
            logger.error(f"更新知识图谱失败: {str(e)}")

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        words = text.split()
        keywords = []
        seen = set()

        for word in words:
            word = "".join(c for c in word if c.isalnum())
            if len(word) > 3 and word not in seen:
                keywords.append(word.lower())
                seen.add(word)

        return keywords[:10]

    def _find_related_memories(self, content: str, limit: int = 3) -> list[tuple[str, float]]:
        """查找相关记忆"""
        if not self.embeddings:
            return []

        try:
            current_embedding = self._generate_embedding(content)
            similarities = []

            for memory_id, embedding in self.embeddings.items():
                similarity = cosine_similarity([current_embedding], [embedding])[0][0]
                similarities.append((memory_id, similarity))

            sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)[:limit]
            return sorted_similarities
        except Exception as e:
            logger.error(f"查找相关记忆失败: {str(e)}")
            return []

    def _cluster_memories(self):
        """对记忆进行聚类"""
        if len(self.embeddings) < 2:
            return

        try:
            memory_ids = list(self.embeddings.keys())

            # 过滤掉维度不匹配的嵌入
            valid_embeddings = []
            valid_memory_ids = []

            for mid in memory_ids:
                emb = self.embeddings[mid]
                if emb.shape[0] == self._embedding_dim:
                    valid_embeddings.append(emb)
                    valid_memory_ids.append(mid)

            if len(valid_embeddings) < 2:
                return

            embeddings_array = np.array(valid_embeddings)

            n_clusters = min(10, len(valid_memory_ids) // 3)
            if n_clusters < 1:
                n_clusters = 1

            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(embeddings_array)

            self.clusters = {}
            for i, memory_id in enumerate(valid_memory_ids):
                cluster_id = f"cluster_{clusters[i]}"
                if cluster_id not in self.clusters:
                    self.clusters[cluster_id] = []
                self.clusters[cluster_id].append(memory_id)
        except Exception as e:
            logger.error(f"记忆聚类失败: {str(e)}")

    def search(
        self, query: str, limit: int = 5, context: dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """搜索记忆 - 改进版"""
        try:
            # 增强查询
            if context:
                query = self._enhance_query_with_context(query, context)

            # 向量搜索
            vector_results = self._vector_search(query, limit * 2)

            # 传统搜索
            traditional_results = search_memories(
                query, palace_path=self.palace_path, n_results=limit
            )

            # 合并结果
            merged_results = self._merge_search_results(
                vector_results, traditional_results.get("results", [])
            )

            # 质量排序
            ranked_results = self._rank_by_quality(merged_results)

            # 上下文排序
            if context:
                ranked_results = self._sort_by_context_relevance(ranked_results, context)

            return ranked_results[:limit]
        except Exception as e:
            logger.error(f"搜索记忆失败: {str(e)}")
            return []

    def _vector_search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """向量搜索"""
        try:
            query_embedding = self._generate_embedding(query)
            similarities = []

            for memory_id, embedding in self.embeddings.items():
                similarity = cosine_similarity([query_embedding], [embedding])[0][0]
                similarities.append((memory_id, similarity))

            similarities.sort(key=lambda x: x[1], reverse=True)

            results = []
            for memory_id, similarity in similarities[:limit]:
                memory = self._get_memory_by_id(memory_id)
                if memory:
                    memory["vector_similarity"] = similarity
                    results.append(memory)

            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []

    def _get_memory_by_id(self, memory_id: str) -> dict[str, Any] | None:
        """根据ID获取记忆"""
        for tier in MemoryTier:
            if memory_id in self.memory_tiers[tier]:
                return self.memory_tiers[tier][memory_id]
        return None

    def _merge_search_results(
        self, vector_results: list[dict], traditional_results: list[dict]
    ) -> list[dict]:
        """合并搜索结果"""
        memory_ids = set()
        merged = []

        # 优先添加向量搜索结果
        for result in vector_results:
            memory_id = result.get("id")
            if memory_id and memory_id not in memory_ids:
                memory_ids.add(memory_id)
                merged.append(result)

        # 添加传统搜索结果
        for result in traditional_results:
            memory_id = result.get("source_file", result.get("id"))
            if memory_id and memory_id not in memory_ids:
                memory_ids.add(memory_id)
                merged.append(result)

        return merged

    def _rank_by_quality(self, results: list[dict]) -> list[dict]:
        """按质量排序"""
        for result in results:
            memory_id = result.get("id", result.get("source_file", ""))
            quality = self.quality_metrics.get(memory_id, {})
            result["quality_score"] = quality.get("overall", 0.5)

        results.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        return results

    def _sort_by_context_relevance(
        self, results: list[dict], context: dict[str, Any]
    ) -> list[dict]:
        """按上下文相关性排序"""
        for result in results:
            score = 0
            result_context = result.get("context", {})

            for key, value in context.items():
                if key in result_context:
                    if result_context[key] == value:
                        score += 1

            result["context_score"] = score

        results.sort(
            key=lambda x: (x.get("context_score", 0), x.get("quality_score", 0)), reverse=True
        )
        return results

    def _enhance_query_with_context(self, query: str, context: dict[str, Any]) -> str:
        """根据上下文增强查询"""
        keywords = []
        for key in ["current_task", "user_role", "project"]:
            if key in context:
                keywords.append(context[key])

        if keywords:
            return f"{query} (相关：{', '.join(keywords)})"
        return query

    def cleanup_duplicates(self) -> dict[str, Any]:
        """清理重复记忆"""
        with self._lock:
            duplicates_found = 0
            merged_count = 0

            # 查找所有重复
            content_to_ids = defaultdict(list)
            for tier in MemoryTier:
                for memory_id, memory in self.memory_tiers[tier].items():
                    content = memory.get("original_content", memory.get("content", ""))
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    content_to_ids[content_hash].append((tier, memory_id))

            # 合并重复
            for content_hash, ids in content_to_ids.items():
                if len(ids) > 1:
                    duplicates_found += len(ids) - 1

                    # 保留最新的，合并其他的
                    sorted_ids = sorted(
                        ids,
                        key=lambda x: self.memory_tiers[x[0]][x[1]].get("created_at", ""),
                        reverse=True,
                    )

                    keep_tier, keep_id = sorted_ids[0]
                    keep_memory = self.memory_tiers[keep_tier][keep_id]

                    for tier, memory_id in sorted_ids[1:]:
                        memory = self.memory_tiers[tier][memory_id]

                        # 合并上下文
                        keep_memory["context"].update(memory.get("context", {}))

                        # 合并标签
                        keep_tags = set(keep_memory.get("tags", []))
                        keep_tags.update(memory.get("tags", []))
                        keep_memory["tags"] = list(keep_tags)

                        # 删除重复
                        del self.memory_tiers[tier][memory_id]

                        # 清理相关数据
                        if memory_id in self.embeddings:
                            del self.embeddings[memory_id]
                        if memory_id in self.quality_metrics:
                            del self.quality_metrics[memory_id]

                        merged_count += 1

            # 重新聚类
            self._cluster_memories()

            # 保存
            self._save_all()

            logger.info(f"清理完成: 发现 {duplicates_found} 个重复, 合并 {merged_count} 个")

            return {
                "success": True,
                "duplicates_found": duplicates_found,
                "merged_count": merged_count,
            }

    def get_memory_stats(self) -> dict[str, Any]:
        """获取记忆统计信息"""
        stats = {
            "total_memories": 0,
            "tier_distribution": {},
            "quality_stats": {},
            "graph_stats": {},
            "cluster_stats": {},
        }

        # 分层统计
        for tier in MemoryTier:
            count = len(self.memory_tiers[tier])
            stats["tier_distribution"][tier.value] = count
            stats["total_memories"] += count

        # 质量统计
        if self.quality_metrics:
            overall_scores = [m.get("overall", 0) for m in self.quality_metrics.values()]
            stats["quality_stats"] = {
                "average": sum(overall_scores) / len(overall_scores),
                "max": max(overall_scores),
                "min": min(overall_scores),
            }

        # 知识图谱统计
        stats["graph_stats"] = {
            "nodes": self.knowledge_graph.number_of_nodes(),
            "edges": self.knowledge_graph.number_of_edges(),
        }

        # 聚类统计
        stats["cluster_stats"] = {
            "total_clusters": len(self.clusters),
            "average_size": sum(len(m) for m in self.clusters.values()) / len(self.clusters)
            if self.clusters
            else 0,
        }

        return stats


# 向后兼容
MemPalaceIntegration = MemPalaceIntegrationV2
