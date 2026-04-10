from typing import Any

from src.persistence.models import TaskStatus
from src.shared.utils import generate_uuid


class Planner:
    """规划编排器"""

    def __init__(self):
        pass

    def create_plan(self, intent: dict[str, Any]) -> dict[str, Any]:
        """创建任务计划"""
        plan_id = generate_uuid()
        tasks = self._decompose_task(intent)

        return {"plan_id": plan_id, "tasks": tasks, "created_at": intent.get("timestamp", None)}

    def _decompose_task(self, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """任务分解"""
        raw_input = intent.get("raw_input", "")
        tasks = []

        # 根据输入内容分解任务
        if "设计" in raw_input and "API" in raw_input:
            tasks = self._decompose_api_design_task(intent)
        elif "代码" in raw_input or "实现" in raw_input:
            tasks = self._decompose_coding_task(intent)
        elif "分析" in raw_input or "需求" in raw_input:
            tasks = self._decompose_analysis_task(intent)
        else:
            # 默认任务分解
            tasks = [
                {
                    "task_id": generate_uuid(),
                    "description": raw_input,
                    "assignee": "engineer",
                    "status": TaskStatus.PENDING.value,
                    "input_params": intent.get("context", {}),
                }
            ]

        return tasks

    def _decompose_api_design_task(self, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """分解API设计任务"""
        return [
            {
                "task_id": generate_uuid(),
                "description": "分析API需求",
                "assignee": "analyst",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
            },
            {
                "task_id": generate_uuid(),
                "description": "设计API架构",
                "assignee": "architect",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
            },
            {
                "task_id": generate_uuid(),
                "description": "实现API代码",
                "assignee": "engineer",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
            },
        ]

    def _decompose_coding_task(self, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """分解编码任务"""
        return [
            {
                "task_id": generate_uuid(),
                "description": "分析编码需求",
                "assignee": "engineer",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
            },
            {
                "task_id": generate_uuid(),
                "description": "编写代码实现",
                "assignee": "engineer",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
            },
            {
                "task_id": generate_uuid(),
                "description": "测试代码功能",
                "assignee": "engineer",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
            },
        ]

    def _decompose_analysis_task(self, intent: dict[str, Any]) -> list[dict[str, Any]]:
        """分解分析任务"""
        return [
            {
                "task_id": generate_uuid(),
                "description": "收集需求信息",
                "assignee": "analyst",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
            },
            {
                "task_id": generate_uuid(),
                "description": "分析需求内容",
                "assignee": "analyst",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
            },
            {
                "task_id": generate_uuid(),
                "description": "生成分析报告",
                "assignee": "analyst",
                "status": TaskStatus.PENDING.value,
                "input_params": intent.get("context", {}),
            },
        ]
