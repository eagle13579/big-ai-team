from typing import Any

from src.execution.scheduler.agent_pool import AgentPool, AgentInfo
from src.shared.logging import logger


class TaskDistributor:
    """任务分配器 - 考虑依赖关系+优先级+Agent能力匹配"""

    def __init__(self, agent_pool: AgentPool):
        self._pool = agent_pool

    def distribute(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """分配任务到Agent"""
        sorted_tasks = self._sort_by_priority_and_dependencies(tasks)
        assignments = []

        for task in sorted_tasks:
            agent = self._find_agent_for_task(task)

            if agent:
                assignment = {
                    "task_id": task.get("id", ""),
                    "task_description": task.get("description", ""),
                    "agent_id": agent.agent_id,
                    "agent_role": agent.role,
                    "priority": task.get("priority", 0),
                    "dependencies": task.get("dependencies", []),
                }
                assignments.append(assignment)

                self._pool.update_status(agent.agent_id, "busy", task.get("id"))

                logger.info(
                    f"📋 分配任务: {task.get('description', '')[:30]}... -> Agent {agent.agent_id} ({agent.role})"
                )
            else:
                assignments.append({
                    "task_id": task.get("id", ""),
                    "task_description": task.get("description", ""),
                    "agent_id": None,
                    "agent_role": None,
                    "priority": task.get("priority", 0),
                    "error": "无可用Agent",
                })
                logger.warning(f"⚠️ 任务 {task.get('id', '')} 无可用Agent")

        return assignments

    def _sort_by_priority_and_dependencies(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """按优先级和依赖关系排序任务"""
        task_map = {t.get("id", str(i)): t for i, t in enumerate(tasks)}
        completed: set[str] = set()
        sorted_tasks = []

        remaining = list(task_map.keys())
        max_iterations = len(remaining) * 2
        iteration = 0

        while remaining and iteration < max_iterations:
            iteration += 1
            ready = []

            for task_id in remaining:
                task = task_map[task_id]
                deps = task.get("dependencies", [])

                if all(dep in completed for dep in deps):
                    ready.append(task_id)

            if not ready:
                for task_id in remaining:
                    sorted_tasks.append(task_map[task_id])
                break

            ready_tasks = [task_map[tid] for tid in ready]
            ready_tasks.sort(key=lambda t: t.get("priority", 0), reverse=True)

            for task in ready_tasks:
                sorted_tasks.append(task)
                completed.add(task.get("id", ""))
                remaining.remove(task.get("id", ""))

        return sorted_tasks

    def _find_agent_for_task(self, task: dict[str, Any]) -> AgentInfo | None:
        """为任务查找最佳Agent"""
        required_role = task.get("required_role")
        required_capabilities = task.get("required_capabilities", [])

        return self._pool.find_best_for_task(required_role or "", required_capabilities)
