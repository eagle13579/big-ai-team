from typing import Any

from src.execution.harness.assembler import AgentAssembler
from src.shared.logging import logger


class HarnessFeedbackLoop:
    """
    Harness 反馈循环 - 执行→观察→反思→调整 的完整闭环
    灵感来自 claw-code 的执行反馈机制
    """

    def __init__(self, assembler: AgentAssembler, llm_client=None, max_retries: int = 3):
        self._assembler = assembler
        self._llm_client = llm_client
        self._max_retries = max_retries
        self._execution_log: list[dict[str, Any]] = []

    async def run(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        运行反馈循环：装配→执行→检查→调整→重试
        """
        logger.info(f"🔄 启动 Harness 反馈循环，任务: {task}")

        plan = await self._assembler.assemble(task, context)

        for attempt in range(1, self._max_retries + 1):
            logger.info(f"🔄 第 {attempt}/{self._max_retries} 次尝试")

            result = await self._assembler.execute_assembly(plan)

            execution_record = {
                "task": task,
                "attempt": attempt,
                "plan": plan,
                "result": result,
            }
            self._execution_log.append(execution_record)

            if result.get("status") == "success":
                logger.info(f"✅ 任务在第 {attempt} 次尝试中成功完成")
                return {
                    "status": "success",
                    "task": task,
                    "attempts": attempt,
                    "result": result,
                    "plan": plan,
                }

            if attempt < self._max_retries:
                logger.info(f"⚠️ 第 {attempt} 次尝试未完全成功，尝试调整计划...")
                plan = await self._adjust_plan(task, plan, result, context)

        logger.error(f"❌ 任务在 {self._max_retries} 次尝试后仍未成功")
        return {
            "status": "failed",
            "task": task,
            "attempts": self._max_retries,
            "result": self._execution_log[-1].get("result") if self._execution_log else None,
            "plan": plan,
        }

    async def _adjust_plan(
        self,
        task: str,
        current_plan: dict[str, Any],
        execution_result: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        根据执行结果调整计划
        """
        failed_steps = [
            step for step in execution_result.get("steps", [])
            if step.get("status") != "success"
        ]

        if not failed_steps:
            return current_plan

        if self._llm_client is None:
            return self._keyword_adjust_plan(current_plan, failed_steps)

        try:
            adjust_prompt = (
                f"任务: {task}\n"
                f"当前计划: {current_plan}\n"
                f"执行结果: {execution_result}\n"
                f"失败的步骤: {failed_steps}\n\n"
                f"请根据失败原因调整执行计划。保持 JSON 格式不变。"
            )

            raw_response = await self._llm_client.generate(adjust_prompt, temperature=0.2)

            import json
            import re

            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if json_match:
                try:
                    adjusted_plan = json.loads(json_match.group())
                    if "steps" in adjusted_plan:
                        logger.info("🔄 LLM 调整计划成功")
                        return adjusted_plan
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            logger.warning(f"⚠️ LLM 调整计划失败: {e}")

        return self._keyword_adjust_plan(current_plan, failed_steps)

    def _keyword_adjust_plan(
        self,
        current_plan: dict[str, Any],
        failed_steps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """基于关键词的计划调整（回退方案）"""
        adjusted_steps = list(current_plan.get("steps", []))

        for failed in failed_steps:
            tool_name = failed.get("tool", "")
            error = failed.get("error", "")

            if "未注册" in str(error):
                adjusted_steps = [s for s in adjusted_steps if s.get("tool") != tool_name]
                logger.info(f"🔄 移除未注册工具: {tool_name}")

            elif "权限" in str(error):
                logger.info(f"🔄 跳过权限不足的工具: {tool_name}")
                adjusted_steps = [s for s in adjusted_steps if s.get("tool") != tool_name]

        if not adjusted_steps:
            adjusted_steps.append({
                "tool": "web_search",
                "args": {"query": current_plan.get("analysis", "")},
                "purpose": "默认搜索回退",
            })

        return {
            "analysis": current_plan.get("analysis", "") + " (已调整)",
            "steps": adjusted_steps,
            "expected_outcome": current_plan.get("expected_outcome", ""),
        }

    def get_execution_log(self) -> list[dict[str, Any]]:
        """获取执行日志"""
        return list(self._execution_log)

    def clear_log(self):
        """清除执行日志"""
        self._execution_log.clear()
