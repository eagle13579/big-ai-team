from typing import Dict, List, Optional, Any, Protocol
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolVersion(BaseModel):
    """
    工具版本模型
    """
    version: str
    tool_class: Any
    is_active: bool = True


class ToolWithVersion(BaseModel):
    """
    带版本的工具模型
    """
    name: str
    versions: Dict[str, ToolVersion]
    default_version: str


class ToolDependency(BaseModel):
    """
    工具依赖模型
    """
    tool_name: str
    version: Optional[str] = None
    required: bool = True


class ToolContext(BaseModel):
    """
    工具执行上下文
    """
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tool_chain: List[str] = Field(default_factory=list)  # 工具调用链


class LLMProtocolFactory:
    """
    LLM 协议工厂，用于创建不同的 LLM 协议实例
    """
    def __init__(self):
        self.protocols: Dict[str, Any] = {}

    def register_protocol(self, name: str, protocol_class: Any):
        """
        注册 LLM 协议
        
        Args:
            name: 协议名称
            protocol_class: 协议类
        """
        self.protocols[name] = protocol_class
        logger.info(f"Registered LLM protocol: {name}")

    def create_protocol(self, name: str, **kwargs) -> Any:
        """
        创建 LLM 协议实例
        
        Args:
            name: 协议名称
            **kwargs: 协议参数
            
        Returns:
            Any: 协议实例
        """
        if name not in self.protocols:
            raise ValueError(f"LLM protocol {name} not found")
        return self.protocols[name](**kwargs)


class EnhancedToolRegistry:
    """
    增强的工具注册表，支持版本管理和依赖管理
    """
    def __init__(self):
        self.tools: Dict[str, ToolWithVersion] = {}
        self.dependencies: Dict[str, List[ToolDependency]] = {}

    def register_tool(self, tool_class: Any, version: str = "1.0.0", is_default: bool = False):
        """
        注册工具（支持版本）
        
        Args:
            tool_class: 工具类
            version: 工具版本
            is_default: 是否为默认版本
        """
        tool_name = tool_class.name
        
        if tool_name not in self.tools:
            self.tools[tool_name] = ToolWithVersion(
                name=tool_name,
                versions={},
                default_version=version
            )
        
        tool_version = ToolVersion(
            version=version,
            tool_class=tool_class,
            is_active=True
        )
        
        self.tools[tool_name].versions[version] = tool_version
        
        if is_default:
            self.tools[tool_name].default_version = version
        
        logger.info(f"Registered tool {tool_name} version {version}")

    def get_tool(self, name: str, version: Optional[str] = None) -> Any:
        """
        获取工具实例（支持版本）
        
        Args:
            name: 工具名称
            version: 工具版本，None 表示使用默认版本
            
        Returns:
            Any: 工具实例
        """
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        
        tool_info = self.tools[name]
        target_version = version or tool_info.default_version
        
        if target_version not in tool_info.versions:
            raise ValueError(f"Version {target_version} for tool {name} not found")
        
        tool_version = tool_info.versions[target_version]
        if not tool_version.is_active:
            raise ValueError(f"Version {target_version} for tool {name} is not active")
        
        # 检查依赖
        self._check_dependencies(name, target_version)
        
        # 创建工具实例
        return tool_version.tool_class()

    def register_dependency(self, tool_name: str, dependency: ToolDependency):
        """
        注册工具依赖
        
        Args:
            tool_name: 工具名称
            dependency: 依赖项
        """
        if tool_name not in self.dependencies:
            self.dependencies[tool_name] = []
        
        self.dependencies[tool_name].append(dependency)
        logger.info(f"Registered dependency for tool {tool_name}: {dependency.tool_name}")

    def _check_dependencies(self, tool_name: str, version: str):
        """
        检查工具依赖
        
        Args:
            tool_name: 工具名称
            version: 工具版本
        """
        if tool_name not in self.dependencies:
            return
        
        for dependency in self.dependencies[tool_name]:
            if dependency.tool_name not in self.tools:
                if dependency.required:
                    raise ValueError(f"Required dependency {dependency.tool_name} for tool {tool_name} not found")
                else:
                    logger.warning(f"Optional dependency {dependency.tool_name} for tool {tool_name} not found")
            else:
                dep_tool = self.tools[dependency.tool_name]
                dep_version = dependency.version or dep_tool.default_version
                if dep_version not in dep_tool.versions:
                    if dependency.required:
                        raise ValueError(f"Required dependency {dependency.tool_name} version {dep_version} not found")
                    else:
                        logger.warning(f"Optional dependency {dependency.tool_name} version {dep_version} not found")

    def get_all_tools(self) -> List[Any]:
        """
        获取所有工具实例（使用默认版本）
        
        Returns:
            List[Any]: 工具实例列表
        """
        tools = []
        for tool_info in self.tools.values():
            try:
                tool = self.get_tool(tool_info.name)
                tools.append(tool)
            except Exception as e:
                logger.error(f"Error getting tool {tool_info.name}: {e}")
        return tools


class ToolChainExecutor:
    """
    工具链执行器，支持多工具协作
    """
    def __init__(self, tool_registry: EnhancedToolRegistry):
        self.tool_registry = tool_registry

    async def execute_chain(self, chain: List[Dict[str, Any]], context: Optional[ToolContext] = None) -> Dict[str, Any]:
        """
        执行工具链
        
        Args:
            chain: 工具链配置
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        if not chain:
            return {"success": False, "error": "Empty tool chain"}
        
        context = context or ToolContext()
        results = {}
        
        for step in chain:
            tool_name = step.get("tool")
            params = step.get("params", {})
            version = step.get("version")
            
            if not tool_name:
                return {"success": False, "error": "Tool name not specified"}
            
            try:
                # 获取工具实例
                tool = self.tool_registry.get_tool(tool_name, version)
                
                # 更新工具调用链
                context.tool_chain.append(tool_name)
                
                # 执行工具
                result = await tool._execute_with_validation(**params)
                results[tool_name] = result.dict()
                
                # 如果执行失败，终止链
                if not result.success:
                    return {
                        "success": False,
                        "error": f"Tool {tool_name} failed: {result.error}",
                        "results": results
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error executing tool {tool_name}: {str(e)}",
                    "results": results
                }
        
        return {
            "success": True,
            "results": results,
            "tool_chain": context.tool_chain
        }


# 创建全局实例
llm_protocol_factory = LLMProtocolFactory()
enhanced_tool_registry = EnhancedToolRegistry()
tool_chain_executor = ToolChainExecutor(enhanced_tool_registry)