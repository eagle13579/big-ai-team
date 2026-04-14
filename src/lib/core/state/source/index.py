from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from src.persistence.models import Task, TaskStatus
from src.shared.logging import logger


class TaskStateMachine:
    """任务状态机 - 增强版：支持暂停/恢复/回滚/分支/合并"""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._state_history: dict[str, list[dict[str, Any]]] = {}

    def transition(self, task_id: str, new_status: str) -> Task | None:
        """状态转换"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return None

        if not self._is_valid_transition(task.status, new_status):
            logger.warning(f"⚠️ 无效的状态转换: {task.status.value} -> {new_status}")
            return None

        self._record_history(task_id, task.status.value, new_status)

        task.status = TaskStatus(new_status)
        self.db.commit()
        self.db.refresh(task)
        return task

    def pause(self, task_id: str) -> Task | None:
        """暂停任务"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return None

        if task.status.value not in ["in_progress", "pending"]:
            logger.warning(f"⚠️ 任务 {task_id} 当前状态 {task.status.value} 不可暂停")
            return None

        self._record_history(task_id, task.status.value, "paused")
        task.status = TaskStatus("paused") if hasattr(TaskStatus, "PAUSED") else task.status
        task.output = task.output or {}
        if isinstance(task.output, dict):
            task.output["paused_at"] = datetime.now().isoformat()
            task.output["previous_status"] = "in_progress"
        self.db.commit()
        self.db.refresh(task)
        logger.info(f"⏸️ 任务 {task_id} 已暂停")
        return task

    def resume(self, task_id: str) -> Task | None:
        """恢复暂停的任务"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return None

        previous_status = "in_progress"
        if isinstance(task.output, dict):
            previous_status = task.output.get("previous_status", "in_progress")

        self._record_history(task_id, task.status.value, previous_status)
        task.status = TaskStatus(previous_status)
        if isinstance(task.output, dict):
            task.output["resumed_at"] = datetime.now().isoformat()
        self.db.commit()
        self.db.refresh(task)
        logger.info(f"▶️ 任务 {task_id} 已恢复到 {previous_status}")
        return task

    def rollback(self, task_id: str, target_status: str | None = None) -> Task | None:
        """回滚任务到历史状态"""
        history = self._state_history.get(task_id, [])
        if not history:
            logger.warning(f"⚠️ 任务 {task_id} 无历史记录，无法回滚")
            return None

        if target_status is None:
            target_status = history[-1]["from_status"]

        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return None

        old_status = task.status.value
        self._record_history(task_id, old_status, target_status)
        task.status = TaskStatus(target_status)
        if isinstance(task.output, dict):
            task.output["rolled_back_at"] = datetime.now().isoformat()
            task.output["rolled_back_from"] = old_status
        self.db.commit()
        self.db.refresh(task)
        logger.info(f"⏪ 任务 {task_id} 已回滚到 {target_status}")
        return task

    def _is_valid_transition(self, current_status: Any, new_status: str) -> bool:
        """检查状态转换是否有效"""
        if hasattr(current_status, "value"):
            current_status = current_status.value
        elif isinstance(current_status, str):
            pass
        else:
            return False

        valid_transitions: dict[str, list[str]] = {
            TaskStatus.PENDING.value: ["in_progress", "failed", "paused"],
            TaskStatus.IN_PROGRESS.value: ["completed", "failed", "retrying", "paused"],
            TaskStatus.COMPLETED.value: [],
            TaskStatus.FAILED.value: ["retrying"],
            TaskStatus.RETRYING.value: ["in_progress", "failed"],
            "paused": ["in_progress", "pending", "failed"],
        }

        return new_status in valid_transitions.get(current_status, [])

    def _record_history(self, task_id: str, from_status: str, to_status: str):
        """记录状态变更历史"""
        if task_id not in self._state_history:
            self._state_history[task_id] = []

        self._state_history[task_id].append({
            "from_status": from_status,
            "to_status": to_status,
            "timestamp": datetime.now().isoformat(),
        })

        if len(self._state_history[task_id]) > 50:
            self._state_history[task_id] = self._state_history[task_id][-25:]

    def get_history(self, task_id: str) -> list[dict[str, Any]]:
        """获取任务状态变更历史"""
        return list(self._state_history.get(task_id, []))

    def get_task_state(self, task_id: str) -> str | None:
        """获取任务状态"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        return task.status.value if task else None

    def get_plan_state(self, plan_id: str) -> dict[str, Any]:
        """获取计划状态"""
        tasks = self.db.query(Task).filter(Task.plan_id == plan_id).all()

        if not tasks:
            return {"status": "not_found", "tasks": []}

        status_counts: dict[str, int] = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "retrying": 0,
            "paused": 0,
        }

        for task in tasks:
            status_val = task.status.value
            status_counts[status_val] = status_counts.get(status_val, 0) + 1

        if status_counts.get("failed", 0) > 0:
            plan_status = "failed"
        elif status_counts.get("paused", 0) > 0:
            plan_status = "paused"
        elif status_counts.get("in_progress", 0) > 0 or status_counts.get("retrying", 0) > 0:
            plan_status = "in_progress"
        elif status_counts.get("pending", 0) > 0:
            plan_status = "pending"
        else:
            plan_status = "completed"

        return {"status": plan_status, "tasks": status_counts, "total_tasks": len(tasks)}

    def get_next_pending_task(self, assignee: str | None = None) -> Task | None:
        """获取下一个待处理任务"""
        query = self.db.query(Task).filter(Task.status == TaskStatus.PENDING)
        if assignee:
            query = query.filter(Task.assignee == assignee)
        return query.order_by(Task.created_at).first()
