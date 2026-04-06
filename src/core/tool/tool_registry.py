import importlib
import pkgutil
import os
from typing import Dict, List, Type
from .base import BaseTool
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表，负责自动发现和注册工具
    """
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.tool_classes: Dict[str, Type[BaseTool]] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """
        注册单个工具实例
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def register_tool_class(self, tool_class: Type[BaseTool]) -> None:
        """
        注册工具类
        """
        self.tool_classes[tool_class.name] = tool_class
        logger.info(f"Registered tool class: {tool_class.name}")

    def get_tool(self, name: str) -> BaseTool:
        """
        根据名称获取工具实例
        """
        if name not in self.tools:
            # 如果工具实例不存在，尝试从工具类创建
            if name in self.tool_classes:
                tool_instance = self.tool_classes[name]()
                self.tools[name] = tool_instance
                logger.info(f"Created tool instance: {name}")
            else:
                raise ValueError(f"Tool {name} not found")
        return self.tools[name]

    def get_all_tools(self) -> List[BaseTool]:
        """
        获取所有工具实例
        """
        # 确保所有工具类都已实例化
        for name, tool_class in self.tool_classes.items():
            if name not in self.tools:
                self.tools[name] = tool_class()
        return list(self.tools.values())

    def discover_tools(self, package_path: str) -> None:
        """
        自动发现并注册指定包路径下的所有工具
        """
        try:
            # 转换为模块路径
            package_name = package_path.replace(os.path.sep, '.')
            package = importlib.import_module(package_name)
            
            # 遍历包内所有模块
            for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
                if is_pkg:
                    continue
                
                module_full_name = f"{package_name}.{module_name}"
                module = importlib.import_module(module_full_name)
                
                # 查找模块中的 BaseTool 子类
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    try:
                        if (
                            isinstance(item, type) and 
                            issubclass(item, BaseTool) and 
                            item != BaseTool and
                            hasattr(item, 'name') and
                            hasattr(item, 'description') and
                            hasattr(item, 'args_schema')
                        ):
                            self.register_tool_class(item)
                    except TypeError:
                        continue
            
            logger.info(f"Discovered tools in {package_path}: {list(self.tool_classes.keys())}")
        except Exception as e:
            logger.error(f"Error discovering tools: {str(e)}")


# 创建全局工具注册表实例
tool_registry = ToolRegistry()