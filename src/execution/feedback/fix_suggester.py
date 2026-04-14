from typing import Any

from src.execution.feedback.error_parser import ParsedError
from src.shared.logging import logger


class FixSuggester:
    """
    修复建议器 - 基于历史修复记录和错误模式提供修复建议
    """

    def __init__(self, llm_client=None):
        self._llm_client = llm_client
        self._fix_history: list[dict[str, Any]] = []

    async def suggest(self, errors: list[ParsedError], context: str = "") -> list[dict[str, Any]]:
        """
        为错误列表生成修复建议
        """
        suggestions = []

        for error in errors:
            historical_fix = self._find_historical_fix(error)
            rule_based_fix = self._get_rule_based_fix(error)

            if self._llm_client is not None and not historical_fix:
                try:
                    llm_fix = await self._get_llm_fix(error, context)
                    if llm_fix:
                        suggestions.append(llm_fix)
                        continue
                except Exception as e:
                    logger.warning(f"⚠️ LLM 修复建议失败: {e}")

            suggestion = historical_fix or {
                "error": error.message,
                "category": error.category.value,
                "severity": error.severity.value,
                "file_path": error.file_path,
                "line_number": error.line_number,
                "fix_type": "rule_based",
                "suggestion": rule_based_fix,
                "confidence": 0.7,
            }

            suggestions.append(suggestion)

        return suggestions

    def record_fix(self, error: ParsedError, fix_applied: str, success: bool):
        """记录修复历史"""
        self._fix_history.append({
            "error_message": error.message,
            "error_category": error.category.value,
            "fix_applied": fix_applied,
            "success": success,
            "file_path": error.file_path,
        })

        if len(self._fix_history) > 1000:
            self._fix_history = self._fix_history[-500:]

    def _find_historical_fix(self, error: ParsedError) -> dict[str, Any] | None:
        """从历史记录中查找相似错误的修复"""
        for record in reversed(self._fix_history):
            if record["error_category"] == error.category.value and record["success"]:
                if any(word in record["error_message"] for word in error.message.split() if len(word) > 3):
                    return {
                        "error": error.message,
                        "category": error.category.value,
                        "severity": error.severity.value,
                        "file_path": error.file_path,
                        "line_number": error.line_number,
                        "fix_type": "historical",
                        "suggestion": record["fix_applied"],
                        "confidence": 0.9,
                    }
        return None

    async def _get_llm_fix(self, error: ParsedError, context: str) -> dict[str, Any] | None:
        """使用 LLM 生成修复建议"""
        prompt = (
            f"错误类型: {error.category.value}\n"
            f"错误信息: {error.message}\n"
            f"文件: {error.file_path}, 行: {error.line_number}\n"
        )
        if context:
            prompt += f"上下文:\n{context[:500]}\n"

        prompt += "\n请提供简洁的修复建议（一句话）："

        response = await self._llm_client.generate(prompt, temperature=0.1)

        if response:
            return {
                "error": error.message,
                "category": error.category.value,
                "severity": error.severity.value,
                "file_path": error.file_path,
                "line_number": error.line_number,
                "fix_type": "llm",
                "suggestion": response.strip(),
                "confidence": 0.8,
            }
        return None

    def _get_rule_based_fix(self, error: ParsedError) -> str:
        """基于规则的修复建议"""
        rule_fixes: dict[str, str] = {
            "syntax": "检查语法：括号配对、冒号、缩进是否正确",
            "type": "检查类型：确保操作数类型匹配，使用 isinstance() 验证",
            "runtime": "检查运行时条件：添加异常处理和边界检查",
            "import": "检查导入：确认模块已安装，路径正确",
            "logic": "检查逻辑：验证条件判断和算法正确性",
            "test_failure": "检查测试：确认期望值与实际值匹配",
            "lint": "修复代码风格：遵循 PEP 8 规范",
        }
        return rule_fixes.get(error.category.value, "请根据错误信息检查相关代码")
