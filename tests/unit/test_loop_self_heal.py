import asyncio
import logging
import pytest
from typing import List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockRunResponse:
    def __init__(self, content: str):
        self.content = content


class MockAgent:
    def __init__(self) -> None:
        self.step = 0

    async def arun(self, prompt: str) -> MockRunResponse:
        self.step += 1
        # 模拟第一次执行会失败
        if self.step == 1:
            return MockRunResponse(
                content="I tried to divide 10 by 0, but it failed: Cannot divide by zero"
            )
        # 模拟第二次执行会成功
        return MockRunResponse(content="Final Answer: 5.0")


class AgenticLoop:
    def __init__(self, agent: MockAgent, max_steps: int = 5):
        self.agent = agent
        self.max_steps = max_steps
        self.history: List[MockRunResponse] = []

    async def run_until_complete(self, task: str) -> Optional[MockRunResponse]:
        step = 0
        current_prompt = task
        while step < self.max_steps:
            logger.info(f"--- [Step {step + 1}] Executing Loop ---")
            
            # 1. 执行 (Act & Observe)
            response = await self.agent.arun(current_prompt)
            self.history.append(response)

            # 2. 检查是否达成目标 (Reflect)
            if self._is_task_complete(response):
                logger.info("✅ Task completed successfully.")
                return response

            # 3. 错误自愈逻辑 (Self-Correction)
            logger.warning(f"⚠️ Step {step + 1} failed or incomplete. Reflecting...")
            current_prompt = self._generate_correction_prompt(response)
            step += 1

        logger.error("❌ Max steps reached. Breaking loop to prevent token drain.")
        return None

    def _is_task_complete(self, response: MockRunResponse) -> bool:
        return "Final Answer:" in response.content

    def _generate_correction_prompt(self, response: MockRunResponse) -> str:
        return "Previous attempt failed. Please adjust your strategy and try again."


@pytest.mark.asyncio
async def test_loop_self_heal() -> None:
    """Test the self-healing capability of AgenticLoop"""
    # 初始化模拟 Agent
    agent = MockAgent()
    # 初始化 AgenticLoop
    loop = AgenticLoop(agent=agent, max_steps=3)

    # 任务指令
    task = "请计算 10 除以 0，如果报错了，请解释原因并改为计算 10 除以 2。"
    logger.info("Starting test with task: %s", task)

    # 执行任务
    result = await loop.run_until_complete(task)

    if result:
        logger.info("Test completed successfully!")
        logger.info("Final response: %s", result.content)
    else:
        logger.error("Test failed: Max steps reached without completion")

    # 验证结果
    assert result is not None, "Task should complete successfully"
    assert "Final Answer:" in result.content, "Response should contain 'Final Answer:'"
    assert "5" in result.content, "Response should contain the correct result (5)"
    logger.info("Test passed!")


if __name__ == "__main__":
    asyncio.run(test_loop_self_heal())
