from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..persistence.models import Task, TaskStatus


class TaskStateMachine:
    """任务状态机"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def transition(self, task_id: str, new_status: str) -> Optional[Task]:
        """状态转换"""
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
    
    def _is_valid_transition(self, current_status: TaskStatus, new_status: str) -> bool:
        """检查状态转换是否有效"""
        valid_transitions = {
            TaskStatus.PENDING: ["in_progress", "failed"],
            TaskStatus.IN_PROGRESS: ["completed", "failed", "retrying"],
            TaskStatus.COMPLETED: [],
            TaskStatus.FAILED: ["retrying"],
            TaskStatus.RETRYING: ["in_progress", "failed"]
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    def get_task_state(self, task_id: str) -> Optional[str]:
        """获取任务状态"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        return task.status.value if task else None
    
    def get_plan_state(self, plan_id: str) -> Dict[str, Any]:
        """获取计划状态"""
        tasks = self.db.query(Task).filter(Task.plan_id == plan_id).all()
        
        if not tasks:
            return {"status": "not_found", "tasks": []}
        
        status_counts = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "retrying": 0
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
        
        return {
            "status": plan_status,
            "tasks": status_counts,
            "total_tasks": len(tasks)
        }
    
    def get_next_pending_task(self, assignee: Optional[str] = None) -> Optional[Task]:
        """获取下一个待处理任务"""
        query = self.db.query(Task).filter(Task.status == TaskStatus.PENDING)
        if assignee:
            query = query.filter(Task.assignee == assignee)
        return query.order_by(Task.created_at).first()
