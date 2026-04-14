from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ToolRiskLevel(str, Enum):
    SAFE = "safe"
    MODERATE = "moderate"
    DANGEROUS = "dangerous"


class ToolSideEffect(str, Enum):
    NONE = "none"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    NETWORK_CALL = "network_call"
    SYSTEM_COMMAND = "system_command"
    DATABASE_WRITE = "database_write"


@dataclass
class ToolParameter:
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDescription:
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    return_type: str = "str"
    side_effects: list[ToolSideEffect] = field(default_factory=list)
    risk_level: ToolRiskLevel = ToolRiskLevel.SAFE
    required_permissions: list[str] = field(default_factory=list)
    examples: list[dict[str, Any]] = field(default_factory=list)
    category: str = "general"

    def to_json_schema(self) -> dict[str, Any]:
        """转换为 JSON Schema 格式（供 LLM 理解）"""
        properties = {}
        required = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
            "returns": {"type": self.return_type},
            "side_effects": [e.value for e in self.side_effects],
            "risk_level": self.risk_level.value,
            "required_permissions": self.required_permissions,
            "category": self.category,
        }

    def to_prompt_description(self) -> str:
        """转换为 Prompt 友好的文本描述"""
        params_desc = []
        for p in self.parameters:
            req = "必填" if p.required else "可选"
            enum_str = f", 可选值: {p.enum}" if p.enum else ""
            default_str = f", 默认: {p.default}" if p.default is not None else ""
            params_desc.append(f"  - {p.name} ({p.type}, {req}): {p.description}{enum_str}{default_str}")

        side_effects_str = ", ".join(e.value for e in self.side_effects) if self.side_effects else "无"
        risk_str = self.risk_level.value

        return (
            f"工具: {self.name}\n"
            f"描述: {self.description}\n"
            f"参数:\n{''.join(params_desc)}\n"
            f"返回类型: {self.return_type}\n"
            f"副作用: {side_effects_str}\n"
            f"风险等级: {risk_str}\n"
            f"所需权限: {', '.join(self.required_permissions) or '无'}\n"
            f"分类: {self.category}"
        )


BUILTIN_TOOL_DESCRIPTIONS: dict[str, ToolDescription] = {
    "web_search": ToolDescription(
        name="web_search",
        description="搜索互联网获取信息",
        parameters=[
            ToolParameter(name="query", type="string", description="搜索查询关键词"),
        ],
        return_type="str",
        side_effects=[ToolSideEffect.NETWORK_CALL],
        risk_level=ToolRiskLevel.SAFE,
        category="search",
    ),
    "file_ops": ToolDescription(
        name="file_ops",
        description="文件操作工具，支持读写删除等操作",
        parameters=[
            ToolParameter(name="operation", type="string", description="操作类型", enum=["read", "write", "delete", "list", "exists"]),
            ToolParameter(name="path", type="string", description="文件路径"),
            ToolParameter(name="content", type="string", description="写入内容（仅write操作）", required=False),
        ],
        return_type="str",
        side_effects=[ToolSideEffect.FILE_WRITE, ToolSideEffect.FILE_DELETE],
        risk_level=ToolRiskLevel.MODERATE,
        required_permissions=["file_access"],
        category="file",
    ),
    "code_interpreter": ToolDescription(
        name="code_interpreter",
        description="执行Python代码并返回结果",
        parameters=[
            ToolParameter(name="code", type="string", description="要执行的Python代码"),
        ],
        return_type="str",
        side_effects=[ToolSideEffect.SYSTEM_COMMAND],
        risk_level=ToolRiskLevel.DANGEROUS,
        required_permissions=["code_execution"],
        category="execution",
    ),
    "calculator": ToolDescription(
        name="calculator",
        description="数学计算工具",
        parameters=[
            ToolParameter(name="expression", type="string", description="数学表达式"),
        ],
        return_type="float",
        side_effects=[ToolSideEffect.NONE],
        risk_level=ToolRiskLevel.SAFE,
        category="math",
    ),
    "git_helper": ToolDescription(
        name="git_helper",
        description="Git版本控制工具",
        parameters=[
            ToolParameter(name="action", type="string", description="Git操作类型", enum=["status", "log", "diff", "add", "commit", "push", "pull", "branch", "checkout"]),
            ToolParameter(name="args", type="object", description="操作参数", required=False),
        ],
        return_type="str",
        side_effects=[ToolSideEffect.FILE_WRITE, ToolSideEffect.NETWORK_CALL],
        risk_level=ToolRiskLevel.MODERATE,
        required_permissions=["git_access"],
        category="vcs",
    ),
    "data_analyzer": ToolDescription(
        name="data_analyzer",
        description="数据分析工具，支持CSV/JSON数据分析",
        parameters=[
            ToolParameter(name="data_path", type="string", description="数据文件路径"),
            ToolParameter(name="analysis_type", type="string", description="分析类型", enum=["basic", "correlation", "trend"], required=False),
        ],
        return_type="str",
        side_effects=[ToolSideEffect.NONE],
        risk_level=ToolRiskLevel.SAFE,
        category="analysis",
    ),
    "file_manager": ToolDescription(
        name="file_manager",
        description="文件管理工具，支持文件搜索、复制、移动等",
        parameters=[
            ToolParameter(name="operation", type="string", description="操作类型", enum=["search", "copy", "move", "rename", "info", "tree"]),
            ToolParameter(name="path", type="string", description="文件或目录路径"),
            ToolParameter(name="destination", type="string", description="目标路径（copy/move操作）", required=False),
        ],
        return_type="str",
        side_effects=[ToolSideEffect.FILE_WRITE],
        risk_level=ToolRiskLevel.MODERATE,
        required_permissions=["file_access"],
        category="file",
    ),
}
