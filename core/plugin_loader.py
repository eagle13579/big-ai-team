import importlib
import os
import sys

from core.plugin_interface import ChannelPlugin


class PluginLoader:
    """插件加载器"""
    
    def __init__(self, plugin_dir: str):
        """初始化插件加载器
        
        Args:
            plugin_dir: 插件目录
        """
        self.plugin_dir = plugin_dir
        self.plugins: dict[str, ChannelPlugin] = {}
        self._ensure_plugin_dir()
    
    def _ensure_plugin_dir(self):
        """确保插件目录存在"""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
        
        # 添加插件目录到Python路径
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)
    
    def load_plugins(self) -> list[str]:
        """加载所有插件
        
        Returns:
            List[str]: 加载的插件名称列表
        """
        loaded_plugins = []
        
        # 遍历插件目录
        for item in os.listdir(self.plugin_dir):
            item_path = os.path.join(self.plugin_dir, item)
            
            # 处理目录形式的插件
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "__init__.py")):
                plugin_name = item
                try:
                    plugin = self._load_plugin(plugin_name)
                    if plugin:
                        self.plugins[plugin_name] = plugin
                        loaded_plugins.append(plugin_name)
                except Exception as e:
                    print(f"加载插件 {plugin_name} 失败: {e}")
            
            # 处理单个文件形式的插件
            elif os.path.isfile(item_path) and item.endswith(".py") and not item.startswith("_"):
                plugin_name = item[:-3]  # 移除.py扩展名
                try:
                    plugin = self._load_plugin(plugin_name)
                    if plugin:
                        self.plugins[plugin_name] = plugin
                        loaded_plugins.append(plugin_name)
                except Exception as e:
                    print(f"加载插件 {plugin_name} 失败: {e}")
        
        return loaded_plugins
    
    def _load_plugin(self, plugin_name: str) -> ChannelPlugin | None:
        """加载单个插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[ChannelPlugin]: 加载的插件实例
        """
        try:
            # 导入插件模块
            module = importlib.import_module(plugin_name)
            
            # 查找插件类
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, ChannelPlugin) and obj != ChannelPlugin:
                    # 实例化插件
                    return obj()
            
            return None
        except Exception as e:
            print(f"加载插件 {plugin_name} 出错: {e}")
            return None
    
    def get_plugin(self, plugin_name: str) -> ChannelPlugin | None:
        """获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[ChannelPlugin]: 插件实例
        """
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> list[str]:
        """列出所有加载的插件
        
        Returns:
            List[str]: 插件名称列表
        """
        return list(self.plugins.keys())
    
    def reload_plugins(self) -> list[str]:
        """重新加载所有插件
        
        Returns:
            List[str]: 重新加载的插件名称列表
        """
        self.plugins.clear()
        return self.load_plugins()
