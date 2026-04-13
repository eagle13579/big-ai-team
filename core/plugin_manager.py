import argparse
import json
import os
import sys
import importlib.util
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.plugin_interface import BasePlugin, PluginManagerInterface
from core.channel_manager import ChannelManager


class PluginManager(PluginManagerInterface):
    """插件管理器"""
    
    def __init__(self, plugin_dir: str = "channel_plugins"):
        """初始化插件管理器
        
        Args:
            plugin_dir: 插件目录
        """
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.plugin_status: Dict[str, str] = {}
        self.channel_manager = ChannelManager(plugin_dir)
    
    def load_plugin(self, plugin_path: str) -> bool:
        """加载插件
        
        Args:
            plugin_path: 插件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            # 检查路径是否存在
            if not os.path.exists(plugin_path):
                print(f"插件路径不存在: {plugin_path}")
                return False
            
            # 加载插件模块
            plugin_name = os.path.basename(plugin_path).replace(".py", "")
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None:
                print(f"无法创建插件模块规范: {plugin_path}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            for name, obj in module.__dict__.items():
                if isinstance(obj, type) and issubclass(obj, BasePlugin) and obj != BasePlugin:
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                print(f"插件中未找到 BasePlugin 子类: {plugin_path}")
                return False
            
            # 实例化插件
            plugin = plugin_class()
            self.plugins[plugin.name] = plugin
            self.plugin_status[plugin.name] = "loaded"
            
            print(f"成功加载插件: {plugin.name} v{plugin.version}")
            return True
            
        except Exception as e:
            print(f"加载插件失败: {str(e)}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 卸载是否成功
        """
        try:
            if plugin_name not in self.plugins:
                print(f"插件不存在: {plugin_name}")
                return False
            
            # 关闭插件
            plugin = self.plugins[plugin_name]
            if self.plugin_status.get(plugin_name) == "initialized":
                plugin.shutdown()
            
            # 从字典中移除
            del self.plugins[plugin_name]
            if plugin_name in self.plugin_configs:
                del self.plugin_configs[plugin_name]
            if plugin_name in self.plugin_status:
                del self.plugin_status[plugin_name]
            
            print(f"成功卸载插件: {plugin_name}")
            return True
            
        except Exception as e:
            print(f"卸载插件失败: {str(e)}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[BasePlugin]: 插件实例
        """
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有插件
        
        Returns:
            Dict[str, BasePlugin]: 插件字典
        """
        return self.plugins
    
    def initialize_all(self, config: Dict[str, Any]) -> bool:
        """初始化所有插件
        
        Args:
            config: 配置
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 先加载所有插件
            self._load_all_plugins()
            
            # 按依赖顺序初始化
            plugins_to_init = self._sort_plugins_by_dependency()
            
            success_count = 0
            for plugin_name in plugins_to_init:
                plugin = self.plugins[plugin_name]
                plugin_config = config.get(plugin_name, {})
                
                # 验证配置
                if not plugin.validate_config(plugin_config):
                    print(f"插件配置验证失败: {plugin_name}")
                    continue
                
                # 初始化插件
                if plugin.initialize(plugin_config):
                    self.plugin_status[plugin_name] = "initialized"
                    self.plugin_configs[plugin_name] = plugin_config
                    success_count += 1
                    print(f"成功初始化插件: {plugin_name}")
                else:
                    self.plugin_status[plugin_name] = "failed"
                    print(f"初始化插件失败: {plugin_name}")
            
            print(f"初始化完成，成功 {success_count} 个插件，失败 {len(plugins_to_init) - success_count} 个插件")
            return success_count > 0
            
        except Exception as e:
            print(f"初始化所有插件失败: {str(e)}")
            return False
    
    def shutdown_all(self) -> bool:
        """关闭所有插件
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            success_count = 0
            for plugin_name, plugin in self.plugins.items():
                if self.plugin_status.get(plugin_name) == "initialized":
                    if plugin.shutdown():
                        success_count += 1
                        print(f"成功关闭插件: {plugin_name}")
                    else:
                        print(f"关闭插件失败: {plugin_name}")
            
            print(f"关闭完成，成功 {success_count} 个插件")
            return success_count > 0
            
        except Exception as e:
            print(f"关闭所有插件失败: {str(e)}")
            return False
    
    def get_plugin_status(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件状态
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Dict[str, Any]: 状态信息
        """
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return {"status": "not_loaded", "plugin": plugin_name}
        
        status = {
            "status": self.plugin_status.get(plugin_name, "loaded"),
            "plugin": plugin_name,
            "version": plugin.version,
            "description": plugin.description,
            "author": plugin.author,
            "type": plugin.plugin_type
        }
        
        # 获取插件自身状态
        try:
            plugin_status = plugin.get_status()
            status.update(plugin_status)
        except Exception as e:
            status["error"] = str(e)
        
        return status
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        health_status = {
            "plugins_count": len(self.plugins),
            "initialized_count": sum(1 for status in self.plugin_status.values() if status == "initialized"),
            "plugins": {}
        }
        
        for plugin_name, plugin in self.plugins.items():
            try:
                health = plugin.get_health_check()
                health_status["plugins"][plugin_name] = health
            except Exception as e:
                health_status["plugins"][plugin_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status
    
    def _load_all_plugins(self):
        """加载所有插件"""
        if not os.path.exists(self.plugin_dir):
            print(f"插件目录不存在: {self.plugin_dir}")
            return
        
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                plugin_path = os.path.join(self.plugin_dir, filename)
                self.load_plugin(plugin_path)
    
    def _sort_plugins_by_dependency(self) -> List[str]:
        """按依赖顺序排序插件
        
        Returns:
            List[str]: 排序后的插件名称列表
        """
        # 构建依赖图
        dependency_graph = {}
        for plugin_name, plugin in self.plugins.items():
            dependencies = plugin.get_dependencies()
            dependency_graph[plugin_name] = dependencies
        
        # 拓扑排序
        visited = set()
        temp = set()
        result = []
        
        def visit(plugin_name):
            if plugin_name in temp:
                raise Exception(f"循环依赖: {plugin_name}")
            if plugin_name not in visited:
                temp.add(plugin_name)
                for dep in dependency_graph.get(plugin_name, []):
                    if dep in self.plugins:
                        visit(dep)
                temp.remove(plugin_name)
                visited.add(plugin_name)
                result.append(plugin_name)
        
        for plugin_name in self.plugins:
            if plugin_name not in visited:
                try:
                    visit(plugin_name)
                except Exception as e:
                    print(f"依赖排序失败: {str(e)}")
                    # 跳过有循环依赖的插件
                    continue
        
        return result
    
    def run(self, args):
        """运行命令
        
        Args:
            args: 命令行参数
        """
        if args.command not in ["load", "reload"]:
            self.initialize_all({})
        
        if args.command == "list":
            self.list_plugins()
        elif args.command == "load":
            self.load_all_plugins()
        elif args.command == "unload":
            self.unload_plugin(args.plugin)
        elif args.command == "status":
            if args.plugin:
                self.get_plugin_status(args.plugin)
            else:
                self.get_all_status()
        elif args.command == "health":
            self.get_health()
        elif args.command == "reload":
            self.reload_plugins()
        else:
            print(f"未知命令: {args.command}")
    
    def list_plugins(self):
        """列出所有插件"""
        plugins_info = []
        for plugin_name, plugin in self.plugins.items():
            info = {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "type": plugin.plugin_type,
                "status": self.plugin_status.get(plugin_name, "loaded")
            }
            plugins_info.append(info)
        print(json.dumps(plugins_info, indent=2, ensure_ascii=False))
    
    def load_all_plugins(self):
        """加载所有插件"""
        self._load_all_plugins()
        print(f"加载完成，共 {len(self.plugins)} 个插件")
    
    def get_all_status(self):
        """获取所有插件状态"""
        status_info = {}
        for plugin_name in self.plugins:
            status_info[plugin_name] = self.get_plugin_status(plugin_name)
        print(json.dumps(status_info, indent=2, ensure_ascii=False))
    
    def get_health(self):
        """获取健康状态"""
        health = self.get_health_status()
        print(json.dumps(health, indent=2, ensure_ascii=False))
    
    def reload_plugins(self):
        """重新加载插件"""
        # 先关闭所有插件
        self.shutdown_all()
        # 清空插件列表
        self.plugins.clear()
        self.plugin_configs.clear()
        self.plugin_status.clear()
        # 重新加载
        self._load_all_plugins()
        # 重新初始化
        self.initialize_all({})
        print("插件重新加载完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="插件管理工具")
    parser.add_argument("command", choices=["list", "load", "unload", "status", "health", "reload"],
                        help="命令")
    parser.add_argument("-p", "--plugin", help="插件名称")
    parser.add_argument("--plugin-dir", default="channel_plugins", help="插件目录")
    
    args = parser.parse_args()
    
    manager = PluginManager(args.plugin_dir)
    manager.run(args)


if __name__ == "__main__":
    main()