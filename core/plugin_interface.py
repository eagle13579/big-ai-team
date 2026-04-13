from abc import ABC, abstractmethod
from typing import Any


class BasePlugin(ABC):
    """基础插件接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass
    
    @property
    @abstractmethod
    def author(self) -> str:
        """插件作者"""
        pass
    
    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """插件类型"""
        pass
    
    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> bool:
        """初始化插件
        
        Args:
            config: 插件配置
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """获取插件状态
        
        Returns:
            dict: 状态信息
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """关闭插件
        
        Returns:
            bool: 关闭是否成功
        """
        pass
    
    def get_dependencies(self) -> list[str]:
        """获取插件依赖
        
        Returns:
            List[str]: 依赖插件列表
        """
        return []
    
    def get_config_schema(self) -> dict[str, Any]:
        """获取配置 schema
        
        Returns:
            Dict[str, Any]: 配置 schema
        """
        return {}
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """验证配置
        
        Args:
            config: 配置
            
        Returns:
            bool: 配置是否有效
        """
        return True
    
    def get_health_check(self) -> dict[str, Any]:
        """健康检查
        
        Returns:
            Dict[str, Any]: 健康检查结果
        """
        return {
            "status": "healthy",
            "plugin": self.name,
            "version": self.version
        }


class ChannelPlugin(BasePlugin):
    """渠道插件接口"""
    
    @property
    def plugin_type(self) -> str:
        return "channel"
    
    @abstractmethod
    def send_message(self, message: dict[str, Any]) -> bool:
        """发送消息
        
        Args:
            message: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    def receive_message(self) -> dict[str, Any] | None:
        """接收消息
        
        Returns:
            Optional[Dict[str, Any]]: 消息内容
        """
        pass


class ToolPlugin(BasePlugin):
    """工具插件接口"""
    
    @property
    def plugin_type(self) -> str:
        return "tool"
    
    @abstractmethod
    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """执行工具操作
        
        Args:
            args: 操作参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass
    
    def get_parameters(self) -> dict[str, Any]:
        """获取参数定义
        
        Returns:
            Dict[str, Any]: 参数定义
        """
        return {}


class IntegrationPlugin(BasePlugin):
    """集成插件接口"""
    
    @property
    def plugin_type(self) -> str:
        return "integration"
    
    @abstractmethod
    def connect(self) -> bool:
        """建立连接
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接
        
        Returns:
            bool: 断开是否成功
        """
        pass


class PluginManagerInterface(ABC):
    """插件管理器接口"""
    
    @abstractmethod
    def load_plugin(self, plugin_path: str) -> bool:
        """加载插件
        
        Args:
            plugin_path: 插件路径
            
        Returns:
            bool: 加载是否成功
        """
        pass
    
    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 卸载是否成功
        """
        pass
    
    @abstractmethod
    def get_plugin(self, plugin_name: str) -> BasePlugin | None:
        """获取插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[BasePlugin]: 插件实例
        """
        pass
    
    @abstractmethod
    def get_all_plugins(self) -> dict[str, BasePlugin]:
        """获取所有插件
        
        Returns:
            Dict[str, BasePlugin]: 插件字典
        """
        pass
    
    @abstractmethod
    def initialize_all(self, config: dict[str, Any]) -> bool:
        """初始化所有插件
        
        Args:
            config: 配置
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def shutdown_all(self) -> bool:
        """关闭所有插件
        
        Returns:
            bool: 关闭是否成功
        """
        pass
    
    @abstractmethod
    def get_plugin_status(self, plugin_name: str) -> dict[str, Any]:
        """获取插件状态
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Dict[str, Any]: 状态信息
        """
        pass
    
    @abstractmethod
    def get_health_status(self) -> dict[str, Any]:
        """获取健康状态
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        pass
