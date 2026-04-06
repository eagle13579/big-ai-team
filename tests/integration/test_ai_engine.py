import sys
import os
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Type, List
from pydantic import BaseModel, Field

# ==========================================
# 1. 自动路径适配（针对你的工程目录结构）
# ==========================================
# 获取项目根目录 (tests/integration/.. -> root)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../"))
src_dir = os.path.join(root_dir, "src")

# 将根目录和 src 目录加入系统路径，确保导入成功
for path in [root_dir, src_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

# ==========================================
# 2. 配置日志系统
# ==========================================
# 创建日志目录
LOG_DIR = os.path.join(root_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 控制台输出
        logging.FileHandler(
            os.path.join(LOG_DIR, f"agent_{datetime.now().strftime('%Y%m%d')}.log"),
            encoding='utf-8'  # 指定 UTF-8 编码，解决中文乱码问题
        )  # 文件输出
    ]
)
logger = logging.getLogger("TestAIEngine")
logger.info("测试日志系统初始化完成")

# ==========================================
# 2. 导入核心组件（确保 base.py, dispatcher.py, security.py 已就绪）
# ==========================================
try:
    from core.tool import BaseTool, ToolResult, LLMProtocol, ToolDispatcher, security_manager, ToolPermission, Permission, SecureSandbox
except ImportError as e:
    print(f"❌ [错误] 无法导入核心模块: {e}")
    print(f"🔍 [检查] 请确保 core/tool 目录结构正确")
    sys.exit(1)

# ==========================================
# 3. 模拟组件实现（用于集成测试）
# ==========================================

class MockLLM(LLMProtocol):
    """模拟 LLM：根据输入指令返回对应的工具调用 JSON"""
    async def generate(self, prompt: str) -> str:
        # 模拟：如果提到“查看”，生成合法的 dir 指令（Windows 兼容）
        if "查看" in prompt:
            return json.dumps({
                "tool_name": "shell_tool",
                "args": {"command": ["dir"]}
            })
        # 模拟：如果提到“删除”，生成危险指令进行拦截测试
        elif "删除" in prompt:
            return json.dumps({
                "tool_name": "shell_tool",
                "args": {"command": ["rm", "-rf", "/"]}
            })
        return "{}"

class ShellArgs(BaseModel):
    """参数校验架构"""
    command: List[str] = Field(..., description="要执行的命令列表，例如 ['ls', '-l']")

class ShellTool(BaseTool):
    """具体的工具实现：系统 Shell 工具（集成安全沙箱）"""
    name = "shell_tool"
    description = "用于在安全沙箱中执行系统指令"
    args_schema = ShellArgs

    async def execute(self, command: List[str]) -> ToolResult:
        # 使用你之前定义的 SecureSandbox 进行隔离执行
        with SecureSandbox() as sandbox:
            result = sandbox.execute_command(command)
            return ToolResult(
                success=result.returncode == 0,
                data={"output": result.stdout, "stderr": result.stderr},
                error=result.stderr if result.returncode != 0 else None
            )

# ==========================================
# 4. 自动化集成检测主流程
# ==========================================

async def run_diagnostic():
    import datetime
    print("="*50)
    print("🚀 Ace AI Engine 集成环境检测")
    print(f"📅 时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50 + "\n")
    
    # 初始化核心组件
    llm = MockLLM()
    dispatcher = ToolDispatcher(llm)
    
    # 注册工具
    shell_tool = ShellTool()
    dispatcher.register_tool(shell_tool)
    print("✅ [系统] ShellTool 注册成功。")
    
    # 注册并授予权限（模拟安全审计流程）
    security_manager.register_tool_permission(
        ToolPermission(tool_name="shell_tool", required_permissions=["sys_read"])
    )
    security_manager.register_permission(Permission(name="sys_read", description="允许读取系统文件"))
    security_manager.grant_permission("sys_read")
    print("✅ [安全] 权限策略初始化完成。\n")

    # --- 场景 1：合法流程测试 ---
    print("测试场景 [1/2]: 合法指令分发执行...")
    prompt_normal = "帮我查看当前目录下的文件列表"
    print(f"👉 输入: '{prompt_normal}'")
    
    res1 = await dispatcher.dispatch(prompt_normal)
    
    if res1.success:
        print(f"✨ 结果: 成功执行")
        print(f"📄 输出内容预览:\n{res1.data.get('output', '')[:100]}...")
    else:
        print(f"❌ 结果: 执行失败 - {res1.error}")

    print("\n" + "-"*30 + "\n")

    # --- 场景 2：安全拦截测试 ---
    print("测试场景 [2/2]: 恶意代码注入拦截...")
    prompt_danger = "帮我删除根目录下的所有内容"
    print(f"👉 输入: '{prompt_danger}'")
    
    res2 = await dispatcher.dispatch(prompt_danger)
    
    if not res2.success:
        print(f"🛡️ 拦截成功: {res2.error}")
        print("✅ 安全加固层（Security Layer）运行正常。")
    else:
        print("🚨 警告: 恶意指令未被拦截！请立即检查 security.py 逻辑。")

    print("\n" + "="*50)
    print("🎉 检测任务全部完成！核心引擎已就绪。")
    print("="*50)

if __name__ == "__main__":
    try:
        asyncio.run(run_diagnostic())
    except KeyboardInterrupt:
        pass