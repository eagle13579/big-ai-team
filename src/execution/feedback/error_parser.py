import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.shared.logging import logger


class ErrorSeverity(str, Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorCategory(str, Enum):
    SYNTAX = "syntax"
    TYPE = "type"
    RUNTIME = "runtime"
    LOGIC = "logic"
    IMPORT = "import"
    CONFIGURATION = "configuration"
    TEST_FAILURE = "test_failure"
    LINT = "lint"
    UNKNOWN = "unknown"


@dataclass
class ParsedError:
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    file_path: str | None = None
    line_number: int | None = None
    column_number: int | None = None
    function_name: str | None = None
    traceback: str | None = None
    suggestion: str | None = None
    raw_line: str = ""


class ErrorParser:
    """
    错误解析器 - 解析测试/lint/类型检查输出为结构化错误
    """

    PATTERNS: list[tuple[ErrorCategory, re.Pattern]] = [
        (ErrorCategory.SYNTAX, re.compile(r'SyntaxError:\s*(.+)')),
        (ErrorCategory.SYNTAX, re.compile(r'IndentationError:\s*(.+)')),
        (ErrorCategory.TYPE, re.compile(r'TypeError:\s*(.+)')),
        (ErrorCategory.TYPE, re.compile(r'AttributeError:\s*(.+)')),
        (ErrorCategory.IMPORT, re.compile(r'ImportError:\s*(.+)')),
        (ErrorCategory.IMPORT, re.compile(r'ModuleNotFoundError:\s*(.+)')),
        (ErrorCategory.RUNTIME, re.compile(r'RuntimeError:\s*(.+)')),
        (ErrorCategory.RUNTIME, re.compile(r'ValueError:\s*(.+)')),
        (ErrorCategory.RUNTIME, re.compile(r'KeyError:\s*(.+)')),
        (ErrorCategory.RUNTIME, re.compile(r'IndexError:\s*(.+)')),
        (ErrorCategory.RUNTIME, re.compile(r'FileNotFoundError:\s*(.+)')),
        (ErrorCategory.RUNTIME, re.compile(r'PermissionError:\s*(.+)')),
        (ErrorCategory.LOGIC, re.compile(r'AssertionError:\s*(.+)')),
        (ErrorCategory.TEST_FAILURE, re.compile(r'FAILED\s+(.+)')),
        (ErrorCategory.TEST_FAILURE, re.compile(r'AssertionError')),
        (ErrorCategory.LINT, re.compile(r'[A-Z]\d{3}\s+(.+)')),
    ]

    FILE_LINE_PATTERN = re.compile(r'File\s+"([^"]+)",\s+line\s+(\d+)')

    RUFF_PATTERN = re.compile(r'(.+):(\d+):(\d+):\s+([A-Z]\d{3})\s+(.+)')

    MYPY_PATTERN = re.compile(r'(.+):(\d+):\s+error:\s+(.+)')

    def parse(self, output: str, test_type: str = "pytest") -> list[ParsedError]:
        """解析输出为结构化错误列表"""
        errors = []

        if test_type == "ruff":
            errors.extend(self._parse_ruff_output(output))
        elif test_type == "mypy":
            errors.extend(self._parse_mypy_output(output))
        else:
            errors.extend(self._parse_pytest_output(output))

        return errors

    def _parse_pytest_output(self, output: str) -> list[ParsedError]:
        """解析 pytest 输出"""
        errors = []
        lines = output.splitlines()

        current_file = None
        current_line_num = None

        for line in lines:
            file_match = self.FILE_LINE_PATTERN.search(line)
            if file_match:
                current_file = file_match.group(1)
                current_line_num = int(file_match.group(2))

            for category, pattern in self.PATTERNS:
                match = pattern.search(line)
                if match:
                    message = match.group(1) if match.lastindex else match.group(0)
                    severity = self._determine_severity(category)

                    errors.append(ParsedError(
                        category=category,
                        severity=severity,
                        message=message.strip(),
                        file_path=current_file,
                        line_number=current_line_num,
                        raw_line=line.strip(),
                    ))
                    break

        return errors

    def _parse_ruff_output(self, output: str) -> list[ParsedError]:
        """解析 ruff 输出"""
        errors = []

        for line in output.splitlines():
            match = self.RUFF_PATTERN.search(line)
            if match:
                errors.append(ParsedError(
                    category=ErrorCategory.LINT,
                    severity=ErrorSeverity.WARNING,
                    message=match.group(5).strip(),
                    file_path=match.group(1),
                    line_number=int(match.group(2)),
                    column_number=int(match.group(3)),
                    raw_line=line.strip(),
                    suggestion=self._ruff_suggestion(match.group(4)),
                ))

        return errors

    def _parse_mypy_output(self, output: str) -> list[ParsedError]:
        """解析 mypy 输出"""
        errors = []

        for line in output.splitlines():
            match = self.MYPY_PATTERN.search(line)
            if match:
                errors.append(ParsedError(
                    category=ErrorCategory.TYPE,
                    severity=ErrorSeverity.ERROR,
                    message=match.group(3).strip(),
                    file_path=match.group(1),
                    line_number=int(match.group(2)),
                    raw_line=line.strip(),
                ))

        return errors

    def _determine_severity(self, category: ErrorCategory) -> ErrorSeverity:
        """根据错误类别确定严重程度"""
        severity_map = {
            ErrorCategory.SYNTAX: ErrorSeverity.CRITICAL,
            ErrorCategory.TYPE: ErrorSeverity.ERROR,
            ErrorCategory.RUNTIME: ErrorSeverity.ERROR,
            ErrorCategory.IMPORT: ErrorSeverity.ERROR,
            ErrorCategory.LOGIC: ErrorSeverity.ERROR,
            ErrorCategory.TEST_FAILURE: ErrorSeverity.ERROR,
            ErrorCategory.LINT: ErrorSeverity.WARNING,
            ErrorCategory.CONFIGURATION: ErrorSeverity.WARNING,
            ErrorCategory.UNKNOWN: ErrorSeverity.INFO,
        }
        return severity_map.get(category, ErrorSeverity.INFO)

    def _ruff_suggestion(self, code: str) -> str:
        """根据 ruff 错误代码提供建议"""
        suggestions = {
            "E501": "行过长，建议拆分或使用括号续行",
            "F401": "未使用的导入，建议移除",
            "F841": "未使用的变量，建议移除或使用 _ 前缀",
            "E302": "缺少空行，在函数/类定义前添加两个空行",
            "E303": "空行过多，保留一个空行即可",
            "W293": "行尾空白字符，建议移除",
        }
        return suggestions.get(code, f"参考 ruff 规则 {code}")

    def summarize(self, errors: list[ParsedError]) -> dict[str, Any]:
        """汇总错误统计"""
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_file: dict[str, int] = {}

        for error in errors:
            by_category[error.category.value] = by_category.get(error.category.value, 0) + 1
            by_severity[error.severity.value] = by_severity.get(error.severity.value, 0) + 1
            if error.file_path:
                by_file[error.file_path] = by_file.get(error.file_path, 0) + 1

        return {
            "total_errors": len(errors),
            "by_category": by_category,
            "by_severity": by_severity,
            "by_file": by_file,
            "has_critical": ErrorSeverity.CRITICAL.value in by_severity,
        }
