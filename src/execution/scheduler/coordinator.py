import asyncio
from typing import Any

from src.execution.scheduler.agent_pool import AgentPool, AgentInfo, AgentStatus
from src.execution.scheduler.task_distributor import TaskDistributor
from src.execution.scheduler.result_aggregator import ResultAggregator
from src.execution.scheduler.conflict_resolver import ConflictResolver
from src.shared.logging import logger


class AgentCoordinator:
    """Agent协调器 - 统一管理子Agent的调度、执行和结果聚合"""

    def __init__(self, max_agents: int = 20):
        self._pool = AgentPool(max_agents=max_agents)
        self._distributor = TaskDistributor(self._pool)
        self._aggregator = ResultAggregator()
        self._conflict_resolver = ConflictResolver()
        self._execution_log: list[dict[str, Any]] = []

    def register_agent(self, agent_id: str, role: str, capabilities: list[str] | None = None) -> bool:
        """注册Agent"""
        agent = AgentInfo(
            agent_id=agent_id,
            role=role,
            capabilities=capabilities or [],
        )
        return self._pool.register(agent)

    async def execute_tasks(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        """执行任务列表"""
        logger.info(f"🎯 开始协调执行 {len(tasks)} 个任务")

        assignments = self._distributor.distribute(tasks)

        assigned = [a for a in assignments if a.get("agent_id")]
        unassigned = [a for a in assignments if not a.get("agent_id")]

        execution_tasks = []
        for assignment in assigned:
            execution_tasks.append(self._execute_single_task(assignment, tasks))

        results = await asyncio.gather(*execution_tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "status": "error",
                    "error": str(result),
                    "agent_id": assigned[i].get("agent_id"),
                })
            else:
                processed_results.append(result)

        for assignment in assigned:
            agent_id = assignment.get("agent_id", "")
            success = any(
                r.get("status") == "success" and r.get("agent_id") == agent_id
                for r in processed_results
            )
            self._pool.record_task_completion(agent_id, success)

        aggregated = self._aggregator.aggregate(processed_results)

        if unassigned:
            aggregated["unassigned_tasks"] = len(unassigned)
            aggregated["unassigned_details"] = unassigned

        coordination_result = {
            "status": aggregated.get("status", "unknown"),
            "total_tasks": len(tasks),
            "assigned": len(assigned),
            "unassigned": len(unassigned),
            "results": aggregated,
        }

        self._execution_log.append(coordination_result)
        logger.info(f"🎯 协调执行完成: {len(assigned)}/{len(tasks)} 已分配")

        return coordination_result

    async def _execute_single_task(self, assignment: dict[str, Any], original_tasks: list[dict[str, Any]]) -> dict[str, Any]:
        """执行单个任务（模拟）"""
        task_id = assignment.get("task_id", "")
        agent_id = assignment.get("agent_id", "")

        task = next((t for t in original_tasks if t.get("id") == task_id), {})
        task_description = task.get("description", assignment.get("task_description", ""))

        await asyncio.sleep(0.1)

        return {
            "status": "success",
            "task_id": task_id,
            "agent_id": agent_id,
            "data": {"result": f"任务 '{task_description[:50]}' 已由 Agent {agent_id} 完成"},
            "confidence": 0.85,
        }

    def resolve_conflicts(self, conflicting_results: list[dict[str, Any]]) -> dict[str, Any]:
        """解决冲突"""
        return self._conflict_resolver.resolve(conflicting_results)

    def get_status(self) -> dict[str, Any]:
        """获取协调器状态"""
        return {
            "pool_stats": self._pool.get_pool_stats(),
            "execution_count": len(self._execution_log),
        }
