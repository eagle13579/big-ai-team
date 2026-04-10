from typing import Any

from sqlalchemy.orm import Session

from ..core.dispatcher import Dispatcher
from ..core.factory import RoleFactory
from ..core.planner import Planner
from ..shared.schemas import IntentRequest, TaskRequest


class TaskRouter:
    """任务路由器"""

    def __init__(self, db: Session):
        self.role_factory = RoleFactory()
        self.planner = Planner()
        self.dispatcher = Dispatcher(db)

    def route_intent(self, intent: IntentRequest) -> dict[str, Any]:
        """路由意图"""
        # 处理意图
        intent_data = {
            "raw_input": intent.raw_input,
            "platform": intent.platform,
            "user_id": intent.user_id,
            "context": intent.context,
        }

        # 创建计划
        plan = self.planner.create_plan(intent_data)

        # 调度任务
        tasks = []
        for task_data in plan["tasks"]:
            task_data["plan_id"] = plan["plan_id"]
            task = self.dispatcher.dispatch_task(task_data)
            tasks.append(
                {
                    "task_id": str(task.task_id),
                    "description": task.description,
                    "assignee": task.assignee,
                    "status": task.status.value,
                }
            )

        return {"plan_id": plan["plan_id"], "tasks": tasks, "status": "dispatched"}

    def route_task(self, task: TaskRequest) -> dict[str, Any]:
        """路由任务"""
        task_data = {
            "plan_id": task.plan_id,
            "description": task.description,
            "assignee": task.assignee,
            "input_params": task.input_params,
            "dependencies": task.dependencies,
        }

        # 调度任务
        dispatched_task = self.dispatcher.dispatch_task(task_data)

        return {
            "task_id": str(dispatched_task.task_id),
            "plan_id": dispatched_task.plan_id,
            "status": dispatched_task.status.value,
            "assignee": dispatched_task.assignee,
        }

    def get_route_options(self, intent_type: str) -> dict[str, Any]:
        """获取路由选项"""
        # 根据意图类型返回可用的角色和任务类型
        role_map = {
            "设计": ["architect", "analyst"],
            "开发": ["engineer"],
            "分析": ["analyst"],
            "测试": ["engineer"],
            "部署": ["engineer", "manager"],
        }

        return {
            "available_roles": role_map.get(intent_type, ["engineer"]),
            "suggested_workflow": self._get_suggested_workflow(intent_type),
        }

    def _get_suggested_workflow(self, intent_type: str) -> list:
        """获取建议的工作流"""
        workflows = {
            "设计": ["需求分析", "架构设计", "方案评审"],
            "开发": ["代码实现", "单元测试", "集成测试"],
            "分析": ["数据收集", "数据分析", "报告生成"],
            "测试": ["测试计划", "测试执行", "测试报告"],
            "部署": ["构建", "部署", "监控"],
        }

        return workflows.get(intent_type, ["任务执行"])
