import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.channel_manager import ChannelManager


def test_system():
    """测试整个系统功能"""
    print("=== 插件化渠道管理系统测试 ===")
    
    # 创建渠道管理器
    manager = ChannelManager("channel_plugins")
    
    # 加载渠道
    print("\n1. 加载渠道:")
    loaded = manager.load_channels()
    print(f"加载了 {len(loaded)} 个渠道: {', '.join(loaded)}")
    
    # 列出渠道
    print("\n2. 列出渠道:")
    channels = manager.list_channels()
    for name, info in channels.items():
        print(f"  - {name}: {info['name']} (v{info['version']}) - {info['description']}")
    
    # 激活控制台渠道
    print("\n3. 激活控制台渠道:")
    result = manager.activate_channel("console_plugin")
    print(f"激活结果: {'成功' if result else '失败'}")
    
    # 发送消息
    print("\n4. 发送消息:")
    message = {"text": "测试消息", "priority": "high"}
    result = manager.send_message("console_plugin", message)
    print(f"发送结果: {'成功' if result else '失败'}")
    
    # 获取渠道状态
    print("\n5. 获取渠道状态:")
    status = manager.get_channel_status("console_plugin")
    print(f"状态: {status}")
    
    # 停用渠道
    print("\n6. 停用渠道:")
    result = manager.deactivate_channel("console_plugin")
    print(f"停用结果: {'成功' if result else '失败'}")
    
    # 重新加载渠道
    print("\n7. 重新加载渠道:")
    reloaded = manager.reload_channels()
    print(f"重新加载了 {len(reloaded)} 个渠道: {', '.join(reloaded)}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_system()
