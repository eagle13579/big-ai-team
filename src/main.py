from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .shared.config import settings
from .persistence.database import get_db
from .shared.schemas import IntentRequest, TaskRequest, TaskResponse, MCPRequest, MCPResponse
from .access.router import TaskRouter
from .execution.executor import ToolExecutor
from .core.state import TaskStateMachine

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 意图处理端点
@app.post(f"{settings.API_V1_STR}/intent/process")
async def process_intent(
    intent: IntentRequest,
    db: Session = Depends(get_db)
):
    """处理用户意图"""
    router = TaskRouter(db)
    result = router.route_intent(intent)
    return result

# 任务编排端点
@app.post(f"{settings.API_V1_STR}/orchestrator/dispatch")
async def dispatch_task(
    task: TaskRequest,
    db: Session = Depends(get_db)
):
    """调度任务"""
    router = TaskRouter(db)
    result = router.route_task(task)
    return result

# 工具执行端点
@app.post(f"{settings.API_V1_STR}/tools/execute")
async def execute_tool(
    request: MCPRequest
):
    """执行工具"""
    executor = ToolExecutor()
    tool_name = request.params.get("name")
    arguments = request.params.get("arguments", {})
    
    result = executor.execute_tool(tool_name, arguments)
    return MCPResponse(
        id=request.id,
        result=result if result["success"] else None,
        error={"code": 500, "message": result["error"]} if not result["success"] else None
    )

# 获取任务状态端点
@app.get(f"{settings.API_V1_STR}/tasks/{{task_id}}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取任务状态"""
    state_machine = TaskStateMachine(db)
    status = state_machine.get_task_state(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "status": status}

# 列出可用工具端点
@app.get(f"{settings.API_V1_STR}/tools/list")
async def list_tools():
    """列出可用工具"""
    executor = ToolExecutor()
    tools = executor.list_tools()
    return {"tools": tools}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
