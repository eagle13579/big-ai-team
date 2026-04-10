import json
import logging
import os
import time
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
    """记忆分层"""

    SHORT_TERM = "short_term"  # 短期记忆 (1-7天)
    MEDIUM_TERM = "medium_term"  # 中期记忆 (7-30天)
    LONG_TERM = "long_term"  # 长期记忆 (30天以上)


class MemPalaceIntegration:
    """MemPalace集成模块 - 世界顶尖AI记忆系统"""

    def __init__(self, palace_path: str = "~/.mempalace/palace"):
        self.palace_path = os.path.expanduser(palace_path)
        self._ensure_palace_exists()
        self.dialect = Dialect()
        self._init_memory_tiers()
        self._init_context_store()
        self._init_quality_metrics()
        self._init_knowledge_graph()
        self._init_embeddings()
        self._init_clustering()

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
            import tempfile

            from mempalace.cli import init

            # 创建临时目录来初始化
            with tempfile.TemporaryDirectory() as tmpdir:
                init(tmpdir)
                # 将初始化的内容复制到目标目录
                import shutil

                shutil.copytree(tmpdir, self.palace_path)

    def _init_memory_tiers(self):
        """初始化记忆分层存储"""
        self.memory_tiers = {
            MemoryTier.SHORT_TERM: {},
            MemoryTier.MEDIUM_TERM: {},
            MemoryTier.LONG_TERM: {},
        }
        self.tier_config = {
            MemoryTier.SHORT_TERM: {"retention_days": 7, "compression_ratio": 1.0},
            MemoryTier.MEDIUM_TERM: {"retention_days": 30, "compression_ratio": 0.5},
            MemoryTier.LONG_TERM: {"retention_days": 365, "compression_ratio": 0.2},
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
            except Exception as e:
                print(f"加载记忆分层失败: {str(e)}")

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
            print(f"保存记忆分层失败: {str(e)}")

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
                    # 重建知识图谱
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
            # 提取节点数据
            for node_id, attributes in self.knowledge_graph.nodes(data=True):
                graph_data["nodes"].append({"id": node_id, "attributes": attributes})
            # 提取边数据
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
                    # 加载嵌入向量
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
        self.quality_metrics = {
            "accuracy": {},  # 记忆准确性
            "completeness": {},  # 记忆完整性
            "relevance": {},  # 记忆相关性
            "confidence": {},  # 记忆置信度
        }
        self.quality_file = Path(self.palace_path) / "quality_metrics.json"
        if self.quality_file.exists():
            try:
                with open(self.quality_file, encoding="utf-8") as f:
                    self.quality_metrics = json.load(f)
            except Exception as e:
                print(f"加载质量评估指标失败: {str(e)}")

    def _save_quality_metrics(self):
        """保存质量评估指标"""
        try:
            with open(self.quality_file, "w", encoding="utf-8") as f:
                json.dump(self.quality_metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存质量评估指标失败: {str(e)}")

    def search(
        self, query: str, limit: int = 5, context: dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """搜索记忆（支持上下文感知和向量搜索）"""
        try:
            # 上下文感知搜索
            if context:
                # 根据上下文调整搜索策略
                query = self._enhance_query_with_context(query, context)

            # 执行传统搜索
            results = search_memories(query, palace_path=self.palace_path, n_results=limit)

            # 提取结果列表
            result_list = results.get("results", [])

            # 执行向量搜索（如果有嵌入向量）
            if self.embeddings:
                vector_results = self._vector_search(query, limit, context)
                # 合并结果
                result_list = self._merge_search_results(result_list, vector_results)

            # 对结果进行质量评估和排序
            results = self._rank_results_by_quality(result_list)

            # 按上下文相关性排序
            if context:
                results = self._sort_by_context_relevance(results, context)

            return results[:limit]
        except Exception as e:
            logger.error(f"搜索记忆失败: {str(e)}")
            return []

    def _vector_search(
        self, query: str, limit: int = 5, context: dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """向量搜索"""
        try:
            # 生成查询向量（简化版，实际应该使用真正的嵌入模型）
            query_embedding = self._generate_embedding(query)

            # 计算相似度
            similarities = {}
            for memory_id, embedding in self.embeddings.items():
                similarity = cosine_similarity([query_embedding], [embedding])[0][0]
                similarities[memory_id] = similarity

            # 排序并获取前N个结果
            sorted_memories = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:limit]

            # 构建结果列表
            results = []
            for memory_id, similarity in sorted_memories:
                # 从记忆分层中获取记忆信息
                memory = self._get_memory_by_id(memory_id)
                if memory:
                    memory["vector_similarity"] = similarity
                    results.append(memory)

            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            return []

    def _generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入向量"""
        # 简化版嵌入生成，实际应该使用OpenAI、Hugging Face等嵌入模型
        # 这里使用基于字符频率的简单嵌入
        char_counts = {}
        for char in text.lower():
            if char.isalnum():
                char_counts[char] = char_counts.get(char, 0) + 1

        # 生成固定长度的向量
        embedding = np.zeros(128)  # 128维向量
        for i, (char, count) in enumerate(char_counts.items()):
            if i < 128:
                embedding[i] = count / len(text)

        # 归一化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _get_memory_by_id(self, memory_id: str) -> dict[str, Any]:
        """根据ID获取记忆"""
        for _tier, memories in self.memory_tiers.items():
            if memory_id in memories:
                return memories[memory_id]
        return None

    def _merge_search_results(
        self, traditional_results: list[dict[str, Any]], vector_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """合并搜索结果"""
        # 使用集合去重
        memory_ids = set()
        merged_results = []

        # 首先添加向量搜索结果（优先级更高）
        for result in vector_results:
            memory_id = result.get("id")
            if memory_id not in memory_ids:
                memory_ids.add(memory_id)
                merged_results.append(result)

        # 然后添加传统搜索结果
        for result in traditional_results:
            memory_id = result.get("source_file", result.get("id"))
            if memory_id and memory_id not in memory_ids:
                memory_ids.add(memory_id)
                merged_results.append(result)

        return merged_results

    def _enhance_query_with_context(self, query: str, context: dict[str, Any]) -> str:
        """根据上下文增强查询"""
        # 提取上下文关键词
        context_keywords = []
        if "current_task" in context:
            context_keywords.append(context["current_task"])
        if "user_role" in context:
            context_keywords.append(context["user_role"])
        if "project" in context:
            context_keywords.append(context["project"])

        # 增强查询
        if context_keywords:
            enhanced_query = f"{query} (相关：{', '.join(context_keywords)})"
            return enhanced_query
        return query

    def _rank_results_by_quality(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """根据质量指标排序结果"""
        # 确保results是一个列表
        result_list = results if isinstance(results, list) else []

        # 计算每个结果的质量分数
        for result in result_list:
            # 使用id或source_file作为记忆ID
            memory_id = result.get("id", result.get("source_file", ""))
            quality_score = self._calculate_quality_score(memory_id)
            result["quality_score"] = quality_score

        # 按质量分数排序
        result_list.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        return result_list

    def _calculate_quality_score(self, memory_id: str) -> float:
        """计算记忆质量分数"""
        metrics = self.quality_metrics
        accuracy = metrics.get("accuracy", {}).get(memory_id, 0.5)
        completeness = metrics.get("completeness", {}).get(memory_id, 0.5)
        relevance = metrics.get("relevance", {}).get(memory_id, 0.5)
        confidence = metrics.get("confidence", {}).get(memory_id, 0.5)

        # 加权平均
        weights = {"accuracy": 0.3, "completeness": 0.25, "relevance": 0.25, "confidence": 0.2}
        score = (
            accuracy * weights["accuracy"]
            + completeness * weights["completeness"]
            + relevance * weights["relevance"]
            + confidence * weights["confidence"]
        )

        return score

    def compress(self, content: str, memory_tier: MemoryTier = MemoryTier.SHORT_TERM) -> str:
        """使用AAAK压缩内容（支持自适应压缩）"""
        try:
            # 根据记忆分层调整压缩率
            compression_ratio = self.tier_config[memory_tier]["compression_ratio"]

            # 基础压缩
            compressed = self.dialect.compress(content)

            # 根据压缩率进一步处理
            if compression_ratio < 1.0:
                # 更激进的压缩
                compressed = self._aggressive_compress(compressed, compression_ratio)

            return compressed
        except Exception as e:
            print(f"压缩内容失败: {str(e)}")
            return content

    def _aggressive_compress(self, content: str, ratio: float) -> str:
        """更激进的压缩"""
        # 移除冗余信息
        lines = content.split("\n")
        compressed_lines = []

        for line in lines:
            # 移除空行
            if not line.strip():
                continue
            # 移除重复内容
            if line not in compressed_lines:
                compressed_lines.append(line)

        # 根据压缩率截断内容
        if ratio < 0.5:
            # 保留核心信息
            compressed_content = "\n".join(compressed_lines[: len(compressed_lines) // 2])
        else:
            compressed_content = "\n".join(compressed_lines)

        return compressed_content

    def get_wake_up_context(self, context: dict[str, Any] = None) -> str:
        """获取唤醒上下文（支持个性化）"""
        try:
            from mempalace.layers import MemoryStack

            # 直接使用MemoryStack类
            stack = MemoryStack(palace_path=self.palace_path)

            # 根据上下文获取个性化唤醒内容
            if context:
                # 提取个性化关键词
                keywords = self._extract_personalization_keywords(context)
                # 生成个性化唤醒内容
                text = stack.wake_up()
                # 增强个性化内容
                text = self._personalize_wake_up_context(text, keywords)
            else:
                text = stack.wake_up()

            return text
        except Exception as e:
            print(f"获取唤醒上下文失败: {str(e)}")
            return ""

    def _extract_personalization_keywords(self, context: dict[str, Any]) -> list[str]:
        """提取个性化关键词"""
        keywords = []
        if "user_role" in context:
            keywords.append(context["user_role"])
        if "project" in context:
            keywords.append(context["project"])
        if "interests" in context:
            keywords.extend(context["interests"])
        return keywords

    def _personalize_wake_up_context(self, text: str, keywords: list[str]) -> str:
        """个性化唤醒上下文"""
        # 添加个性化部分
        if keywords:
            personalized_section = f"\n## 个性化推荐\n基于您的兴趣：{', '.join(keywords)}"
            text += personalized_section
        return text

    def get_memory_summary(self) -> dict[str, Any]:
        """获取记忆摘要"""
        try:
            import io
            import sys

            from mempalace.miner import status

            # 捕获标准输出
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                status(palace_path=self.palace_path)
                output = sys.stdout.getvalue()
            finally:
                sys.stdout = old_stdout

            # 解析输出
            lines = output.strip().split("\n")
            summary = {}

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    summary[key.strip()] = value.strip()

            # 添加记忆分层信息
            tier_summary = {}
            for tier, memories in self.memory_tiers.items():
                tier_summary[tier.value] = len(memories)
            summary["memory_tiers"] = tier_summary

            # 添加质量评估信息
            quality_summary = {}
            for metric, values in self.quality_metrics.items():
                if values:
                    avg_value = sum(values.values()) / len(values)
                    quality_summary[metric] = round(avg_value, 2)
            summary["quality_metrics"] = quality_summary

            return summary
        except Exception as e:
            print(f"获取记忆摘要失败: {str(e)}")
            return {}

    def add_memory(
        self, content: str or dict[str, Any], context: dict[str, Any] = None, tags: list[str] = None
    ) -> dict[str, Any]:
        """添加记忆（支持情境化、知识图谱和向量嵌入）"""
        try:
            # 处理字典形式的输入
            if isinstance(content, dict):
                memory_dict = content
                content = memory_dict.get("content", "")
                context = memory_dict.get("metadata", {}) or context
                tags = memory_dict.get("keywords", []) or tags

            # 生成记忆ID
            memory_id = f"memory_{int(time.time())}_{hash(content) % 10000}"

            # 确定记忆分层
            tier = self._determine_memory_tier(context)

            # 压缩内容
            compressed_content = self.compress(content, tier)

            # 记录情境信息
            memory_data = {
                "id": memory_id,
                "content": compressed_content,
                "original_content": content,
                "context": context or {},
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "access_count": 0,
                "quality_score": 0.8,  # 初始质量分数
            }

            # 存储到对应分层
            self.memory_tiers[tier][memory_id] = memory_data

            # 记录情境
            if context:
                self._record_context(memory_id, context)

            # 评估记忆质量
            self._evaluate_memory_quality(memory_id, content, context)

            # 生成向量嵌入
            embedding = self._generate_embedding(content)
            self.embeddings[memory_id] = embedding

            # 更新知识图谱
            self._update_knowledge_graph(memory_id, content, context, tags)

            # 执行记忆聚类
            self._cluster_memories()

            # 保存数据
            self._save_memory_tiers()
            self._save_context_store()
            self._save_quality_metrics()
            self._save_embeddings()
            self._save_knowledge_graph()
            self._save_clustering()

            return {"success": True, "memory_id": memory_id, "tier": tier.value}
        except Exception as e:
            logger.error(f"添加记忆失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _update_knowledge_graph(
        self, memory_id: str, content: str, context: dict[str, Any], tags: list[str]
    ):
        """更新知识图谱"""
        try:
            # 添加记忆节点
            self.knowledge_graph.add_node(
                memory_id,
                type="memory",
                content=content[:100],  # 存储内容摘要
                created_at=datetime.now().isoformat(),
                tags=tags or [],
            )

            # 提取关键词作为节点
            keywords = self._extract_keywords(content)
            for keyword in keywords[:5]:  # 取前5个关键词
                keyword_id = f"keyword_{hash(keyword) % 10000}"
                # 添加关键词节点
                if not self.knowledge_graph.has_node(keyword_id):
                    self.knowledge_graph.add_node(keyword_id, type="keyword", name=keyword)
                # 添加记忆与关键词的边
                self.knowledge_graph.add_edge(memory_id, keyword_id, type="contains", weight=0.8)

            # 处理上下文关系
            if context:
                # 添加上下文节点
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

            # 查找相关记忆并建立连接
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
        # 简化版关键词提取，实际应该使用NLP库
        # 这里简单地提取长度大于3的单词
        words = text.split()
        keywords = []
        seen = set()

        for word in words:
            # 去除标点符号
            word = "".join(c for c in word if c.isalnum())
            if len(word) > 3 and word not in seen:
                keywords.append(word.lower())
                seen.add(word)

        return keywords[:10]  # 取前10个关键词

    def _find_related_memories(self, content: str, limit: int = 3) -> list[tuple[str, float]]:
        """查找相关记忆"""
        if not self.embeddings:
            return []

        try:
            # 生成当前内容的嵌入
            current_embedding = self._generate_embedding(content)

            # 计算与所有记忆的相似度
            similarities = {}
            for memory_id, embedding in self.embeddings.items():
                similarity = cosine_similarity([current_embedding], [embedding])[0][0]
                similarities[memory_id] = similarity

            # 排序并返回前N个
            sorted_similarities = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[
                :limit
            ]
            return sorted_similarities
        except Exception as e:
            logger.error(f"查找相关记忆失败: {str(e)}")
            return []

    def _cluster_memories(self):
        """对记忆进行聚类"""
        if len(self.embeddings) < 2:
            return

        try:
            # 准备嵌入向量
            memory_ids = list(self.embeddings.keys())
            embeddings = np.array([self.embeddings[mid] for mid in memory_ids])

            # 使用K-means聚类
            n_clusters = min(5, len(memory_ids) // 2)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(embeddings)

            # 更新聚类结果
            self.clusters = {}
            for i, memory_id in enumerate(memory_ids):
                cluster_id = f"cluster_{clusters[i]}"
                if cluster_id not in self.clusters:
                    self.clusters[cluster_id] = []
                self.clusters[cluster_id].append(memory_id)
        except Exception as e:
            logger.error(f"记忆聚类失败: {str(e)}")

    def _determine_memory_tier(self, context: dict[str, Any] = None) -> MemoryTier:
        """确定记忆分层"""
        if not context:
            return MemoryTier.SHORT_TERM

        # 根据上下文确定分层
        if "priority" in context:
            priority = context["priority"]
            if priority == "high":
                return MemoryTier.LONG_TERM
            elif priority == "medium":
                return MemoryTier.MEDIUM_TERM

        if "retention" in context:
            retention = context["retention"]
            if retention == "long":
                return MemoryTier.LONG_TERM
            elif retention == "medium":
                return MemoryTier.MEDIUM_TERM

        return MemoryTier.SHORT_TERM

    def _record_context(self, memory_id: str, context: dict[str, Any]):
        """记录情境信息"""
        # 提取关键情境信息
        key_context = {
            "time": context.get("time", datetime.now().isoformat()),
            "location": context.get("location", "unknown"),
            "participants": context.get("participants", []),
            "emotion": context.get("emotion", "neutral"),
            "task": context.get("task", "unknown"),
        }

        self.context_store[memory_id] = key_context

    def _evaluate_memory_quality(self, memory_id: str, content: str, context: dict[str, Any]):
        """智能评估记忆质量"""
        # 基础质量评估
        accuracy = 0.85  # 基础准确性
        completeness = min(1.0, len(content) / 500)  # 基于内容长度，更严格的标准
        relevance = 0.8  # 基础相关性
        confidence = 0.75  # 基础置信度

        # 根据内容特征调整
        # 内容长度评估
        if len(content) > 1000:
            completeness = min(1.0, completeness + 0.1)
        elif len(content) < 50:
            completeness = max(0.3, completeness - 0.2)

        # 内容复杂度评估
        words = content.split()
        unique_words = len(set(words))
        if unique_words > 50:
            completeness = min(1.0, completeness + 0.1)
            accuracy = min(1.0, accuracy + 0.05)

        # 根据上下文调整
        if context:
            # 来源可信度
            if "source" in context:
                source = context["source"]
                if source == "verified":
                    accuracy = 0.95
                    confidence = 0.95
                elif source == "trusted":
                    accuracy = 0.9
                    confidence = 0.9
                elif source == "unverified":
                    accuracy = 0.7
                    confidence = 0.6

            # 详细程度
            if "details" in context:
                if context["details"] == "complete":
                    completeness = 1.0
                elif context["details"] == "partial":
                    completeness = 0.7
                elif context["details"] == "minimal":
                    completeness = 0.4

            # 重要性
            if "importance" in context:
                importance = context["importance"]
                if importance == "high":
                    relevance = 0.95
                    confidence = min(1.0, confidence + 0.1)
                elif importance == "medium":
                    relevance = 0.85
                elif importance == "low":
                    relevance = 0.6

            # 时效性
            if "timestamp" in context:
                try:
                    memory_time = datetime.fromisoformat(context["timestamp"])
                    time_diff = (datetime.now() - memory_time).days
                    if time_diff < 7:
                        relevance = min(1.0, relevance + 0.1)
                    elif time_diff > 365:
                        relevance = max(0.5, relevance - 0.2)
                except:
                    pass

        # 基于访问历史调整
        memory = self._get_memory_by_id(memory_id)
        if memory:
            access_count = memory.get("access_count", 0)
            if access_count > 5:
                # 频繁访问的记忆质量可能更高
                relevance = min(1.0, relevance + 0.1)
                confidence = min(1.0, confidence + 0.05)

            # 基于最后访问时间调整
            last_accessed = memory.get("last_accessed")
            if last_accessed:
                try:
                    last_access_time = datetime.fromisoformat(last_accessed)
                    days_since_access = (datetime.now() - last_access_time).days
                    if days_since_access < 7:
                        relevance = min(1.0, relevance + 0.05)
                except:
                    pass

        # 存储质量评估
        self.quality_metrics["accuracy"][memory_id] = accuracy
        self.quality_metrics["completeness"][memory_id] = completeness
        self.quality_metrics["relevance"][memory_id] = relevance
        self.quality_metrics["confidence"][memory_id] = confidence

        # 计算综合质量分数
        quality_score = self._calculate_quality_score(memory_id)
        if memory:
            memory["quality_score"] = quality_score

    def assess_memory_quality(self, memory_id: str) -> dict[str, float]:
        """评估记忆质量并返回质量指标"""
        try:
            metrics = self.quality_metrics
            accuracy = metrics.get("accuracy", {}).get(memory_id, 0.5)
            completeness = metrics.get("completeness", {}).get(memory_id, 0.5)
            relevance = metrics.get("relevance", {}).get(memory_id, 0.5)
            confidence = metrics.get("confidence", {}).get(memory_id, 0.5)

            # 计算综合质量分数
            quality_score = (
                accuracy * 0.3 + completeness * 0.25 + relevance * 0.25 + confidence * 0.2
            )

            return {
                "accuracy": accuracy,
                "completeness": completeness,
                "relevance": relevance,
                "confidence": confidence,
                "overall": quality_score,
            }
        except Exception as e:
            logger.error(f"评估记忆质量失败: {str(e)}")
            return {
                "accuracy": 0.5,
                "completeness": 0.5,
                "relevance": 0.5,
                "confidence": 0.5,
                "overall": 0.5,
            }

    def update_memory(
        self, memory_id: str, content: str = None, context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """更新记忆（支持知识图谱和向量嵌入更新）"""
        try:
            # 查找记忆
            found = False
            for tier, memories in self.memory_tiers.items():
                if memory_id in memories:
                    memory = memories[memory_id]

                    # 更新内容
                    if content:
                        # 重新压缩
                        compressed_content = self.compress(content, tier)
                        memory["content"] = compressed_content
                        memory["original_content"] = content

                        # 更新向量嵌入
                        embedding = self._generate_embedding(content)
                        self.embeddings[memory_id] = embedding

                        # 更新知识图谱
                        tags = memory.get("tags", [])
                        self._update_knowledge_graph(memory_id, content, memory["context"], tags)

                    # 更新情境
                    if context:
                        memory["context"].update(context)
                        self._record_context(memory_id, context)

                        # 更新知识图谱
                        tags = memory.get("tags", [])
                        content = memory.get("original_content", "")
                        self._update_knowledge_graph(memory_id, content, memory["context"], tags)

                    # 更新访问信息
                    memory["last_accessed"] = datetime.now().isoformat()
                    memory["access_count"] += 1

                    # 重新评估质量
                    self._evaluate_memory_quality(
                        memory_id, memory["original_content"], memory["context"]
                    )

                    # 检查是否需要调整分层
                    new_tier = self._reassess_memory_tier(memory)
                    if new_tier != tier:
                        # 移动到新分层
                        del self.memory_tiers[tier][memory_id]
                        self.memory_tiers[new_tier][memory_id] = memory

                    found = True
                    break

            if not found:
                return {"success": False, "error": "Memory not found"}

            # 重新聚类
            self._cluster_memories()

            # 保存数据
            self._save_memory_tiers()
            self._save_context_store()
            self._save_quality_metrics()
            self._save_embeddings()
            self._save_knowledge_graph()
            self._save_clustering()

            return {"success": True, "memory_id": memory_id}
        except Exception as e:
            logger.error(f"更新记忆失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_related_memories(self, memory_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """获取相关记忆"""
        try:
            # 从知识图谱中获取相关记忆
            related_memories = []

            # 检查记忆是否存在
            memory = self._get_memory_by_id(memory_id)
            if not memory:
                return []

            # 从知识图谱获取相关节点
            if memory_id in self.knowledge_graph:
                # 获取直接相连的节点
                neighbors = list(self.knowledge_graph.neighbors(memory_id))

                # 过滤出记忆节点
                memory_neighbors = []
                for neighbor_id in neighbors:
                    if neighbor_id.startswith("memory_"):
                        neighbor_memory = self._get_memory_by_id(neighbor_id)
                        if neighbor_memory:
                            # 获取边的权重
                            weight = self.knowledge_graph[memory_id][neighbor_id].get("weight", 0.5)
                            neighbor_memory["relevance_score"] = weight
                            memory_neighbors.append(neighbor_memory)

                # 按相关性排序
                memory_neighbors.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
                related_memories = memory_neighbors[:limit]

            # 如果知识图谱中没有足够的相关记忆，使用向量搜索
            if len(related_memories) < limit and self.embeddings.get(memory_id):
                # 向量搜索相关记忆
                content = memory.get("original_content", "")
                vector_related = self._find_related_memories(content, limit=limit)

                # 转换为记忆对象
                for related_id, similarity in vector_related:
                    if related_id != memory_id and not any(
                        m.get("id") == related_id for m in related_memories
                    ):
                        related_memory = self._get_memory_by_id(related_id)
                        if related_memory:
                            related_memory["relevance_score"] = similarity
                            related_memories.append(related_memory)

                # 重新排序并限制数量
                related_memories.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
                related_memories = related_memories[:limit]

            return related_memories
        except Exception as e:
            logger.error(f"获取相关记忆失败: {str(e)}")
            return []

    def get_memory_recommendations(
        self, context: dict[str, Any], limit: int = 5
    ) -> list[dict[str, Any]]:
        """智能记忆推荐"""
        try:
            # 提取上下文关键词
            keywords = self._extract_context_keywords(context)
            if not keywords:
                return []

            # 构建查询
            query = " ".join(keywords)

            # 搜索相关记忆
            search_results = self.search(query, limit * 2, context)

            # 基于知识图谱进行推荐
            recommended_memories = []
            memory_ids = set()

            # 首先添加搜索结果
            for result in search_results:
                memory_id = result.get("id")
                if memory_id and memory_id not in memory_ids:
                    memory_ids.add(memory_id)
                    recommended_memories.append(result)

            # 基于聚类进行推荐
            if self.clusters:
                # 找到与当前上下文最相关的聚类
                cluster_scores = {}
                for cluster_id, cluster_memories in self.clusters.items():
                    score = 0
                    for memory_id in cluster_memories[:3]:  # 每个聚类取前3个记忆计算分数
                        memory = self._get_memory_by_id(memory_id)
                        if memory:
                            relevance = self._calculate_context_relevance(memory, context)
                            score += relevance
                    if score > 0:
                        cluster_scores[cluster_id] = score / min(3, len(cluster_memories))

                # 按分数排序聚类
                sorted_clusters = sorted(cluster_scores.items(), key=lambda x: x[1], reverse=True)

                # 从高分数聚类中添加推荐
                for cluster_id, score in sorted_clusters:
                    if len(recommended_memories) >= limit:
                        break
                    for memory_id in self.clusters[cluster_id]:
                        if len(recommended_memories) >= limit:
                            break
                        if memory_id not in memory_ids:
                            memory = self._get_memory_by_id(memory_id)
                            if memory:
                                memory["cluster_score"] = score
                                recommended_memories.append(memory)
                                memory_ids.add(memory_id)

            # 按综合分数排序
            def get_score(memory):
                return (
                    memory.get("quality_score", 0) * 0.4
                    + memory.get("context_relevance", 0) * 0.3
                    + memory.get("vector_similarity", 0) * 0.2
                    + memory.get("cluster_score", 0) * 0.1
                )

            recommended_memories.sort(key=get_score, reverse=True)
            return recommended_memories[:limit]
        except Exception as e:
            logger.error(f"获取记忆推荐失败: {str(e)}")
            return []

    def get_knowledge_graph_stats(self) -> dict[str, Any]:
        """获取知识图谱统计信息"""
        try:
            stats = {
                "nodes": self.knowledge_graph.number_of_nodes(),
                "edges": self.knowledge_graph.number_of_edges(),
                "memory_nodes": len(
                    [n for n in self.knowledge_graph.nodes() if n.startswith("memory_")]
                ),
                "keyword_nodes": len(
                    [n for n in self.knowledge_graph.nodes() if n.startswith("keyword_")]
                ),
                "user_nodes": len(
                    [n for n in self.knowledge_graph.nodes() if n.startswith("user_")]
                ),
                "project_nodes": len(
                    [n for n in self.knowledge_graph.nodes() if n.startswith("project_")]
                ),
                "average_degree": sum(d for n, d in self.knowledge_graph.degree())
                / self.knowledge_graph.number_of_nodes()
                if self.knowledge_graph.number_of_nodes() > 0
                else 0,
            }
            return stats
        except Exception as e:
            logger.error(f"获取知识图谱统计失败: {str(e)}")
            return {}

    def get_clustering_stats(self) -> dict[str, Any]:
        """获取聚类统计信息"""
        try:
            stats = {
                "total_clusters": len(self.clusters),
                "cluster_sizes": {k: len(v) for k, v in self.clusters.items()},
                "average_cluster_size": sum(len(v) for v in self.clusters.values())
                / len(self.clusters)
                if self.clusters
                else 0,
            }
            return stats
        except Exception as e:
            logger.error(f"获取聚类统计失败: {str(e)}")
            return {}

    def _reassess_memory_tier(self, memory: dict[str, Any]) -> MemoryTier:
        """重新评估记忆分层"""
        # 根据访问频率和时间调整分层
        access_count = memory.get("access_count", 0)
        created_at = datetime.fromisoformat(memory.get("created_at"))
        days_since_creation = (datetime.now() - created_at).days

        # 高频访问的记忆提升分层
        if access_count > 10:
            if days_since_creation > 30:
                return MemoryTier.LONG_TERM
            elif days_since_creation > 7:
                return MemoryTier.MEDIUM_TERM

        # 长期未访问的记忆降低分层
        last_accessed = datetime.fromisoformat(memory.get("last_accessed"))
        days_since_access = (datetime.now() - last_accessed).days

        if days_since_access > 30:
            return MemoryTier.LONG_TERM
        elif days_since_access > 7:
            return MemoryTier.MEDIUM_TERM

        return MemoryTier.SHORT_TERM

    def delete_memory(self, memory_id: str) -> dict[str, Any]:
        """删除记忆（包括知识图谱、向量嵌入和聚类）"""
        try:
            # 查找并删除记忆
            found = False
            for tier, memories in self.memory_tiers.items():
                if memory_id in memories:
                    del self.memory_tiers[tier][memory_id]
                    found = True
                    break

            if not found:
                return {"success": False, "error": "Memory not found"}

            # 删除相关情境
            if memory_id in self.context_store:
                del self.context_store[memory_id]

            # 删除相关质量评估
            for metric in self.quality_metrics.values():
                if memory_id in metric:
                    del metric[memory_id]

            # 删除向量嵌入
            if memory_id in self.embeddings:
                del self.embeddings[memory_id]

            # 从知识图谱中删除节点及其边
            if memory_id in self.knowledge_graph:
                # 获取与该记忆相关的所有边
                edges = list(self.knowledge_graph.edges(memory_id))
                # 删除所有边
                for edge in edges:
                    self.knowledge_graph.remove_edge(*edge)
                # 删除节点
                self.knowledge_graph.remove_node(memory_id)

            # 从聚类中删除
            for cluster_id, cluster_memories in list(self.clusters.items()):
                if memory_id in cluster_memories:
                    cluster_memories.remove(memory_id)
                    # 如果聚类为空，删除聚类
                    if not cluster_memories:
                        del self.clusters[cluster_id]

            # 重新聚类
            self._cluster_memories()

            # 保存数据
            self._save_memory_tiers()
            self._save_context_store()
            self._save_quality_metrics()
            self._save_embeddings()
            self._save_knowledge_graph()
            self._save_clustering()

            return {"success": True, "memory_id": memory_id}
        except Exception as e:
            logger.error(f"删除记忆失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def cleanup_memory(self):
        """清理过期记忆（包括知识图谱、向量嵌入和聚类）"""
        try:
            now = datetime.now()
            deleted_count = 0
            deleted_memory_ids = []

            for tier, memories in self.memory_tiers.items():
                retention_days = self.tier_config[tier]["retention_days"]
                expired_memories = []

                for memory_id, memory in memories.items():
                    created_at = datetime.fromisoformat(memory.get("created_at"))
                    days_since_creation = (now - created_at).days

                    if days_since_creation > retention_days:
                        expired_memories.append(memory_id)

                # 删除过期记忆
                for memory_id in expired_memories:
                    del memories[memory_id]
                    deleted_memory_ids.append(memory_id)
                    deleted_count += 1

            # 清理相关数据
            for memory_id in deleted_memory_ids:
                # 删除相关情境
                if memory_id in self.context_store:
                    del self.context_store[memory_id]

                # 删除相关质量评估
                for metric in self.quality_metrics.values():
                    if memory_id in metric:
                        del metric[memory_id]

                # 删除向量嵌入
                if memory_id in self.embeddings:
                    del self.embeddings[memory_id]

                # 从知识图谱中删除节点及其边
                if memory_id in self.knowledge_graph:
                    # 获取与该记忆相关的所有边
                    edges = list(self.knowledge_graph.edges(memory_id))
                    # 删除所有边
                    for edge in edges:
                        self.knowledge_graph.remove_edge(*edge)
                    # 删除节点
                    self.knowledge_graph.remove_node(memory_id)

                # 从聚类中删除
                for cluster_id, cluster_memories in list(self.clusters.items()):
                    if memory_id in cluster_memories:
                        cluster_memories.remove(memory_id)
                        # 如果聚类为空，删除聚类
                        if not cluster_memories:
                            del self.clusters[cluster_id]

            # 重新聚类
            self._cluster_memories()

            # 保存数据
            self._save_memory_tiers()
            self._save_context_store()
            self._save_quality_metrics()
            self._save_embeddings()
            self._save_knowledge_graph()
            self._save_clustering()

            return {"success": True, "deleted_count": deleted_count}
        except Exception as e:
            logger.error(f"清理记忆失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_contextual_memory(
        self, context: dict[str, Any], limit: int = 5
    ) -> list[dict[str, Any]]:
        """获取与上下文相关的记忆（使用向量搜索和知识图谱）"""
        try:
            # 提取上下文关键词
            keywords = self._extract_context_keywords(context)

            # 构建查询
            query = " ".join(keywords)

            # 搜索记忆（使用向量搜索和传统搜索）
            search_results = self.search(query, limit * 2, context)

            # 使用智能推荐
            recommended_results = self.get_memory_recommendations(context, limit * 2)

            # 合并结果
            combined_results = []
            memory_ids = set()

            # 首先添加推荐结果
            for result in recommended_results:
                memory_id = result.get("id")
                if memory_id and memory_id not in memory_ids:
                    memory_ids.add(memory_id)
                    combined_results.append(result)

            # 然后添加搜索结果
            for result in search_results:
                memory_id = result.get("id")
                if memory_id and memory_id not in memory_ids:
                    memory_ids.add(memory_id)
                    combined_results.append(result)

            # 按上下文相关性排序
            combined_results = self._sort_by_context_relevance(combined_results, context)

            # 限制结果数量
            return combined_results[:limit]
        except Exception as e:
            logger.error(f"获取上下文相关记忆失败: {str(e)}")
            return []

    def _extract_context_keywords(self, context: dict[str, Any]) -> list[str]:
        """提取上下文关键词"""
        keywords = []

        # 从上下文提取关键词
        if "task" in context:
            keywords.append(context["task"])
        if "project" in context:
            keywords.append(context["project"])
        if "user" in context:
            keywords.append(context["user"])
        if "topic" in context:
            keywords.append(context["topic"])
        if "location" in context:
            keywords.append(context["location"])

        return keywords

    def _sort_by_context_relevance(
        self, results: list[dict[str, Any]], context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """按上下文相关性排序"""
        for result in results:
            # 计算与上下文的相关性分数
            relevance_score = self._calculate_context_relevance(result, context)
            result["context_relevance"] = relevance_score

        # 按相关性分数排序
        results.sort(key=lambda x: x.get("context_relevance", 0), reverse=True)
        return results

    def _calculate_context_relevance(
        self, result: dict[str, Any], context: dict[str, Any]
    ) -> float:
        """计算与上下文的相关性分数"""
        score = 0.0

        # 检查关键词匹配
        result_content = result.get("content", "")
        for _key, value in context.items():
            if isinstance(value, str) and value in result_content:
                score += 0.2
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item in result_content:
                        score += 0.1

        # 检查时间相关性
        if "time" in context:
            try:
                context_time = datetime.fromisoformat(context["time"])
                result_time = datetime.fromisoformat(
                    result.get("created_at", datetime.now().isoformat())
                )
                time_diff = abs((context_time - result_time).days)
                if time_diff < 7:
                    score += 0.3
                elif time_diff < 30:
                    score += 0.1
            except:
                pass

        # 检查地点相关性
        if "location" in context and "location" in result.get("context", {}):
            if context["location"] == result["context"]["location"]:
                score += 0.2

        return min(1.0, score)

    def get_memory_analytics(self) -> dict[str, Any]:
        """获取记忆分析（包含知识图谱和聚类统计）"""
        try:
            # 计算记忆统计
            total_memories = sum(len(memories) for memories in self.memory_tiers.values())
            tier_distribution = {}
            for tier, memories in self.memory_tiers.items():
                tier_distribution[tier.value] = len(memories)

            # 计算质量统计
            quality_stats = {}
            for metric, values in self.quality_metrics.items():
                if values:
                    avg_value = sum(values.values()) / len(values)
                    quality_stats[metric] = round(avg_value, 2)

            # 计算访问统计
            total_accesses = 0
            for memories in self.memory_tiers.values():
                for memory in memories.values():
                    total_accesses += memory.get("access_count", 0)

            # 计算时间统计
            now = datetime.now()
            age_stats = {}
            for tier, memories in self.memory_tiers.items():
                if memories:
                    ages = []
                    for memory in memories.values():
                        created_at = datetime.fromisoformat(memory.get("created_at"))
                        age = (now - created_at).days
                        ages.append(age)
                    avg_age = sum(ages) / len(ages)
                    age_stats[tier.value] = round(avg_age, 1)

            # 获取知识图谱统计
            graph_stats = self.get_knowledge_graph_stats()

            # 获取聚类统计
            cluster_stats = self.get_clustering_stats()

            # 获取向量嵌入统计
            embedding_stats = {
                "total_embeddings": len(self.embeddings),
                "embedding_dimension": 128,  # 当前使用的嵌入维度
            }

            analytics = {
                "total_memories": total_memories,
                "tier_distribution": tier_distribution,
                "quality_stats": quality_stats,
                "total_accesses": total_accesses,
                "age_stats": age_stats,
                "knowledge_graph": graph_stats,
                "clustering": cluster_stats,
                "embeddings": embedding_stats,
                "last_updated": now.isoformat(),
            }

            return analytics
        except Exception as e:
            logger.error(f"获取记忆分析失败: {str(e)}")
            return {}
