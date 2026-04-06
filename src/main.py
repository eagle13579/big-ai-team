import asyncio
import logging
import sys
import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# 导入项目核心组件
from shared.config import settings, config_manager
from execution.executor import ToolExecutor
from workflow.loop import ExecutionLoop

# --- 1. 配置生产级日志系统 ---
import os

# 创建日志目录
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 控制台输出
        logging.FileHandler(
            os.path.join(LOG_DIR, f"agent_{datetime.now().strftime('%Y%m%d')}.log"),
            encoding='utf-8'  # 指定 UTF-8 编码，解决中文乱码问题
        )  # 文件输出
    ]
)
logger = logging.getLogger("AceAgent.Main")

# --- 2. 定义请求和响应模型 ---
class TaskRequest(BaseModel):
    query: str
    max_steps: int = None

class TaskResponse(BaseModel):
    status: str
    final_answer: str = None
    total_steps: int
    steps: list
    start_time: str
    end_time: str

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    components: dict

# --- 3. 应用生命周期管理 ---
class AceAgentApp:
    """
    🚀 Ace Agent 项目主入口 (2026 最佳实践)
    负责组件生命周期管理、异常熔断与任务调度。
    """

    def __init__(self):
        logger.info(f"🌟 初始化 {settings.PROJECT_NAME} 核心组件...")
        
        # 初始化执行器 (负责具体工具操作)
        self.executor = ToolExecutor()
        
        # 初始化工作流循环 (负责 AI 决策大脑)
        # 这里自动从 settings 中读取 AGENT_MAX_STEPS
        self.workflow = ExecutionLoop(executor=self.executor)
        
        logger.info("✅ 组件加载完毕。当前系统时间: 2026-04-06 01:27:00")

    async def run_task(self, query: str, max_steps: int = None):
        """
        核心任务运行方法
        """
        try:
            # 启动自适应决策循环
            result = await self.workflow.run(query)
            return result
        except Exception as e:
            logger.error(f"🚨 系统运行期间发生未捕获异常: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"任务执行失败: {str(e)}")

    def display_welcome(self):
        """显示项目启动信息"""
        welcome_msg = f"""
        -------------------------------------------
        Project: {settings.PROJECT_NAME}
        Status:  Operational
        Time:    2026-04-06 01:27:00 (GMT+8)
        -------------------------------------------
        """
        print(welcome_msg)

# 导入监控模块
try:
    from shared.monitoring import init_monitoring
except ImportError:
    init_monitoring = None

# --- 4. FastAPI 应用初始化 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时
    logger.info("🚀 启动 Ace Agent 服务...")
    app.state.agent_app = AceAgentApp()
    app.state.agent_app.display_welcome()
    
    # 初始化监控
    if init_monitoring:
        init_monitoring(app)
    
    yield
    # 关闭时
    logger.info("👋 关闭 Ace Agent 服务...")

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="2026 生产级 AI Agent 系统",
    version="2.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. 依赖注入 ---
def get_agent_app(request: Request):
    """
    获取 Agent 应用实例
    """
    return request.app.state.agent_app

# --- 6. 路由定义 ---
@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskRequest,
    agent_app: AceAgentApp = Depends(get_agent_app)
):
    """
    创建并执行任务
    """
    logger.info(f"📋 接收到任务: {task.query}")
    result = await agent_app.run_task(task.query, task.max_steps)
    return TaskResponse(
        status=result["status"],
        final_answer=result.get("final_answer"),
        total_steps=result["total_steps"],
        steps=result["steps"],
        start_time=result["start_time"],
        end_time=result["end_time"]
    )

@app.get("/health", response_model=HealthResponse)
async def health_check(
    agent_app: AceAgentApp = Depends(get_agent_app)
):
    """
    健康检查端点
    """
    try:
        # 检查执行器状态
        executor_status = await agent_app.executor.execute("get_system_status", {})
        
        # 检查工作流状态
        workflow_status = {
            "history_count": len(agent_app.workflow.history),
            "memory_summary": agent_app.workflow.get_memory_summary()
        }
        
        return HealthResponse(
            status="healthy",
            version=settings.CONFIG_VERSION,
            timestamp=datetime.now().isoformat(),
            components={
                "executor": executor_status,
                "workflow": workflow_status,
                "config": {
                    "version": settings.CONFIG_VERSION,
                    "env_mode": settings.ENV_MODE
                }
            }
        )
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            version=settings.CONFIG_VERSION,
            timestamp=datetime.now().isoformat(),
            components={"error": str(e)}
        )

@app.get("/api/v1/tools")
async def get_available_tools(
    agent_app: AceAgentApp = Depends(get_agent_app)
):
    """
    获取可用工具列表
    """
    tools = agent_app.executor.get_available_tools()
    return {"tools": tools}

@app.get("/api/v1/config")
async def get_config():
    """
    获取当前配置
    """
    config = config_manager.get_settings()
    return config.model_dump()

# --- 7. 异常处理 ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理
    """
    logger.error(f"全局异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"内部服务器错误: {str(exc)}"}
    )

# --- 8. 命令行执行 ---
async def main():
    """
    命令行执行入口
    """
    # 实例化应用
    app = AceAgentApp()
    app.display_welcome()

    # 模拟用户输入：你可以从 sys.argv 获取，或直接定义
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        # 默认测试任务
        user_query = "帮我调研 Ace 浏览器的 2026 年市场表现并生成一份 Markdown 报告"

    # 执行异步任务
    await app.run_task(user_query)

if __name__ == "__main__":
    # 检查是否以模块方式运行（用于 FastAPI）
    if "__uvicorn_main__" not in sys.modules:
        # 以命令行方式运行
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n👋 用户手动停止，正在安全退出...")
        except Exception as e:
            logger.critical(f"💥 无法启动 Ace Agent: {e}")
    else:
        # 以 FastAPI 模块方式运行，由 uvicorn 管理
        pass

# --- 9. 启动服务器 ---
if __name__ == "__main__" and "__uvicorn_main__" not in sys.modules:
    # 启动 FastAPI 服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
