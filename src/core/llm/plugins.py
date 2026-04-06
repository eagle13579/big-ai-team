import importlib
import pkgutil
import os
from typing import Dict, Any, List, Type
from .logger import logger


class Plugin:
    """插件基类"""
    
    name: str = ""
    version: str = ""
    description: str = ""
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        return True
    
    def shutdown(self) -> bool:
        """关闭插件"""
        return True


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_dirs: List[str] = []
    
    def add_plugin_dir(self, plugin_dir: str):
        """添加插件目录"""
        if os.path.exists(plugin_dir) and plugin_dir not in self.plugin_dirs:
            self.plugin_dirs.append(plugin_dir)
            logger.debug(f"Added plugin directory: {plugin_dir}")
    
    def load_plugins(self, config: Dict[str, Any] = None):
        """加载插件"""
        config = config or {}
        
        for plugin_dir in self.plugin_dirs:
            for _, plugin_name, is_pkg in pkgutil.iter_modules([plugin_dir]):
                if is_pkg:
                    try:
                        module_path = f"{plugin_dir.replace(os.path.sep, '.')}.{plugin_name}"
                        module = importlib.import_module(module_path)
                        
                        # 查找插件类
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, type) and issubclass(attr, Plugin) and attr != Plugin:
                                plugin_instance = attr()
                                if plugin_instance.initialize(config.get(plugin_instance.name, {})):
                                    self.plugins[plugin_instance.name] = plugin_instance
                                    logger.info(f"Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")
                                else:
                                    logger.warning(f"Failed to initialize plugin: {plugin_instance.name}")
                    except Exception as e:
                        logger.error(f"Error loading plugin {plugin_name}: {e}")
    
    def get_plugin(self, name: str) -> Plugin:
        """获取插件"""
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> List[Plugin]:
        """获取所有插件"""
        return list(self.plugins.values())
    
    def unload_plugin(self, name: str):
        """卸载插件"""
        if name in self.plugins:
            plugin = self.plugins[name]
            if plugin.shutdown():
                del self.plugins[name]
                logger.info(f"Unloaded plugin: {name}")
            else:
                logger.warning(f"Failed to shutdown plugin: {name}")
    
    def unload_all_plugins(self):
        """卸载所有插件"""
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)


# 全局插件管理器实例
plugin_manager = PluginManager()
