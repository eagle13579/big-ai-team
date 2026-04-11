import argparse
import json
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.channel_manager import ChannelManager


class PluginManager:
    """插件管理工具"""
    
    def __init__(self, plugin_dir: str):
        """初始化插件管理工具
        
        Args:
            plugin_dir: 插件目录
        """
        self.channel_manager = ChannelManager(plugin_dir)
    
    def run(self, args):
        """运行命令
        
        Args:
            args: 命令行参数
        """
        # 除了load和reload命令外，其他命令都需要先加载插件
        if args.command not in ["load", "reload"]:
            self.channel_manager.load_channels()
        
        if args.command == "list":
            self.list_channels()
        elif args.command == "load":
            self.load_channels()
        elif args.command == "activate":
            self.activate_channel(args.channel, args.config)
        elif args.command == "deactivate":
            self.deactivate_channel(args.channel)
        elif args.command == "send":
            self.send_message(args.channel, args.message)
        elif args.command == "status":
            self.get_channel_status(args.channel)
        elif args.command == "reload":
            self.reload_channels()
        else:
            print(f"未知命令: {args.command}")
    
    def list_channels(self):
        """列出所有渠道"""
        channels = self.channel_manager.list_channels()
        print(json.dumps(channels, indent=2, ensure_ascii=False))
    
    def load_channels(self):
        """加载所有渠道"""
        loaded = self.channel_manager.load_channels()
        print(f"加载了 {len(loaded)} 个渠道: {', '.join(loaded)}")
    
    def activate_channel(self, channel_name: str, config: str = None):
        """激活渠道"""
        config_dict = {} if config is None else json.loads(config)
        result = self.channel_manager.activate_channel(channel_name, config_dict)
        if result:
            print(f"渠道 {channel_name} 激活成功")
        else:
            print(f"渠道 {channel_name} 激活失败")
    
    def deactivate_channel(self, channel_name: str):
        """停用渠道"""
        result = self.channel_manager.deactivate_channel(channel_name)
        if result:
            print(f"渠道 {channel_name} 停用成功")
        else:
            print(f"渠道 {channel_name} 停用失败")
    
    def send_message(self, channel_name: str, message: str):
        """发送消息"""
        message_dict = json.loads(message)
        result = self.channel_manager.send_message(channel_name, message_dict)
        if result:
            print("消息发送成功")
        else:
            print("消息发送失败")
    
    def get_channel_status(self, channel_name: str):
        """获取渠道状态"""
        status = self.channel_manager.get_channel_status(channel_name)
        if status:
            print(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            print(f"渠道 {channel_name} 未激活或获取状态失败")
    
    def reload_channels(self):
        """重新加载渠道"""
        reloaded = self.channel_manager.reload_channels()
        print(f"重新加载了 {len(reloaded)} 个渠道: {', '.join(reloaded)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="渠道插件管理工具")
    parser.add_argument("command", choices=["list", "load", "activate", "deactivate", "send", "status", "reload"],
                        help="命令")
    parser.add_argument("-c", "--channel", help="渠道名称")
    parser.add_argument("-m", "--message", help="消息内容 (JSON格式)")
    parser.add_argument("--config", help="渠道配置 (JSON格式)")
    parser.add_argument("--plugin-dir", default="channel_plugins", help="插件目录")
    
    args = parser.parse_args()
    
    # 检查必要参数
    if args.command in ["activate", "deactivate", "send", "status"] and not args.channel:
        parser.error(f"命令 {args.command} 需要指定渠道名称")
    
    if args.command == "send" and not args.message:
        parser.error("命令 send 需要指定消息内容")
    
    manager = PluginManager(args.plugin_dir)
    manager.run(args)


if __name__ == "__main__":
    main()
