import pytest

from src.execution.harness.tool_description import (
    ToolDescription,
    ToolParameter,
    ToolRiskLevel,
    ToolSideEffect,
    BUILTIN_TOOL_DESCRIPTIONS,
)
from src.execution.harness.assembler import AgentAssembler, _DANGEROUS_TOOLS


class TestToolDescription:

    def test_to_json_schema(self):
        desc = ToolDescription(
            name="test_tool",
            description="A test tool",
            parameters=[
                ToolParameter(name="query", type="string", description="Search query", required=True),
                ToolParameter(name="limit", type="integer", description="Max results", required=False),
            ],
            risk_level=ToolRiskLevel.SAFE,
        )
        schema = desc.to_json_schema()
        assert schema["name"] == "test_tool"
        assert "query" in schema["parameters"]["properties"]
        assert schema["parameters"]["required"] == ["query"]

    def test_to_prompt_description(self):
        desc = ToolDescription(
            name="calculator",
            description="Performs calculations",
            parameters=[ToolParameter(name="expr", type="string", description="Expression", required=True)],
            risk_level=ToolRiskLevel.SAFE,
        )
        prompt = desc.to_prompt_description()
        assert "calculator" in prompt
        assert "Performs calculations" in prompt

    def test_builtin_tools_exist(self):
        assert "web_search" in BUILTIN_TOOL_DESCRIPTIONS
        assert "file_ops" in BUILTIN_TOOL_DESCRIPTIONS
        assert "code_interpreter" in BUILTIN_TOOL_DESCRIPTIONS
        assert "calculator" in BUILTIN_TOOL_DESCRIPTIONS
        assert "git_helper" in BUILTIN_TOOL_DESCRIPTIONS
        assert "data_analyzer" in BUILTIN_TOOL_DESCRIPTIONS
        assert "file_manager" in BUILTIN_TOOL_DESCRIPTIONS


class TestAgentAssembler:

    @pytest.fixture
    def assembler(self):
        return AgentAssembler()

    def test_register_tool(self, assembler):
        desc = ToolDescription(
            name="custom_tool",
            description="Custom tool",
            parameters=[],
            risk_level=ToolRiskLevel.SAFE,
        )
        assembler.register_tool(desc)
        assert assembler.get_tool_description("custom_tool") is not None

    def test_unregister_tool(self, assembler):
        assembler.unregister_tool("web_search")
        assert assembler.get_tool_description("web_search") is None

    def test_list_tools(self, assembler):
        tools = assembler.list_tools()
        assert len(tools) > 0

    def test_get_tools_prompt(self, assembler):
        prompt = assembler.get_tools_prompt()
        assert len(prompt) > 0

    @pytest.mark.asyncio
    async def test_assemble_by_keywords(self, assembler):
        plan = await assembler.assemble("搜索最新的AI新闻")
        assert "steps" in plan
        assert any(s["tool"] == "web_search" for s in plan["steps"])

    @pytest.mark.asyncio
    async def test_assemble_calculator_keyword(self, assembler):
        plan = await assembler.assemble("计算 2+2 的结果")
        assert any(s["tool"] == "calculator" for s in plan["steps"])

    def test_dangerous_tools_set(self):
        assert "code_interpreter" in _DANGEROUS_TOOLS
        assert "file_manager" in _DANGEROUS_TOOLS
        assert "git_helper" in _DANGEROUS_TOOLS

    def test_check_permissions_dangerous_without_security(self, assembler):
        code_interpreter = BUILTIN_TOOL_DESCRIPTIONS.get("code_interpreter")
        if code_interpreter:
            result = assembler._check_permissions(code_interpreter, {})
            assert result["allowed"] is False

    def test_check_permissions_safe_without_security(self, assembler):
        calculator = BUILTIN_TOOL_DESCRIPTIONS.get("calculator")
        if calculator:
            result = assembler._check_permissions(calculator, {})
            assert result["allowed"] is True

    def test_get_assembly_history(self, assembler):
        assert isinstance(assembler.get_assembly_history(), list)
