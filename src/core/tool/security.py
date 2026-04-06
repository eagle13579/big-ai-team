from typing import Dict, List, Optional, Set, Any
import logging
import os
import subprocess
import tempfile
import shutil
import platform
from pydantic import BaseModel, Field

# 只有在类 Unix 系统下才能限制资源
if platform.system() != "Windows":
    import resource

logger = logging.getLogger(__name__)

class Permission(BaseModel):
    """ 权限模型 """
    name: str
    description: str

class ToolPermission(BaseModel):
    """ 工具权限模型 """
    tool_name: str
    required_permissions: List[str] = Field(default_factory=list)

class SecurityManager:
    """ 安全管理器，负责权限控制和安全策略 """
    
    def __init__(self):
        self.permissions: Dict[str, Permission] = {}
        self.tool_permissions: Dict[str, ToolPermission] = {}
        self.granted_permissions: Set[str] = set()
        # 定义危险指令黑名单，防止 Shell 注入
        self.banned_keywords = {
            ';', '&', '|', '>', '<', '`', '$', '(', ')', 
            'rm', 'mkfs', 'dd', 'chmod', 'chown', 'sudo'
        }

    def register_permission(self, permission: Permission) -> None:
        self.permissions[permission.name] = permission
        logger.info(f"Registered permission: {permission.name}")

    def register_tool_permission(self, tool_permission: ToolPermission) -> None:
        self.tool_permissions[tool_permission.tool_name] = tool_permission
        logger.info(f"Registered permissions for tool: {tool_permission.tool_name}")

    def grant_permission(self, permission_name: str) -> None:
        if permission_name in self.permissions:
            self.granted_permissions.add(permission_name)
            logger.info(f"Granted permission: {permission_name}")
        else:
            logger.warning(f"Permission {permission_name} not found")

    def check_permission(self, tool_name: str) -> bool:
        """ 
        检查工具是否有执行权限 
        核心改进：遵循“默认拒绝 (Default Deny)”原则
        """
        if tool_name not in self.tool_permissions:
            logger.error(f"Security Alert: Tool '{tool_name}' has no defined permissions. Access Denied.")
            return False 

        tool_permission = self.tool_permissions[tool_name]
        for required_perm in tool_permission.required_permissions:
            if required_perm not in self.granted_permissions:
                logger.warning(f"Tool {tool_name} requires {required_perm} which is not granted.")
                return False
        return True

    def validate_command_safety(self, command: List[str]) -> bool:
        """ 审计指令安全性，防止恶意注入 """
        cmd_str = " ".join(command).lower()
        for char in self.banned_keywords:
            if char in cmd_str:
                logger.error(f"Security Violation: Dangerous keyword '{char}' detected in command.")
                return False
        return True

class SecureSandbox:
    """ 
    安全沙箱：具备物理隔离与资源限制 
    """
    
    def __init__(self, temp_dir: Optional[str] = None, mem_limit_mb: int = 256, cpu_timeout_sec: int = 30):
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="ace_sandbox_")
        self.mem_limit = mem_limit_mb * 1024 * 1024  # 转换为字节
        self.cpu_timeout = cpu_timeout_sec
        logger.info(f"Created secure sandbox at: {self.temp_dir}")

    def _set_resource_limits(self):
        """ 设置进程级别的资源限制 (仅限 Unix) """
        if platform.system() != "Windows":
            # 限制内存使用量 (Address Space)
            resource.setrlimit(resource.RLIMIT_AS, (self.mem_limit, self.mem_limit))
            # 限制 CPU 时间
            resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_timeout, self.cpu_timeout))

    def execute_command(self, command: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """ 在受限沙箱中执行命令 """
        # 1. 首先通过全局安全管理器进行指令审计
        if not security_manager.validate_command_safety(command):
            raise PermissionError("Command rejected by Security Audit")

        exec_timeout = timeout or self.cpu_timeout

        try:
            logger.info(f"Executing sandboxed command: {' '.join(command)}")
            # 核心改进：通过 preexec_fn 注入资源限制
            result = subprocess.run(
                command,
                cwd=self.temp_dir,
                capture_output=True,
                text=True,
                timeout=exec_timeout,
                preexec_fn=self._set_resource_limits if platform.system() != "Windows" else None,
                shell=False # 强制禁用 shell=True，防止注入
            )
            return result
        except subprocess.TimeoutExpired:
            logger.error("Sandbox process killed: Timeout exceeded.")
            raise
        except Exception as e:
            logger.error(f"Sandbox execution error: {str(e)}")
            raise

    def cleanup(self) -> None:
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up sandbox: {self.temp_dir}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

# 创建全局安全管理器实例
security_manager = SecurityManager()