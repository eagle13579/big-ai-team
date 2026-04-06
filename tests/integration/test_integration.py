import pytest
import asyncio
from src.workflow.loop import ExecutionLoop
from src.execution.executor import ToolExecutor


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def execution_loop(self):
        """创建执行循环实例"""
        executor = ToolExecutor()
        return ExecutionLoop(executor)
    
    async def test_full_workflow(self, execution_loop):
        """测试完整工作流"""
        # 测试任务：调研 Ace 浏览器的市场表现并生成报告
        task = "帮我调研 Ace 浏览器的 2026 年市场表现并生成一份 Markdown 报告"
        result = await execution_loop.run(task)
        
        # 验证结果
        assert isinstance(result, dict)
        assert result["status"] == "SUCCESS"
        assert "final_answer" in result
        assert "total_steps" in result
        assert result["total_steps"] > 0
        assert "steps" in result
        assert len(result["steps"]) > 0
        
        # 验证步骤内容
        for step in result["steps"]:
            assert "step" in step
            assert "thought" in step
            assert "tool" in step
            assert "status" in step
            assert "observation" in step
    
    async def test_error_handling(self, execution_loop):
        """测试错误处理"""
        # 测试任务：计算 10 除以 0
        task = "请计算 10 除以 0"
        result = await execution_loop.run(task)
        
        # 验证结果
        assert isinstance(result, dict)
        assert "status" in result
        assert "total_steps" in result
        assert "steps" in result
        
        # 验证是否有错误处理
        has_error = any(step["status"] == "失败" for step in result["steps"])
        assert has_error
    
    async def test_memory_integration(self, execution_loop):
        """测试记忆集成"""
        # 测试任务 1
        task1 = "帮我调研 Ace 浏览器的 2026 年市场表现"
        result1 = await execution_loop.run(task1)
        
        # 测试任务 2，应该利用之前的记忆
        task2 = "基于之前的调研，生成一份 Markdown 报告"
        result2 = await execution_loop.run(task2)
        
        # 验证结果
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert result1["status"] == "SUCCESS"
        assert result2["status"] == "SUCCESS"
        assert "final_answer" in result2
