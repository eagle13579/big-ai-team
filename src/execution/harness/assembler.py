import json
from typing import Any

from src.execution.harness.tool_description import (
    BUILTIN_TOOL_DESCRIPTIONS,
    ToolDescription,
    ToolRiskLevel,
    ToolSideEffect,
)
from src.shared.logging import logger


_DANGEROUS_TOOLS = {"code_interpreter", "file_manager", "git_helper"}


class AgentAssembler:
    """
    智能体装配器 - 根据 LLM 输出自动选择和装配工具链
    灵感来自 claw-code 的 Agent Harness 机制
    """

    def __init__(self, executor=None, llm_client=None, security_manager=None):
        self._executor = executor
        self._llm_client = llm_client
        self._security_manager = security_manager
        self._tool_registry: dict[str, ToolDescription] = dict(BUILTIN_TOOL_DESCRIPTIONS)
        self._assembly_history: list[dict[str, Any]] = []

    def register_tool(self, description: ToolDescription):
        """注册工具描述"""
        self._tool_registry[description.name] = description
        logger.info(f"🔧 注册工具: {description.name} (风险: {description.risk_level.value})")

    def unregister_tool(self, name: str):
        """注销工具"""
        if name in self._tool_registry:
            del self._tool_registry[name]

    def get_tool_description(self, name: str) -> ToolDescription | None:
        """获取工具描述"""
        return self._tool_registry.get(name)

    def list_tools(self, category: str | None = None) -> list[ToolDescription]:
        """列出所有可用工具"""
        tools = list(self._tool_registry.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def get_tools_prompt(self) -> str:
        """生成供 LLM 使用的工具列表描述"""
        descriptions = []
        for tool in self._tool_registry.values():
            descriptions.append(tool.to_prompt_description())
        return "\n\n".join(descriptions)

    async def assemble(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        根据任务描述自动装配工具链并生成执行计划
        """
        logger.info(f"🛠️ 开始装配任务: {task}")

        if self._llm_client is None:
            return self._assemble_by_keywords(task, context)

        try:
            assembly_prompt = self._build_assembly_prompt(task, context)
            raw_response = await self._llm_client.generate(assembly_prompt, temperature=0.2)
            plan = self._parse_assembly_response(raw_response, task)

            self._assembly_history.append({
                "task": task,
                "plan": plan,
                "method": "llm",
            })

            logger.info(f"🛠️ LLM 装配完成，工具链: {[s['tool'] for s in plan.get('steps', [])]}")
            return plan

        except Exception as e:
            logger.error(f"❌ LLM 装配失败: {e}，回退到关键词装配")
            return self._assemble_by_keywords(task, context)

    async def execute_assembly(self, plan: dict[str, Any]) -> dict[str, Any]:
        """
        执行装配计划
        """
        if self._executor is None:
            return {"status": "error", "message": "执行器未初始化"}

        steps = plan.get("steps", [])
        results = []
        context_log = ""

        for i, step in enumerate(steps):
            tool_name = step.get("tool")
            tool_args = step.get("args", {})

            tool_desc = self._tool_registry.get(tool_name)
            if tool_desc is None:
                results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "status": "error",
                    "error": f"工具 {tool_name} 未注册",
                })
                continue

            permission_check = self._check_permissions(tool_desc, tool_args)
            if not permission_check["allowed"]:
                results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "status": "error",
                    "error": f"权限不足: {permission_check['reason']}",
                })
                continue

            try:
                result = await self._executor.execute(tool_name, tool_args)
                results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "status": "success" if result.get("success") else "failed",
                    "result": result.get("result") if result.get("success") else None,
                    "error": result.get("error") if not result.get("success") else None,
                })
                context_log += f"步骤{i+1}: {tool_name} -> {'成功' if result.get('success') else '失败'}\n"

            except Exception as e:
                results.append({
                    "step": i + 1,
                    "tool": tool_name,
                    "status": "error",
                    "error": str(e),
                })
                context_log += f"步骤{i+1}: {tool_name} -> 异常: {e}\n"

        all_success = all(r.get("status") == "success" for r in results)
        return {
            "status": "success" if all_success else "partial",
            "steps": results,
            "context_log": context_log,
            "total_steps": len(steps),
            "successful_steps": sum(1 for r in results if r.get("status") == "success"),
        }

    def _build_assembly_prompt(self, task: str, context: dict[str, Any] | None) -> str:
        """构建装配 Prompt"""
        tools_prompt = self.get_tools_prompt()
        context_str = json.dumps(context, ensure_ascii=False, indent=2) if context else "无"

        return f"""你是一个智能任务装配器。根据用户任务，从可用工具中选择合适的工具链，生成执行计划。

用户任务: {task}

上下文信息: {context_str}

可用工具:
{tools_prompt}

请严格按照以下 JSON 格式输出执行计划（不要输出任何其他内容）:
{{
    "analysis": "任务分析",
    "steps": [
        {{
            "tool": "工具名称",
            "args": {{}},
            "purpose": "使用该工具的目的"
        }}
    ],
    "expected_outcome": "预期结果"
}}

执行计划:"""

    def _parse_assembly_response(self, raw_response: str, task: str) -> dict[str, Any]:
        """解析装配响应"""
        import re

        json_match = re.search(r'\{[\s\S]*\}', raw_response)
        if json_match:
            try:
                plan = json.loads(json_match.group())
                if "steps" in plan:
                    for step in plan["steps"]:
                        if "tool" not in step:
                            step["tool"] = "unknown"
                        if "args" not in step:
                            step["args"] = {}
                    return plan
            except json.JSONDecodeError:
                pass

        logger.warning("⚠️ LLM 返回非结构化装配响应，使用关键词装配")
        return self._assemble_by_keywords(task)

    def _assemble_by_keywords(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """基于关键词的装配（回退方案）"""
        steps = []

        if any(kw in task for kw in ["搜索", "查找", "调研", "了解", "search"]):
            steps.append({"tool": "web_search", "args": {"query": task}, "purpose": "搜索相关信息"})

        if any(kw in task for kw in ["分析", "统计", "数据", "analyze"]):
            steps.append({"tool": "data_analyzer", "args": {"data_path": ""}, "purpose": "分析数据"})

        if any(kw in task for kw in ["计算", "数学", "算", "calculate"]):
            steps.append({"tool": "calculator", "args": {"expression": task}, "purpose": "执行计算"})

        if any(kw in task for kw in ["代码", "编程", "运行", "code", "python"]):
            steps.append({"tool": "code_interpreter", "args": {"code": ""}, "purpose": "执行代码"})

        if any(kw in task for kw in ["文件", "读写", "file"]):
            steps.append({"tool": "file_ops", "args": {"operation": "read", "path": ""}, "purpose": "文件操作"})

        if any(kw in task for kw in ["git", "提交", "分支", "commit"]):
            steps.append({"tool": "git_helper", "args": {"action": "status"}, "purpose": "Git操作"})

        if not steps:
            steps.append({"tool": "web_search", "args": {"query": task}, "purpose": "默认搜索"})

        self._assembly_history.append({
            "task": task,
            "plan": {"analysis": "关键词装配", "steps": steps, "expected_outcome": "完成用户任务"},
            "method": "keyword",
        })

        return {
            "analysis": f"基于关键词为任务 '{task}' 装配工具链",
            "steps": steps,
            "expected_outcome": "完成用户请求的任务",
        }

    def _check_permissions(self, tool_desc: ToolDescription, args: dict[str, Any]) -> dict[str, Any]:
        """检查工具执行权限 — 默认拒绝危险工具 (Deny by Default)"""
        if tool_desc.risk_level == ToolRiskLevel.DANGEROUS:
            if self._security_manager is None:
                if tool_desc.name in _DANGEROUS_TOOLS:
                    return {"allowed": False, "reason": f"危险工具 {tool_desc.name} 需要安全管理器授权"}
            else:
                try:
                    allowed = self._security_manager.check_permission("execute_dangerous_tool", tool_desc.name)
                    if not allowed:
                        return {"allowed": False, "reason": f"危险工具 {tool_desc.name} 需要授权"}
                except Exception as e:
                    logger.error(f"❌ 权限检查异常，默认拒绝: {e}")
                    return {"allowed": False, "reason": f"权限检查失败: {e}"}

        if ToolSideEffect.FILE_DELETE in tool_desc.side_effects:
            if self._security_manager is None:
                return {"allowed": False, "reason": "文件删除操作需要安全管理器授权"}
            try:
                path = args.get("path", "")
                allowed = self._security_manager.validate_file_path(path)
                if not allowed:
                    return {"allowed": False, "reason": f"文件路径 {path} 受保护"}
            except Exception as e:
                logger.error(f"❌ 文件路径验证异常，默认拒绝: {e}")
                return {"allowed": False, "reason": f"路径验证失败: {e}"}

        return {"allowed": True, "reason": ""}

    def get_assembly_history(self) -> list[dict[str, Any]]:
        """获取装配历史"""
        return list(self._assembly_history)
