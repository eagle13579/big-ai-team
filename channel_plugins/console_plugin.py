from core.plugin_interface import ChannelPlugin


class ConsolePlugin(ChannelPlugin):
    """控制台输出插件"""
    
    @property
    def name(self) -> str:
        return "Console Channel"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "将消息输出到控制台"
    
    def initialize(self, config: dict) -> bool:
        print(f"初始化控制台插件，配置: {config}")
        self.config = config
        return True
    
    def send_message(self, message: dict) -> bool:
        print(f"[控制台] 发送消息: {message}")
        return True
    
    def get_status(self) -> dict:
        return {
            "status": "active",
            "config": self.config,
            "messages_sent": 0
        }
    
    def shutdown(self) -> bool:
        print("关闭控制台插件")
        return True
