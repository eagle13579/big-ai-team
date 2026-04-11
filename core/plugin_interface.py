from abc import ABC, abstractmethod


class ChannelPlugin(ABC):
    """渠道插件接口"""
    
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
    
    @abstractmethod
    def initialize(self, config: dict) -> bool:
        """初始化插件
        
        Args:
            config: 插件配置
            
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def send_message(self, message: dict) -> bool:
        """发送消息
        
        Args:
            message: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
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
