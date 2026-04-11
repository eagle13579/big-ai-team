import os
import subprocess
from abc import abstractmethod
from typing import Any

from .base import AdapterContext, BaseAdapter
from .registry import adapter_registry


class SandboxAdapter(BaseAdapter[dict[str, Any]]):
    """执行沙箱适配器基类"""

    async def execute(
        self, operation: str, params: dict[str, Any], context: AdapterContext | None = None
    ) -> dict[str, Any]:
        """执行沙箱操作"""
        if operation == "run":
            return await self.run(params, context)
        elif operation == "health_check":
            return await self._health_check(context)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    @abstractmethod
    async def run(
        self, params: dict[str, Any], context: AdapterContext | None = None
    ) -> dict[str, Any]:
        """运行代码"""
        pass

    async def _health_check(self, context: AdapterContext | None = None) -> dict[str, Any]:
        """健康检查"""
        try:
            # 尝试运行一个简单的命令
            result = await self.run({"code": "echo 'health check'"}, context)
            if result.get("stdout") == "health check\n":
                return {
                    "status": "healthy",
                    "platform": self.platform,
                    "timestamp": context.timestamp.isoformat() if context else None,
                }
            else:
                return {
                    "status": "unhealthy",
                    "platform": self.platform,
                    "error": "Health check failed",
                    "timestamp": context.timestamp.isoformat() if context else None,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "platform": self.platform,
                "error": str(e),
                "timestamp": context.timestamp.isoformat() if context else None,
            }


class DockerAdapter(SandboxAdapter):
    """Docker 执行沙箱适配器"""

    def __init__(self, config):
        super().__init__(config)
        self.image = self.config.config.get("image", "python:3.12-slim")

    async def initialize(self, context: AdapterContext | None = None) -> bool:
        """初始化适配器"""
        # 检查 Docker 是否可用
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Docker is not available")
            self._set_initialized(True)
            return True
        except Exception as e:
            raise Exception(f"Failed to initialize Docker adapter: {str(e)}")

    async def run(
        self, params: dict[str, Any], context: AdapterContext | None = None
    ) -> dict[str, Any]:
        """运行代码"""
        if not self.is_initialized():
            await self.initialize(context)

        code = params.get("code")
        if not code:
            raise ValueError("Code is required")

        # 创建临时文件
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # 运行 Docker 容器
            cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{temp_file}:/app/code.py",
                self.image,
                "python",
                "/app/code.py",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout} seconds",
                "returncode": 1,
            }
        except Exception as e:
            raise Exception(f"Run operation failed: {str(e)}")
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)

    async def close(self, context: AdapterContext | None = None) -> bool:
        """关闭适配器"""
        self._set_initialized(False)
        return True

    def get_status(self) -> dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "image": self.image,
        }


class E2BAdapter(SandboxAdapter):
    """E2B 执行沙箱适配器"""

    def __init__(self, config):
        super().__init__(config)
        self.api_key = self.config.config.get("api_key")
        self.template = self.config.config.get("template", "python3")
        self.client = None

    async def initialize(self, context: AdapterContext | None = None) -> bool:
        """初始化适配器"""
        if not self.api_key:
            raise ValueError("E2B API key is required")

        try:
            # 导入 E2B 客户端
            import e2b

            self.client = e2b
            self._set_initialized(True)
            return True
        except ImportError:
            raise Exception("E2B SDK is not installed. Please run: pip install e2b")
        except Exception as e:
            raise Exception(f"Failed to initialize E2B adapter: {str(e)}")

    async def run(
        self, params: dict[str, Any], context: AdapterContext | None = None
    ) -> dict[str, Any]:
        """运行代码"""
        if not self.client:
            await self.initialize(context)

        code = params.get("code")
        if not code:
            raise ValueError("Code is required")

        try:
            # 创建 E2B 沙箱
            with self.client.Sandbox(template=self.template, api_key=self.api_key) as sandbox:
                # 运行代码
                result = sandbox.process.start_and_wait(
                    "python3", ["-c", code], timeout=self.timeout
                )

                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.exit_code,
                }
        except Exception as e:
            raise Exception(f"Run operation failed: {str(e)}")

    async def close(self, context: AdapterContext | None = None) -> bool:
        """关闭适配器"""
        self.client = None
        self._set_initialized(False)
        return True

    def get_status(self) -> dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "template": self.template,
        }


# 注册执行沙箱适配器
adapter_registry.register("docker", DockerAdapter)
adapter_registry.register("e2b", E2BAdapter)
