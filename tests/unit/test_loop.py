import pytest
import asyncio
from src.workflow.loop import ExecutionLoop, MemoryManager, LLMClient
from src.execution.executor import ToolExecutor


class TestMemoryManager:
    """测试记忆管理器"""
    
    def test_memory_manager_creation(self):
        """测试记忆管理器创建"""
        memory_manager = MemoryManager()
        assert len(memory_manager.short_term_memory) == 0
        assert isinstance(memory_manager.long_term_memory, dict)
    
    def test_add_to_short_term_memory(self):
        """测试添加到短期记忆"""
        memory_manager = MemoryManager()
        memory_manager.add_to_short_term_memory({"test": "data"})
        assert len(memory_manager.short_term_memory) == 1
        assert memory_manager.short_term_memory[0]["test"] == "data"
    
    def test_add_to_long_term_memory(self):
        """测试添加到长期记忆"""
        memory_manager = MemoryManager()
        memory_manager.add_to_long_term_memory("test_key", "test_value")
        assert "test_key" in memory_manager.long_term_memory
        assert memory_manager.long_term_memory["test_key"] == "test_value"
    
    def test_get_short_term_memory(self):
        """测试获取短期记忆"""
        memory_manager = MemoryManager()
        for i in range(15):
            memory_manager.add_to_short_term_memory({"id": i})
        memory = memory_manager.get_short_term_memory(10)
        assert len(memory) == 10
        assert memory[0]["id"] == 5
    
    def test_get_long_term_memory(self):
        """测试获取长期记忆"""
        memory_manager = MemoryManager()
        memory_manager.add_to_long_term_memory("test_key", "test_value")
        assert memory_manager.get_long_term_memory("test_key") == "test_value"
        assert memory_manager.get_long_term_memory("non_existent") is None


class TestLLMClient:
    """测试 LLM 客户端"""
    
    @pytest.mark.asyncio
    async def test_generate(self):
        """测试生成文本"""
        llm_client = LLMClient()
        result = await llm_client.generate("Hello, world!")
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_generate_decision(self):
        """测试生成决策"""
        llm_client = LLMClient()
        decision = await llm_client.generate_decision("测试任务", "测试上下文")
        assert isinstance(decision, dict)
        assert "action" in decision
        assert decision["action"] in ["CALL_TOOL", "FINISH"]


class TestExecutionLoop:
    """测试执行循环"""
    
    @pytest.fixture
    def loop(self):
        """创建执行循环实例"""
        executor = ToolExecutor()
        return ExecutionLoop(executor)
    
    @pytest.mark.asyncio
    async def test_run_task(self, loop):
        """测试运行任务"""
        result = await loop.run("帮我调研 Ace 浏览器的 2026 年市场表现并生成一份 Markdown 报告")
        assert isinstance(result, dict)
        assert "status" in result
        assert "total_steps" in result
        assert "steps" in result
        assert isinstance(result["steps"], list)
    
    def test_get_history_summary(self, loop):
        """测试获取历史摘要"""
        summary = loop.get_history_summary()
        assert isinstance(summary, str)
    
    def test_clear_history(self, loop):
        """测试清除历史"""
        loop.clear_history()
        assert len(loop.history) == 0
    
    def test_get_memory_summary(self, loop):
        """测试获取记忆摘要"""
        summary = loop.get_memory_summary()
        assert isinstance(summary, dict)
        assert "short_term_memory_count" in summary
        assert "long_term_memory_keys" in summary
