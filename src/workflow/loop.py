from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..core.dispatcher import Dispatcher
from ..core.state import TaskStateMachine
from ..execution.executor import ToolExecutor
from ..persistence.models import Task, TaskStatus


class ExecutionLoop:
    """执行反馈循环"""
    
    def __init__(self, db: Session):
        self.db = db
        self.dispatcher = Dispatcher(db)
        self.state_machine = TaskStateMachine(db)
        self.executor = ToolExecutor()
    
    def run(self, task_id: str) -> Dict[str, Any]:
        """运行执行循环"""
        task = self.dispatcher.get_task_by_id(task_id)
        if not task:
            return {"status": "error", "message": "Task not found"}
        
        # 开始执行任务
        self.state_machine.transition(task_id, "in_progress")
        
        try:
            # 执行任务
            result = self._execute_task(task)
            
            # 更新任务状态和输出
            self.dispatcher.update_task_output(task_id, result)
            self.state_machine.transition(task_id, "completed")
            
            return {"status": "completed", "result": result}
        except Exception as e:
            # 处理错误
            error_message = str(e)
            self.dispatcher.update_task_output(task_id, {"error": error_message})
            
            # 尝试重试
            if task.retry_count < task.max_retries:
                self.state_machine.transition(task_id, "retrying")
                return {"status": "retrying", "error": error_message}
            else:
                self.state_machine.transition(task_id, "failed")
                return {"status": "failed", "error": error_message}
    
    def _execute_task(self, task: Any) -> Dict[str, Any]:
        """执行具体任务"""
        # 根据任务类型执行不同的操作
        description = task.description
        input_params = task.input_params or {}
        
        if "API" in description or "api" in description:
            return self._execute_api_task(input_params)
        elif "代码" in description or "code" in description:
            return self._execute_code_task(input_params)
        elif "分析" in description or "analyze" in description:
            return self._execute_analysis_task(input_params)
        else:
            return self._execute_general_task(input_params)
    
    def _execute_api_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行API相关任务"""
        # 这里可以实现具体的API设计或实现逻辑
        return {
            "api_design": "completed",
            "endpoints": params.get("endpoints", []),
            "status": "success"
        }
    
    def _execute_code_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码相关任务"""
        # 这里可以实现具体的代码执行逻辑
        return {
            "code_executed": True,
            "output": params.get("output", "Code execution completed"),
            "status": "success"
        }
    
    def _execute_analysis_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析相关任务"""
        # 这里可以实现具体的分析逻辑
        return {
            "analysis_completed": True,
            "insights": params.get("insights", []),
            "status": "success"
        }
    
    def _execute_general_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行通用任务"""
        # 这里可以实现通用任务执行逻辑
        return {
            "task_completed": True,
            "status": "success"
        }
    
    def monitor_tasks(self) -> Dict[str, Any]:
        """监控任务执行状态"""
        pending_tasks = self.dispatcher.get_pending_tasks()
        in_progress_tasks = self.db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).all()
        
        return {
            "pending_tasks": len(pending_tasks),
            "in_progress_tasks": len(in_progress_tasks),
            "total_tasks": len(pending_tasks) + len(in_progress_tasks)
        }
