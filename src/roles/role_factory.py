from typing import Any

from src.shared.logging import logger


class Role:
    """角色基类"""

    def __init__(self, role_type: str, name: str, description: str):
        self.role_type = role_type
        self.name = name
        self.description = description

    def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """处理任务"""
        raise NotImplementedError("Subclass must implement process_task method")


class AnalystRole(Role):
    """分析专家角色"""

    def __init__(self):
        super().__init__(
            role_type="analyst", name="分析专家", description="负责分析任务需求，制定执行计划"
        )

    def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """处理分析任务"""
        try:
            # 分析任务需求
            task_description = task.get("description", "")

            # 生成分析结果
            analysis_result = {
                "task_type": self._identify_task_type(task_description),
                "required_skills": self._identify_required_skills(task_description),
                "execution_plan": self._generate_execution_plan(task_description),
                "estimated_time": self._estimate_time(task_description),
            }

            return {"status": "success", "data": analysis_result}
        except Exception as e:
            logger.error(f"分析专家处理任务失败: {str(e)}")
            return {"status": "error", "message": f"处理任务失败: {str(e)}"}

    def _identify_task_type(self, task_description: str) -> str:
        """识别任务类型"""
        if "代码" in task_description or "编程" in task_description:
            return "coding"
        elif "分析" in task_description or "研究" in task_description:
            return "analysis"
        elif "文档" in task_description or "写作" in task_description:
            return "documentation"
        else:
            return "general"

    def _identify_required_skills(self, task_description: str) -> list:
        """识别所需技能"""
        skills = []
        if "代码" in task_description:
            skills.append("coding")
        if "分析" in task_description:
            skills.append("analysis")
        if "文档" in task_description:
            skills.append("documentation")
        if "git" in task_description:
            skills.append("git")
        if "文件" in task_description:
            skills.append("file_management")
        return skills

    def _generate_execution_plan(self, task_description: str) -> list:
        """生成执行计划"""
        return ["分析任务需求", "制定执行步骤", "执行任务", "验证结果", "总结报告"]

    def _estimate_time(self, task_description: str) -> str:
        """估计执行时间"""
        if "代码" in task_description:
            return "30-60分钟"
        elif "分析" in task_description:
            return "15-30分钟"
        elif "文档" in task_description:
            return "20-40分钟"
        else:
            return "10-20分钟"


class ExecutorRole(Role):
    """执行专家角色 - 对接 ToolExecutor 执行真实任务"""

    def __init__(self, executor=None):
        super().__init__(
            role_type="executor", name="执行专家", description="负责执行具体任务，使用工具完成操作"
        )
        self._executor = executor

    def set_executor(self, executor):
        """设置工具执行器"""
        self._executor = executor

    def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """处理执行任务 - 对接真实 ToolExecutor"""
        try:
            task_description = task.get("description", "")
            tool_name = task.get("tool")
            tool_args = task.get("args", {})

            if not tool_name:
                return {
                    "status": "error",
                    "message": "缺少 tool 参数，无法执行",
                    "suggestion": "请指定要调用的工具名称",
                }

            if self._executor is None:
                return {
                    "status": "error",
                    "message": "执行器未初始化",
                    "task_description": task_description,
                }

            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run,
                            self._executor.execute(tool_name, tool_args)
                        )
                        result = future.result(timeout=60)
                else:
                    result = loop.run_until_complete(
                        self._executor.execute(tool_name, tool_args)
                    )
            except RuntimeError:
                result = asyncio.run(
                    self._executor.execute(tool_name, tool_args)
                )

            execution_result = {
                "task_description": task_description,
                "tool": tool_name,
                "tool_args": tool_args,
                "execution_status": "success" if result.get("success") else "failed",
                "result": result.get("result") if result.get("success") else None,
                "error": result.get("error") if not result.get("success") else None,
            }

            return {"status": "success" if result.get("success") else "error", "data": execution_result}

        except Exception as e:
            logger.error(f"执行专家处理任务失败: {str(e)}")
            return {"status": "error", "message": f"处理任务失败: {str(e)}"}


class ReviewerRole(Role):
    """审查专家角色 - 对接 ExecutionLoop 审查步骤"""

    def __init__(self, llm_client=None):
        super().__init__(
            role_type="reviewer", name="审查专家", description="负责审查任务执行结果，确保质量"
        )
        self._llm_client = llm_client

    def set_llm_client(self, llm_client):
        """设置 LLM 客户端"""
        self._llm_client = llm_client

    def process_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """处理审查任务 - 使用 LLM 进行智能审查"""
        try:
            task_description = task.get("description", "")
            execution_result = task.get("execution_result", {})

            review_checks = self._perform_automated_checks(execution_result)

            llm_review = None
            if self._llm_client is not None:
                try:
                    import asyncio
                    review_prompt = (
                        f"请审查以下任务执行结果的质量：\n"
                        f"任务描述: {task_description}\n"
                        f"执行结果: {execution_result}\n"
                        f"自动检查结果: {review_checks}\n"
                        f"请给出审查意见和改进建议。"
                    )
                    llm_review = asyncio.run(
                        self._llm_client.generate(review_prompt, temperature=0.3)
                    )
                except Exception as e:
                    logger.warning(f"LLM 审查失败，使用自动审查: {e}")

            passed = all(review_checks.values())
            review_result = {
                "task_description": task_description,
                "execution_result": execution_result,
                "review_status": "passed" if passed else "needs_improvement",
                "automated_checks": review_checks,
                "llm_review": llm_review,
                "review_comments": "审查通过" if passed else "需要改进",
            }

            return {"status": "success", "data": review_result}

        except Exception as e:
            logger.error(f"审查专家处理任务失败: {str(e)}")
            return {"status": "error", "message": f"处理任务失败: {str(e)}"}

    def _perform_automated_checks(self, execution_result: dict[str, Any]) -> dict[str, bool]:
        """执行自动化质量检查"""
        checks = {
            "has_result": bool(execution_result.get("result")),
            "no_error": not execution_result.get("error"),
            "result_not_empty": bool(execution_result.get("result")),
        }

        result = execution_result.get("result")
        if isinstance(result, str):
            checks["result_meaningful"] = len(result.strip()) > 10
        elif isinstance(result, dict):
            checks["result_meaningful"] = len(result) > 0
        elif isinstance(result, list):
            checks["result_meaningful"] = len(result) > 0
        else:
            checks["result_meaningful"] = result is not None

        return checks


class RoleFactory:
    """角色工厂"""

    def __init__(self):
        self.roles = {"analyst": AnalystRole, "executor": ExecutorRole, "reviewer": ReviewerRole}

    def create_role(self, role_type: str) -> Role | None:
        """创建角色"""
        try:
            if role_type in self.roles:
                return self.roles[role_type]()
            else:
                logger.warning(f"未知角色类型: {role_type}")
                return None
        except Exception as e:
            logger.error(f"创建角色失败: {str(e)}")
            return None

    def list_roles(self) -> list:
        """列出所有可用角色"""
        return list(self.roles.keys())

    def get_role_info(self, role_type: str) -> dict[str, Any] | None:
        """获取角色信息"""
        try:
            if role_type in self.roles:
                role_instance = self.roles[role_type]()
                return {
                    "role_type": role_instance.role_type,
                    "name": role_instance.name,
                    "description": role_instance.description,
                }
            else:
                return None
        except Exception as e:
            logger.error(f"获取角色信息失败: {str(e)}")
            return None
