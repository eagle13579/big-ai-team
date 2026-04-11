
from core.plugin_interface import ChannelPlugin
from core.plugin_loader import PluginLoader


class ChannelManager:
    """渠道管理器"""
    
    def __init__(self, plugin_dir: str):
        """初始化渠道管理器
        
        Args:
            plugin_dir: 插件目录
        """
        self.plugin_loader = PluginLoader(plugin_dir)
        self.active_channels: dict[str, ChannelPlugin] = {}
    
    def load_channels(self) -> list[str]:
        """加载所有渠道
        
        Returns:
            List[str]: 加载的渠道名称列表
        """
        return self.plugin_loader.load_plugins()
    
    def activate_channel(self, channel_name: str, config: dict = None) -> bool:
        """激活渠道
        
        Args:
            channel_name: 渠道名称
            config: 渠道配置
            
        Returns:
            bool: 激活是否成功
        """
        plugin = self.plugin_loader.get_plugin(channel_name)
        if not plugin:
            return False
        
        try:
            if plugin.initialize(config or {}):
                self.active_channels[channel_name] = plugin
                return True
            return False
        except Exception as e:
            print(f"激活渠道 {channel_name} 失败: {e}")
            return False
    
    def deactivate_channel(self, channel_name: str) -> bool:
        """停用渠道
        
        Args:
            channel_name: 渠道名称
            
        Returns:
            bool: 停用是否成功
        """
        if channel_name not in self.active_channels:
            return False
        
        try:
            plugin = self.active_channels[channel_name]
            result = plugin.shutdown()
            if result:
                del self.active_channels[channel_name]
            return result
        except Exception as e:
            print(f"停用渠道 {channel_name} 失败: {e}")
            return False
    
    def send_message(self, channel_name: str, message: dict) -> bool:
        """发送消息到指定渠道
        
        Args:
            channel_name: 渠道名称
            message: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        if channel_name not in self.active_channels:
            return False
        
        try:
            return self.active_channels[channel_name].send_message(message)
        except Exception as e:
            print(f"发送消息到渠道 {channel_name} 失败: {e}")
            return False
    
    def get_channel_status(self, channel_name: str) -> dict | None:
        """获取渠道状态
        
        Args:
            channel_name: 渠道名称
            
        Returns:
            Optional[dict]: 状态信息
        """
        if channel_name not in self.active_channels:
            return None
        
        try:
            return self.active_channels[channel_name].get_status()
        except Exception as e:
            print(f"获取渠道 {channel_name} 状态失败: {e}")
            return None
    
    def list_channels(self) -> dict[str, dict]:
        """列出所有渠道及其状态
        
        Returns:
            Dict[str, dict]: 渠道信息字典
        """
        channels = {}
        
        # 所有加载的插件
        for plugin_name in self.plugin_loader.list_plugins():
            plugin = self.plugin_loader.get_plugin(plugin_name)
            if plugin:
                is_active = plugin_name in self.active_channels
                channels[plugin_name] = {
                    "name": plugin.name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "active": is_active,
                    "status": self.get_channel_status(plugin_name) if is_active else None
                }
        
        return channels
    
    def reload_channels(self) -> list[str]:
        """重新加载所有渠道
        
        Returns:
            List[str]: 重新加载的渠道名称列表
        """
        # 先停用所有活跃渠道
        for channel_name in list(self.active_channels.keys()):
            self.deactivate_channel(channel_name)
        
        # 重新加载插件
        return self.plugin_loader.reload_plugins()
