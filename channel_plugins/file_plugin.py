import os

from core.plugin_interface import ChannelPlugin


class FilePlugin(ChannelPlugin):
    """文件输出插件"""
    
    @property
    def name(self) -> str:
        return "File Channel"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "将消息写入文件"
    
    def initialize(self, config: dict) -> bool:
        self.config = config
        self.output_file = config.get("output_file", "messages.txt")
        # 确保输出目录存在
        output_dir = os.path.dirname(self.output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        print(f"初始化文件插件，输出文件: {self.output_file}")
        return True
    
    def send_message(self, message: dict) -> bool:
        try:
            with open(self.output_file, "a", encoding="utf-8") as f:
                f.write(str(message) + "\n")
            print(f"[文件] 消息已写入: {self.output_file}")
            return True
        except Exception as e:
            print(f"[文件] 写入失败: {e}")
            return False
    
    def get_status(self) -> dict:
        return {
            "status": "active",
            "output_file": self.output_file,
            "file_exists": os.path.exists(self.output_file),
            "file_size": os.path.getsize(self.output_file) if os.path.exists(self.output_file) else 0
        }
    
    def shutdown(self) -> bool:
        print("关闭文件插件")
        return True
