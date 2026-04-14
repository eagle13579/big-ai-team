import json
import re
from typing import Any

from src.persistence.models import TaskStatus
from src.shared.logging import logger
from src.shared.utils import generate_uuid


class Planner:
    """规划编排器 - 增强版：支持LLM驱动动态分解 + DAG依赖图 + 并行调度 + 动态重规划"""

    def __init__(self, llm_client=None):
        self._llm_client = llm_client

    def create_plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """创建任务计划"""
        plan_id = generate_uuid()
        tasks = self._decompose_task(intent)
        dag = self._build_dag(tasks)

        return {
            "plan_id": plan_id,
            "tasks": tasks,
            "dag": dag,
            "parallel_groups": self._identify_parallel_groups(dag),
            "created_at": intent.get("timestamp", None),
        }

    async def create_plan_async(self, intent: dict[str, Any]) -> dict[str, Any]:
        """异步创建任务计划（支持LLM驱动分解）"""
        plan_id = generate_uuid()

        if self._llm_client is not None:
            tasks = await self._decompose_with_llm(intent)
        else:
            tasks = self._decompose_task(intent)

        dag = self._build_dag(tasks)

        return {
            "plan_id": plan_id,
            "tasks": tasks,
            "dag": dag,
            "parallel_groups": self._identify_parallel_groups(dag),
            "created_at": intent.get("timestamp", None),
        }

    async def replan(self, original_plan: dict[str, Any], failed_task: dict[str, Any], error: str) -> dict[str, Any]:
        """动态重规划 - 执行失败时自动调整计划"""
        logger.info(f"🔄 动态重规划: 任务 {failed_task.get('task_id', '')} 失败")

        tasks = list(original_plan.get("tasks", []))

        for i, task in enumerate(tasks):
            if task.get("task_id") == failed_task.get("task_id"):
                tasks[i] = {
                    **task,
                    "status": TaskStatus.FAILED.value,
                    "error": error,
                    "retry_count": task.get("retry_count", 0) + 1,
                }
                break

        if self._llm_client is not None:
            try:
                alternative_tasks = await self._generate_alternative_tasks(failed_task, error)
                tasks.extend(alternative_tasks)
            except Exception as e:
                logger.warning(f"⚠️ LLM 生成替代任务失败: {e}")

        dag = self._build_dag(tasks)

        return {
            **original_plan,
            "tasks": tasks,
            "dag": dag,
            "parallel_groups": self._identify_parallel_groups(dag),
            "replanned": True,
            "original_failed_task": failed_task.get("task_id"),
        }

    def _decompose_task(self, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """任务分解（关键词模板 + 增强版依赖关系）"""
        raw_input = intent.get("raw_input", "")

        if "设计" in raw_input and "API" in raw_input:
            tasks = self._decompose_api_design_task(intent)
        elif "代码" in raw_input or "实现" in raw_input:
            tasks = self._decompose_coding_task(intent)
        elif "分析" in raw_input or "需求" in raw_input:
            tasks = self._decompose_analysis_task(intent)
        else:
            tasks = [
                {
                    "task_id": generate_uuid(),
                    "description": raw_input,
                    "assignee": "engineer",
                    "status": TaskStatus.PENDING.value,
                    "input_params": intent.get("context", {}),
                    "dependencies": [],
                    "priority": 0,
                }
            ]

        return tasks

    async def _decompose_with_llm(self, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """使用 LLM 驱动的动态任务分解"""
        raw_input = intent.get("raw_input", "")

        prompt = f"""请将以下任务分解为具体的子任务列表。

任务: {raw_input}

请严格按照以下 JSON 格式输出（不要输出其他内容）:
[
    {{
        "description": "子任务描述",
        "assignee": "analyst/engineer/architect/manager",
        "dependencies": [],
        "priority": 1-5
    }}
]

子任务列表:"""

        try:
            response = await self._llm_client.generate(prompt, temperature=0.2)
            tasks = self._parse_llm_decomposition(response, intent)
            if tasks:
                logger.info(f"🧠 LLM 分解完成: {len(tasks)} 个子任务")
                return tasks
        except Exception as e:
            logger.warning(f"⚠️ LLM 分解失败: {e}，回退到模板分解")

        return self._decompose_task(intent)

    def _parse_llm_decomposition(self, response: str, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """解析 LLM 返回的任务分解"""
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                tasks = []
                for item in parsed:
                    if isinstance(item, dict) and "description" in item:
                        tasks.append({
                            "task_id": generate_uuid(),
                            "description": item["description"],
                            "assignee": item.get("assignee", "engineer"),
                            "status": TaskStatus.PENDING.value,
                            "input_params": intent.get("context", {}),
                            "dependencies": item.get("dependencies", []),
                            "priority": item.get("priority", 3),
                        })
                return tasks
            except json.JSONDecodeError:
                pass
        return []

    async def _generate_alternative_tasks(self, failed_task: dict[str, Any], error: str) -> list[dict[str, Any]]:
        """生成替代任务"""
        prompt = f"""任务执行失败，请生成替代方案。

失败任务: {failed_task.get('description', '')}
错误信息: {error}

请生成1-2个替代任务（JSON数组格式）:
[
    {{
        "description": "替代任务描述",
        "assignee": "analyst/engineer/architect",
        "priority": 3
    }}
]"""

        response = await self._llm_client.generate(prompt, temperature=0.3)
        alternatives = self._parse_llm_decomposition(response, {"context": {}})

        for task in alternatives:
            task["is_alternative"] = True
            task["replaces"] = failed_task.get("task_id")

        return alternatives

    def _build_dag(self, tasks: list[dict[str, Any]]) -> dict[str, list[str]]:
        """构建任务依赖图（DAG）"""
        dag: dict[str, list[str]] = {}

        task_ids = {t.get("task_id", str(i)) for i, t in enumerate(tasks)}

        for i, task in enumerate(tasks):
            task_id = task.get("task_id", str(i))
            deps = task.get("dependencies", [])

            valid_deps = [d for d in deps if d in task_ids]
            dag[task_id] = valid_deps

        return dag

    def _identify_parallel_groups(self, dag: dict[str, list[str]]) -> list[list[str]]:
        """识别可并行执行的任务组"""
        groups: list[list[str]] = []
        completed: set[str] = set()
        remaining = set(dag.keys())

        while remaining:
            ready = []
            for task_id in remaining:
                deps = dag.get(task_id, [])
                if all(dep in completed for dep in deps):
                    ready.append(task_id)

            if not ready:
                groups.append(list(remaining))
                break

            groups.append(ready)
            completed.update(ready)
            remaining -= set(ready)

        return groups

    def _decompose_api_design_task(self, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """分解API设计任务"""
        task_1_id = generate_uuid()
        task_2_id = generate_uuid()
        return [
            {
                "task_id": task_1_id,
                "description": "分析API需求",
                "assignee": "analyst",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
                "dependencies": [],
                "priority": 5,
            },
            {
                "task_id": task_2_id,
                "description": "设计API架构",
                "assignee": "architect",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
                "dependencies": [task_1_id],
                "priority": 4,
            },
            {
                "task_id": generate_uuid(),
                "description": "实现API代码",
                "assignee": "engineer",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
                "dependencies": [task_2_id],
                "priority": 3,
            },
        ]

    def _decompose_coding_task(self, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """分解编码任务"""
        task_1_id = generate_uuid()
        task_2_id = generate_uuid()
        return [
            {
                "task_id": task_1_id,
                "description": "分析编码需求",
                "assignee": "engineer",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
                "dependencies": [],
                "priority": 5,
            },
            {
                "task_id": task_2_id,
                "description": "编写代码实现",
                "assignee": "engineer",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
                "dependencies": [task_1_id],
                "priority": 4,
            },
            {
                "task_id": generate_uuid(),
                "description": "测试代码功能",
                "assignee": "engineer",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
                "dependencies": [task_2_id],
                "priority": 3,
            },
        ]

    def _decompose_analysis_task(self, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """分解分析任务"""
        task_1_id = generate_uuid()
        task_2_id = generate_uuid()
        return [
            {
                "task_id": task_1_id,
                "description": "收集需求信息",
                "assignee": "analyst",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
                "dependencies": [],
                "priority": 5,
            },
            {
                "task_id": task_2_id,
                "description": "分析需求内容",
                "assignee": "analyst",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
                "dependencies": [task_1_id],
                "priority": 4,
            },
            {
                "task_id": generate_uuid(),
                "description": "生成分析报告",
                "assignee": "analyst",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
                "dependencies": [task_2_id],
                "priority": 3,
            },
        ]
