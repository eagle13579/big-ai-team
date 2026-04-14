import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.shared.logging import logger


class TestType(str, Enum):
    PYTEST = "pytest"
    RUFF = "ruff"
    MYPY = "mypy"
    UNITTEST = "unittest"


@dataclass
class TestResult:
    test_type: TestType
    success: bool
    output: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    return_code: int = -1
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class TestRunner:
    """
    测试运行器 - 运行 pytest/ruff/mypy 并捕获结构化输出
    """

    def __init__(self, project_root: str = ".", timeout: int = 120):
        self._project_root = project_root
        self._timeout = timeout

    def run_all(self, paths: list[str] | None = None) -> list[TestResult]:
        """运行所有测试"""
        results = []
        results.append(self.run_pytest(paths))
        results.append(self.run_ruff(paths))
        results.append(self.run_mypy(paths))
        return results

    def run_pytest(self, paths: list[str] | None = None) -> TestResult:
        """运行 pytest"""
        cmd = ["python", "-m", "pytest"]
        if paths:
            cmd.extend(paths)
        else:
            cmd.append("tests/")
        cmd.extend(["-v", "--tb=short", "--no-header", "-q"])

        return self._execute_command(cmd, TestType.PYTEST)

    def run_ruff(self, paths: list[str] | None = None) -> TestResult:
        """运行 ruff 检查"""
        cmd = ["python", "-m", "ruff", "check"]
        if paths:
            cmd.extend(paths)
        else:
            cmd.append("src/")

        return self._execute_command(cmd, TestType.RUFF)

    def run_mypy(self, paths: list[str] | None = None) -> TestResult:
        """运行 mypy 类型检查"""
        cmd = ["python", "-m", "mypy"]
        if paths:
            cmd.extend(paths)
        else:
            cmd.append("src/")

        return self._execute_command(cmd, TestType.MYPY)

    def run_unittest(self, module: str) -> TestResult:
        """运行 unittest"""
        cmd = ["python", "-m", "unittest", module, "-v"]
        return self._execute_command(cmd, TestType.UNITTEST)

    def _execute_command(self, cmd: list[str], test_type: TestType) -> TestResult:
        """执行命令并捕获输出"""
        import time

        logger.info(f"🧪 运行 {test_type.value}: {' '.join(cmd)}")
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=self._project_root,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )

            duration = time.time() - start_time
            output = result.stdout + result.stderr
            success = result.returncode == 0

            errors = []
            warnings = []

            for line in output.splitlines():
                stripped = line.strip()
                if "ERROR" in stripped.upper() or "FAILED" in stripped.upper():
                    errors.append(stripped)
                elif "WARNING" in stripped.upper() or "WARN" in stripped.upper():
                    warnings.append(stripped)

            logger.info(f"🧪 {test_type.value} 完成: {'✅ 通过' if success else '❌ 失败'} ({duration:.1f}s)")

            return TestResult(
                test_type=test_type,
                success=success,
                output=output,
                errors=errors,
                warnings=warnings,
                return_code=result.returncode,
                duration_seconds=duration,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"❌ {test_type.value} 超时 ({self._timeout}s)")
            return TestResult(
                test_type=test_type,
                success=False,
                output=f"超时: {self._timeout}s",
                errors=[f"执行超时 ({self._timeout}s)"],
                duration_seconds=duration,
            )

        except FileNotFoundError as e:
            logger.error(f"❌ {test_type.value} 命令未找到: {e}")
            return TestResult(
                test_type=test_type,
                success=False,
                output=f"命令未找到: {e}",
                errors=[f"命令未找到: {e}"],
            )

        except Exception as e:
            logger.error(f"❌ {test_type.value} 执行异常: {e}")
            return TestResult(
                test_type=test_type,
                success=False,
                output=str(e),
                errors=[str(e)],
            )
