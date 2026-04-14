import asyncio

from typing import Any

from src.execution.feedback.test_runner import TestRunner, TestType
from src.execution.feedback.error_parser import ErrorParser, ParsedError
from src.execution.feedback.feedback_injector import FeedbackInjector
from src.execution.feedback.fix_suggester import FixSuggester
from src.shared.logging import logger


class FeedbackLoop:
    """
    执行反馈闭环 - 代码变更 → 运行测试 → 捕获错误 → 解析错误 → 注入反馈 → LLM修复 → 重新测试
    """

    def __init__(self, llm_client=None, project_root: str = ".", max_iterations: int = 3):
        self._test_runner = TestRunner(project_root=project_root)
        self._error_parser = ErrorParser()
        self._feedback_injector = FeedbackInjector(llm_client)
        self._fix_suggester = FixSuggester(llm_client)
        self._llm_client = llm_client
        self._max_iterations = max_iterations
        self._iteration_log: list[dict[str, Any]] = []

    async def run(self, target_paths: list[str] | None = None) -> dict[str, Any]:
        """
        运行完整的反馈闭环
        """
        logger.info("🔄 启动执行反馈闭环")

        for iteration in range(1, self._max_iterations + 1):
            logger.info(f"🔄 反馈闭环第 {iteration}/{self._max_iterations} 轮")

            test_results = await asyncio.to_thread(self._test_runner.run_all, target_paths)

            all_errors = []
            for result in test_results:
                if not result.success:
                    errors = self._error_parser.parse(result.output, result.test_type.value)
                    all_errors.extend(errors)

            iteration_record = {
                "iteration": iteration,
                "test_results": [
                    {"type": r.test_type.value, "success": r.success, "errors": len(r.errors)}
                    for r in test_results
                ],
                "parsed_errors": len(all_errors),
            }

            if not all_errors:
                logger.info(f"✅ 第 {iteration} 轮所有测试通过，反馈闭环完成")
                iteration_record["status"] = "success"
                self._iteration_log.append(iteration_record)
                return {
                    "status": "success",
                    "iterations": iteration,
                    "message": "所有测试通过",
                }

            logger.info(f"⚠️ 第 {iteration} 轮发现 {len(all_errors)} 个错误")

            feedback = await self._feedback_injector.inject(all_errors)
            suggestions = await self._fix_suggester.suggest(all_errors)

            iteration_record["status"] = "has_errors"
            iteration_record["feedback"] = feedback[:500]
            iteration_record["suggestions_count"] = len(suggestions)
            self._iteration_log.append(iteration_record)

            if iteration < self._max_iterations:
                logger.info(f"🔄 生成修复反馈，等待代码修改后重新测试...")
            else:
                logger.warning(f"⚠️ 达到最大迭代次数 {self._max_iterations}，仍有错误")

        return {
            "status": "failed",
            "iterations": self._max_iterations,
            "message": f"经过 {self._max_iterations} 轮迭代仍有错误",
            "last_errors": len(all_errors) if all_errors else 0,
        }

    async def run_single_test(self, test_path: str) -> dict[str, Any]:
        """运行单个测试文件"""
        result = await asyncio.to_thread(self._test_runner.run_pytest, [test_path])

        if result.success:
            return {"status": "success", "output": result.output}

        errors = self._error_parser.parse(result.output, "pytest")
        feedback = await self._feedback_injector.inject(errors)
        suggestions = await self._fix_suggester.suggest(errors)

        return {
            "status": "failed",
            "errors": [
                {
                    "message": e.message,
                    "file": e.file_path,
                    "line": e.line_number,
                    "category": e.category.value,
                }
                for e in errors
            ],
            "feedback": feedback,
            "suggestions": suggestions,
        }

    def get_iteration_log(self) -> list[dict[str, Any]]:
        """获取迭代日志"""
        return list(self._iteration_log)

    def get_error_summary(self) -> dict[str, Any]:
        """获取错误汇总"""
        if not self._iteration_log:
            return {"total_iterations": 0}

        last_iteration = self._iteration_log[-1]
        return {
            "total_iterations": len(self._iteration_log),
            "last_status": last_iteration.get("status"),
            "last_error_count": last_iteration.get("parsed_errors", 0),
        }
