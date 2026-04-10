from typing import Any, Optional

from sqlalchemy.orm import Session

from src.persistence.models import Task, TaskStatus


class TaskStateMachine:
    """任务状态机

    负责管理任务状态的转换和查询。

    Attributes:
        db: SQLAlchemy会话对象，用于数据库操作
    """

    def __init__(self, db: Session) -> None:
        """初始化任务状态机

        Args:
            db: SQLAlchemy会话对象
        """
        self.db = db

    def transition(self, task_id: str, new_status: str) -> Optional[Task]:
        """状态转换

        将任务从当前状态转换到新状态。

        Args:
            task_id: 任务ID
            new_status: 新的任务状态

        Returns:
            Optional[Task]: 转换后的任务对象，若任务不存在或转换无效则返回None
        """
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return None

        # 检查状态转换是否有效
        if not self._is_valid_transition(task.status, new_status):
            return None

        # 执行状态转换
        task.status = TaskStatus(new_status)
        self.db.commit()
        self.db.refresh(task)
        return task

    def _is_valid_transition(self, current_status: Any, new_status: str) -> bool:
        """检查状态转换是否有效

        Args:
            current_status: 当前任务状态
            new_status: 新的任务状态

        Returns:
            bool: 状态转换是否有效
        """
        # 处理SQLAlchemy Column对象
        if hasattr(current_status, "value"):
            current_status = current_status.value
        elif isinstance(current_status, str):
            pass
        else:
            return False

        valid_transitions: dict[str, list[str]] = {
            TaskStatus.PENDING.value: ["in_progress", "failed"],
            TaskStatus.IN_PROGRESS.value: ["completed", "failed", "retrying"],
            TaskStatus.COMPLETED.value: [],
            TaskStatus.FAILED.value: ["retrying"],
            TaskStatus.RETRYING.value: ["in_progress", "failed"],
        }

        return new_status in valid_transitions.get(current_status, [])

    def get_task_state(self, task_id: str) -> Optional[str]:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            Optional[str]: 任务状态值，若任务不存在则返回None
        """
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        return task.status.value if task else None

    def get_plan_state(self, plan_id: str) -> dict[str, Any]:
        """获取计划状态

        获取指定计划的整体状态和任务状态分布。

        Args:
            plan_id: 计划ID

        Returns:
            Dict[str, Any]: 计划状态信息，包含以下键：
                - status: 计划整体状态
                - tasks: 各状态任务数量
                - total_tasks: 总任务数
        """
        tasks = self.db.query(Task).filter(Task.plan_id == plan_id).all()

        if not tasks:
            return {"status": "not_found", "tasks": []}

        status_counts: dict[str, int] = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "retrying": 0,
        }

        for task in tasks:
            status_counts[task.status.value] += 1

        # 确定计划整体状态
        if status_counts["failed"] > 0:
            plan_status = "failed"
        elif status_counts["in_progress"] > 0 or status_counts["retrying"] > 0:
            plan_status = "in_progress"
        elif status_counts["pending"] > 0:
            plan_status = "pending"
        else:
            plan_status = "completed"

        return {"status": plan_status, "tasks": status_counts, "total_tasks": len(tasks)}

    def get_next_pending_task(self, assignee: Optional[str] = None) -> Optional[Task]:
        """获取下一个待处理任务

        获取最早创建的待处理任务，可选择按负责人过滤。

        Args:
            assignee: 任务负责人（可选，不指定则查询所有待处理任务）

        Returns:
            Optional[Task]: 下一个待处理任务，若不存在则返回None
        """
        query = self.db.query(Task).filter(Task.status == TaskStatus.PENDING)
        if assignee:
            query = query.filter(Task.assignee == assignee)
        return query.order_by(Task.created_at).first()
