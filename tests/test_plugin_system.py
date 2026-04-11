import os
import sys
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.channel_manager import ChannelManager


def test_plugin_loading():
    """测试插件加载"""
    print("测试插件加载...")
    
    # 创建临时插件目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 复制示例插件到临时目录
        plugin_files = ["console_plugin.py", "file_plugin.py"]
        for plugin_file in plugin_files:
            src = os.path.join("channel_plugins", plugin_file)
            dst = os.path.join(temp_dir, plugin_file)
            if os.path.exists(src):
                with open(src, encoding="utf-8") as f:
                    content = f.read()
                # 保持绝对导入路径
                content = content
                with open(dst, "w", encoding="utf-8") as f:
                    f.write(content)
        
        # 测试插件加载
        manager = ChannelManager(temp_dir)
        loaded = manager.load_channels()
        print(f"加载的插件: {loaded}")
        assert len(loaded) >= 2, "应该至少加载2个插件"
        
        # 测试列出渠道
        channels = manager.list_channels()
        print(f"渠道列表: {list(channels.keys())}")
        assert len(channels) >= 2, "应该至少有2个渠道"
        
        print("插件加载测试通过!")


def test_channel_activation():
    """测试渠道激活"""
    print("测试渠道激活...")
    
    # 创建临时插件目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 复制控制台插件到临时目录
        src = os.path.join("channel_plugins", "console_plugin.py")
        dst = os.path.join(temp_dir, "console_plugin.py")
        if os.path.exists(src):
            with open(src, encoding="utf-8") as f:
                content = f.read()
            # 修改导入路径
            content = content.replace("from core.plugin_interface", "from ..core.plugin_interface")
            with open(dst, "w", encoding="utf-8") as f:
                f.write(content)
        
        manager = ChannelManager(temp_dir)
        manager.load_channels()
        
        # 测试激活渠道
        result = manager.activate_channel("console_plugin", {"test": "config"})
        assert result, "渠道激活应该成功"
        
        # 测试渠道状态
        status = manager.get_channel_status("console_plugin")
        assert status is not None, "应该能获取渠道状态"
        print(f"渠道状态: {status}")
        
        # 测试停用渠道
        result = manager.deactivate_channel("console_plugin")
        assert result, "渠道停用应该成功"
        
        print("渠道激活测试通过!")


def test_message_sending():
    """测试消息发送"""
    print("测试消息发送...")
    
    # 创建临时插件目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 复制控制台插件到临时目录
        src = os.path.join("channel_plugins", "console_plugin.py")
        dst = os.path.join(temp_dir, "console_plugin.py")
        if os.path.exists(src):
            with open(src, encoding="utf-8") as f:
                content = f.read()
            # 修改导入路径
            content = content.replace("from core.plugin_interface", "from ..core.plugin_interface")
            with open(dst, "w", encoding="utf-8") as f:
                f.write(content)
        
        manager = ChannelManager(temp_dir)
        manager.load_channels()
        manager.activate_channel("console_plugin")
        
        # 测试发送消息
        message = {"text": "测试消息", "priority": "high"}
        result = manager.send_message("console_plugin", message)
        assert result, "消息发送应该成功"
        
        print("消息发送测试通过!")


def test_reload_plugins():
    """测试重新加载插件"""
    print("测试重新加载插件...")
    
    # 创建临时插件目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 复制控制台插件到临时目录
        src = os.path.join("channel_plugins", "console_plugin.py")
        dst = os.path.join(temp_dir, "console_plugin.py")
        if os.path.exists(src):
            with open(src, encoding="utf-8") as f:
                content = f.read()
            # 修改导入路径
            content = content.replace("from core.plugin_interface", "from ..core.plugin_interface")
            with open(dst, "w", encoding="utf-8") as f:
                f.write(content)
        
        manager = ChannelManager(temp_dir)
        initial_loaded = manager.load_channels()
        print(f"初始加载的插件: {initial_loaded}")
        
        # 激活渠道
        manager.activate_channel("console_plugin")
        
        # 重新加载插件
        reloaded = manager.reload_channels()
        print(f"重新加载的插件: {reloaded}")
        assert len(reloaded) == len(initial_loaded), "重新加载应该加载相同数量的插件"
        
        # 检查渠道是否被停用
        channels = manager.list_channels()
        assert not channels.get("console_plugin", {}).get("active", False), "重新加载后渠道应该被停用"
        
        print("重新加载插件测试通过!")


if __name__ == "__main__":
    test_plugin_loading()
    test_channel_activation()
    test_message_sending()
    test_reload_plugins()
    print("所有测试通过!")
