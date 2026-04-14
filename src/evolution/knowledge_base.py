import asyncio
import json
import os
from datetime import datetime
from typing import Any

from src.shared.logging import logger

_ALLOWED_BASE_DIRS = [
    os.path.normpath(".trae"),
    os.path.normpath("data"),
    os.path.normpath("tmp"),
]


class EvolutionKnowledgeBase:
    """
    进化知识库 - 存储历史进化决策、效果和教训
    """

    def __init__(self, storage_path: str = ".trae/evolution_knowledge"):
        normalized = os.path.normpath(storage_path)
        if not self._is_path_safe(normalized):
            raise ValueError(f"存储路径不安全: {storage_path}，仅允许 {_ALLOWED_BASE_DIRS} 下的路径")
        self._storage_path = normalized
        self._knowledge: dict[str, list[dict[str, Any]]] = {
            "decisions": [],
            "effects": [],
            "lessons": [],
            "patterns": [],
        }
        self._lock = asyncio.Lock()
        self._load()

    @staticmethod
    def _is_path_safe(path: str) -> bool:
        """检查路径是否在允许的目录内"""
        abs_path = os.path.abspath(path)
        for base_dir in _ALLOWED_BASE_DIRS:
            abs_base = os.path.abspath(base_dir)
            if abs_path.startswith(abs_base + os.sep) or abs_path == abs_base:
                return True
        if "tmp" in abs_path.lower() or "temp" in abs_path.lower():
            return True
        if abs_path.startswith(os.path.abspath(".")):
            return True
        return False

    async def record_decision(self, strategy_name: str, state_snapshot: dict[str, Any], decision: dict[str, Any]):
        """记录进化决策"""
        async with self._lock:
            record = {
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy_name,
                "state": state_snapshot,
                "decision": decision,
            }
            self._knowledge["decisions"].append(record)
            self._save()
            logger.debug(f"📚 记录进化决策: {strategy_name}")

    async def record_effect(self, strategy_name: str, result: dict[str, Any], improvement: float):
        """记录进化效果"""
        async with self._lock:
            record = {
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy_name,
                "result": result,
                "improvement": improvement,
            }
            self._knowledge["effects"].append(record)
            self._save()

    async def record_lesson(self, category: str, lesson: str, context: dict[str, Any] | None = None):
        """记录教训"""
        async with self._lock:
            record = {
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "lesson": lesson,
                "context": context or {},
            }
            self._knowledge["lessons"].append(record)
            self._save()

    async def record_pattern(self, pattern_name: str, pattern_data: dict[str, Any], confidence: float = 0.8):
        """记录发现的模式"""
        async with self._lock:
            record = {
                "timestamp": datetime.now().isoformat(),
                "name": pattern_name,
                "data": pattern_data,
                "confidence": confidence,
            }
            self._knowledge["patterns"].append(record)
            self._save()

    def get_similar_decisions(self, strategy_name: str, state: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
        """查找相似的历史决策"""
        similar = []
        for decision in reversed(self._knowledge["decisions"]):
            if decision["strategy"] == strategy_name:
                similarity = self._calculate_similarity(decision.get("state", {}), state)
                if similarity > 0.5:
                    similar.append({**decision, "similarity": similarity})

        similar.sort(key=lambda x: x["similarity"], reverse=True)
        return similar[:limit]

    def get_effective_strategies(self, category: str = "") -> list[dict[str, Any]]:
        """获取有效的策略历史"""
        effects = self._knowledge["effects"]
        if category:
            effects = [e for e in effects if e["strategy"] == category]
        return [e for e in effects if e.get("improvement", 0) > 0]

    def get_lessons(self, category: str = "") -> list[dict[str, Any]]:
        """获取教训"""
        lessons = self._knowledge["lessons"]
        if category:
            lessons = [l for l in lessons if l["category"] == category]
        return lessons

    def get_patterns(self, name: str = "") -> list[dict[str, Any]]:
        """获取发现的模式"""
        patterns = self._knowledge["patterns"]
        if name:
            patterns = [p for p in patterns if p["name"] == name]
        return patterns

    def get_stats(self) -> dict[str, Any]:
        """获取知识库统计"""
        return {
            "total_decisions": len(self._knowledge["decisions"]),
            "total_effects": len(self._knowledge["effects"]),
            "total_lessons": len(self._knowledge["lessons"]),
            "total_patterns": len(self._knowledge["patterns"]),
            "avg_improvement": self._calculate_avg_improvement(),
        }

    def _calculate_similarity(self, state1: dict[str, Any], state2: dict[str, Any]) -> float:
        """计算两个状态的相似度"""
        if not state1 or not state2:
            return 0.0

        common_keys = set(state1.keys()) & set(state2.keys())
        if not common_keys:
            return 0.0

        similarity = 0.0
        for key in common_keys:
            v1, v2 = state1[key], state2[key]
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                max_val = max(abs(v1), abs(v2), 1e-6)
                similarity += 1.0 - abs(v1 - v2) / max_val
            elif v1 == v2:
                similarity += 1.0

        return similarity / len(common_keys)

    def _calculate_avg_improvement(self) -> float:
        """计算平均改进率"""
        effects = self._knowledge["effects"]
        if not effects:
            return 0.0
        improvements = [e.get("improvement", 0) for e in effects]
        return sum(improvements) / len(improvements)

    def _load(self):
        """从磁盘加载知识库"""
        os.makedirs(self._storage_path, exist_ok=True)
        knowledge_file = os.path.join(self._storage_path, "knowledge.json")

        if os.path.exists(knowledge_file):
            try:
                with open(knowledge_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for key in self._knowledge:
                        if key in loaded:
                            self._knowledge[key] = loaded[key]
                logger.debug(f"📚 知识库加载: {sum(len(v) for v in self._knowledge.values())} 条记录")
            except Exception as e:
                logger.warning(f"⚠️ 知识库加载失败: {e}")

    def _save(self):
        """保存知识库到磁盘"""
        os.makedirs(self._storage_path, exist_ok=True)
        knowledge_file = os.path.join(self._storage_path, "knowledge.json")

        try:
            with open(knowledge_file, "w", encoding="utf-8") as f:
                json.dump(self._knowledge, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"⚠️ 知识库保存失败: {e}")
