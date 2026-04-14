import asyncio
import json
import os
import tempfile

import pytest

from src.evolution.knowledge_base import EvolutionKnowledgeBase


@pytest.fixture
def kb(tmp_path):
    return EvolutionKnowledgeBase(storage_path=str(tmp_path / "evolution_knowledge"))


@pytest.fixture
def kb_with_data(kb):
    asyncio.run(kb.record_decision("test_strategy", {"cpu": 0.5}, {"action": "scale"}))
    asyncio.run(kb.record_effect("test_strategy", {"success": True}, 0.15))
    asyncio.run(kb.record_lesson("performance", "缓存命中率低", {"cache_hit_rate": 0.2}))
    asyncio.run(kb.record_pattern("high_load_pattern", {"threshold": 0.8}, 0.9))
    return kb


class TestEvolutionKnowledgeBase:

    def test_init_default_path(self):
        kb = EvolutionKnowledgeBase()
        assert kb._storage_path == os.path.normpath(".trae/evolution_knowledge")

    def test_init_path_traversal_rejected(self):
        with pytest.raises(ValueError, match="存储路径不安全"):
            EvolutionKnowledgeBase(storage_path="../../etc")

    def test_init_path_traversal_absolute(self):
        with pytest.raises(ValueError, match="存储路径不安全"):
            EvolutionKnowledgeBase(storage_path="/etc/passwd")

    def test_init_allowed_path(self, tmp_path):
        traedir = tmp_path / ".trae"
        kb = EvolutionKnowledgeBase(storage_path=str(traedir / "evolution_knowledge"))
        assert kb._storage_path == os.path.normpath(str(traedir / "evolution_knowledge"))

    @pytest.mark.asyncio
    async def test_record_decision(self, kb):
        await kb.record_decision("perf", {"cpu": 0.8}, {"action": "optimize"})
        assert len(kb._knowledge["decisions"]) == 1
        assert kb._knowledge["decisions"][0]["strategy"] == "perf"

    @pytest.mark.asyncio
    async def test_record_effect(self, kb):
        await kb.record_effect("perf", {"success": True}, 0.2)
        assert len(kb._knowledge["effects"]) == 1
        assert kb._knowledge["effects"][0]["improvement"] == 0.2

    @pytest.mark.asyncio
    async def test_record_lesson(self, kb):
        await kb.record_lesson("reliability", "频繁超时", {"timeout_count": 5})
        assert len(kb._knowledge["lessons"]) == 1
        assert kb._knowledge["lessons"][0]["category"] == "reliability"

    @pytest.mark.asyncio
    async def test_record_pattern(self, kb):
        await kb.record_pattern("spike_pattern", {"threshold": 0.9}, 0.85)
        assert len(kb._knowledge["patterns"]) == 1
        assert kb._knowledge["patterns"][0]["confidence"] == 0.85

    def test_get_similar_decisions(self, kb_with_data):
        similar = kb_with_data.get_similar_decisions("test_strategy", {"cpu": 0.5}, limit=5)
        assert len(similar) >= 1
        assert similar[0]["similarity"] > 0.5

    def test_get_similar_decisions_no_match(self, kb_with_data):
        similar = kb_with_data.get_similar_decisions("nonexistent", {"cpu": 0.5}, limit=5)
        assert len(similar) == 0

    def test_get_effective_strategies(self, kb_with_data):
        effective = kb_with_data.get_effective_strategies("test_strategy")
        assert len(effective) == 1
        assert effective[0]["improvement"] > 0

    def test_get_lessons(self, kb_with_data):
        lessons = kb_with_data.get_lessons("performance")
        assert len(lessons) == 1

    def test_get_patterns(self, kb_with_data):
        patterns = kb_with_data.get_patterns("high_load_pattern")
        assert len(patterns) == 1

    def test_get_stats(self, kb_with_data):
        stats = kb_with_data.get_stats()
        assert stats["total_decisions"] == 1
        assert stats["total_effects"] == 1
        assert stats["total_lessons"] == 1
        assert stats["total_patterns"] == 1
        assert stats["avg_improvement"] == 0.15

    def test_persistence(self, tmp_path):
        kb1 = EvolutionKnowledgeBase(storage_path=str(tmp_path / "kb"))
        asyncio.run(kb1.record_decision("test", {"cpu": 0.5}, {"action": "scale"}))

        kb2 = EvolutionKnowledgeBase(storage_path=str(tmp_path / "kb"))
        assert len(kb2._knowledge["decisions"]) == 1
        assert kb2._knowledge["decisions"][0]["strategy"] == "test"

    def test_calculate_similarity(self, kb):
        s1 = kb._calculate_similarity({"cpu": 0.5, "mem": 0.6}, {"cpu": 0.5, "mem": 0.6})
        assert s1 == 1.0

        s2 = kb._calculate_similarity({"cpu": 0.5}, {"cpu": 0.8})
        assert 0.0 < s2 < 1.0

        s3 = kb._calculate_similarity({}, {"cpu": 0.5})
        assert s3 == 0.0

        s4 = kb._calculate_similarity({"a": 1}, {"b": 2})
        assert s4 == 0.0
