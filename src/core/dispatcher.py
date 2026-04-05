from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..persistence.models import Task, TaskStatus
from ..shared.utils import generate_uuid


class Dispatcher:
    """子Agent调度器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def dispatch_task(self, task_data: Dict[str, Any]) -> Task:
        """调度任务"""
        task = Task(
            task_id=task_data.get("task_id", generate_uuid()),
            plan_id=task_data["plan_id"],
            parent_task_id=task_data.get("parent_task_id"),
            description=task_data["description"],
            assignee=task_data["assignee"],
            status=TaskStatus(task_data.get("status", "pending")),
            input_params=task_data.get("input_params"),
            dependencies=task_data.get("dependencies", [])
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_pending_tasks(self, assignee: Optional[str] = None) -> list[Task]:
        """获取待处理任务"""
        query = self.db.query(Task).filter(Task.status == TaskStatus.PENDING)
        if assignee:
            query = query.filter(Task.assignee == assignee)
        return query.all()
    
    def update_task_status(self, task_id: str, status: str) -> Optional[Task]:
        """更新任务状态"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = TaskStatus(status)
            self.db.commit()
            self.db.refresh(task)
        return task
    
    def update_task_output(self, task_id: str, output_data: Dict[str, Any]) -> Optional[Task]:
        """更新任务输出"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.output_data = output_data
            self.db.commit()
            self.db.refresh(task)
        return task
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        return self.db.query(Task).filter(Task.task_id == task_id).first()
    
    def get_tasks_by_plan(self, plan_id: str) -> list[Task]:
        """根据计划ID获取任务"""
        return self.db.query(Task).filter(Task.plan_id == plan_id).all()
    
    def retry_task(self, task_id: str) -> Optional[Task]:
        """重试任务"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if task and task.retry_count < task.max_retries:
            task.status = TaskStatus.RETRYING
            task.retry_count += 1
            self.db.commit()
            self.db.refresh(task)
        return task
