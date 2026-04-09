<<<<<<< New base: init
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from src.persistence.models import Task, TaskStatus
from src.shared.utils import generate_uuid


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
|||||||
=======
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from src.persistence.models import Task, TaskStatus
from src.shared.utils import generate_uuid


class Dispatcher:
    """子Agent调度器
    
    负责任务的调度、状态更新和查询操作。
    
    Attributes:
        db: SQLAlchemy会话对象，用于数据库操作
    """
    
    def __init__(self, db: Session) -> None:
        """初始化调度器
        
        Args:
            db: SQLAlchemy会话对象
        """
        self.db = db
    
    def dispatch_task(self, task_data: Dict[str, Any]) -> Task:
        """调度任务
        
        创建并保存新任务到数据库。
        
        Args:
            task_data: 任务数据字典，包含以下键：
                - task_id: 任务ID（可选，默认自动生成）
                - plan_id: 计划ID（必需）
                - parent_task_id: 父任务ID（可选）
                - description: 任务描述（必需）
                - assignee: 任务负责人（必需）
                - status: 任务状态（可选，默认pending）
                - input_params: 输入参数（可选）
                - dependencies: 依赖任务列表（可选，默认空列表）
        
        Returns:
            Task: 创建的任务对象
        """
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
    
    def get_pending_tasks(self, assignee: Optional[str] = None) -> List[Task]:
        """获取待处理任务
        
        查询状态为PENDING的任务，可选择按负责人过滤。
        
        Args:
            assignee: 任务负责人（可选，不指定则查询所有待处理任务）
        
        Returns:
            List[Task]: 待处理任务列表
        """
        query = self.db.query(Task).filter(Task.status == TaskStatus.PENDING)
        if assignee:
            query = query.filter(Task.assignee == assignee)
        return query.all()
    
    def update_task_status(self, task_id: str, status: str) -> Optional[Task]:
        """更新任务状态
        
        根据任务ID更新任务状态。
        
        Args:
            task_id: 任务ID
            status: 新的任务状态
        
        Returns:
            Optional[Task]: 更新后的任务对象，若任务不存在则返回None
        """
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = status
            self.db.commit()
            self.db.refresh(task)
        return task
    
    def update_task_output(self, task_id: str, output_data: Dict[str, Any]) -> Optional[Task]:
        """更新任务输出
        
        根据任务ID更新任务输出数据。
        
        Args:
            task_id: 任务ID
            output_data: 输出数据字典
        
        Returns:
            Optional[Task]: 更新后的任务对象，若任务不存在则返回None
        """
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.output_data = output_data
            self.db.commit()
            self.db.refresh(task)
        return task
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            Optional[Task]: 任务对象，若不存在则返回None
        """
        return self.db.query(Task).filter(Task.task_id == task_id).first()
    
    def get_tasks_by_plan(self, plan_id: str) -> List[Task]:
        """根据计划ID获取任务
        
        Args:
            plan_id: 计划ID
        
        Returns:
            List[Task]: 属于该计划的任务列表
        """
        return self.db.query(Task).filter(Task.plan_id == plan_id).all()
    
    def retry_task(self, task_id: str) -> Optional[Task]:
        """重试任务
        
        将任务状态设置为RETRYING并增加重试次数。
        
        Args:
            task_id: 任务ID
        
        Returns:
            Optional[Task]: 更新后的任务对象，若任务不存在或已达到最大重试次数则返回None
        """
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if task and task.retry_count < task.max_retries:
            task.status = "retrying"
            task.retry_count = task.retry_count + 1
            self.db.commit()
            self.db.refresh(task)
        return task
>>>>>>> Current commit: init
