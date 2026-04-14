from typing import Any

from src.execution.feedback.error_parser import ParsedError
from src.shared.logging import logger


class FeedbackInjector:
    """
    反馈注入器 - 将错误信息注入 LLM 上下文，生成修复指令
    """

    def __init__(self, llm_client=None):
        self._llm_client = llm_client

    async def inject(self, errors: list[ParsedError], code_context: str = "") -> str:
        """
        将错误注入 LLM 上下文，生成修复指令
        """
        if not errors:
            return "没有检测到错误，代码质量良好。"

        error_summary = self._format_errors(errors)

        if self._llm_client is None:
            return self._generate_rule_based_feedback(errors, code_context)

        try:
            prompt = self._build_fix_prompt(errors, code_context)
            feedback = await self._llm_client.generate(prompt, temperature=0.2)
            return feedback
        except Exception as e:
            logger.error(f"❌ LLM 反馈注入失败: {e}，使用规则反馈")
            return self._generate_rule_based_feedback(errors, code_context)

    def _format_errors(self, errors: list[ParsedError]) -> str:
        """格式化错误列表"""
        lines = []
        for i, error in enumerate(errors, 1):
            location = ""
            if error.file_path:
                location = f" [{error.file_path}"
                if error.line_number:
                    location += f":{error.line_number}"
                location += "]"

            lines.append(
                f"{i}. [{error.severity.value.upper()}] {error.category.value}: "
                f"{error.message}{location}"
            )

            if error.suggestion:
                lines.append(f"   建议: {error.suggestion}")

        return "\n".join(lines)

    def _build_fix_prompt(self, errors: list[ParsedError], code_context: str) -> str:
        """构建修复 Prompt"""
        error_summary = self._format_errors(errors)

        context_section = ""
        if code_context:
            context_section = f"\n相关代码:\n```\n{code_context}\n```\n"

        return f"""以下代码存在错误，请分析并提供修复方案。

检测到的错误:
{error_summary}
{context_section}
请提供:
1. 每个错误的根因分析
2. 具体的修复代码（包含完整函数/方法）
3. 修复后需要验证的测试点

修复方案:"""

    def _generate_rule_based_feedback(self, errors: list[ParsedError], code_context: str) -> str:
        """基于规则的反馈生成（回退方案）"""
        feedback_lines = ["检测到以下错误，建议修复：\n"]

        for error in errors:
            fix = self._get_rule_based_fix(error)
            feedback_lines.append(f"- {error.message}")
            feedback_lines.append(f"  修复建议: {fix}\n")

        return "\n".join(feedback_lines)

    def _get_rule_based_fix(self, error: ParsedError) -> str:
        """基于错误类型提供规则化修复建议"""
        fixes = {
            "SyntaxError": "检查语法错误，确保括号、引号、冒号等配对正确",
            "IndentationError": "检查缩进是否一致，建议使用4空格缩进",
            "TypeError": "检查变量类型是否正确，确保操作符和函数参数类型匹配",
            "AttributeError": "检查对象是否具有该属性，可能是拼写错误或对象为None",
            "ImportError": "检查模块是否已安装，导入路径是否正确",
            "ModuleNotFoundError": "运行 pip install 安装缺失的模块",
            "ValueError": "检查函数参数值是否在有效范围内",
            "KeyError": "检查字典键是否存在，使用 .get() 方法安全访问",
            "IndexError": "检查索引是否越界，确保列表/数组长度足够",
            "FileNotFoundError": "检查文件路径是否正确，确保文件存在",
            "PermissionError": "检查文件/目录权限，可能需要管理员权限",
            "AssertionError": "检查断言条件，测试期望与实际结果不匹配",
        }

        for key, fix in fixes.items():
            if key in error.message or error.category.value in key.lower():
                return fix

        return "请检查相关代码逻辑，参考错误信息进行修复"
