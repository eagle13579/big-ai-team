# 插件化渠道管理系统

一个灵活的插件化渠道管理系统，支持动态添加新渠道，适用于各种消息分发场景。

## 系统架构

- **核心模块**：
  - `core/plugin_interface.py` - 插件接口规范
  - `core/plugin_loader.py` - 插件加载机制
  - `core/channel_manager.py` - 渠道管理
  - `core/plugin_manager.py` - 命令行管理工具

- **插件目录**：
  - `channel_plugins/` - 存放渠道插件

- **示例插件**：
  - `console_plugin.py` - 控制台输出插件
  - `file_plugin.py` - 文件输出插件

- **测试**：
  - `tests/test_plugin_system.py` - 系统测试

## 快速开始

### 1. 安装依赖

本系统使用纯Python实现，无需额外依赖。

### 2. 运行管理工具

```bash
# 列出所有渠道
python core/plugin_manager.py list

# 加载渠道
python core/plugin_manager.py load

# 激活渠道
python core/plugin_manager.py activate -c console_plugin --config '{"test": "config"}'

# 发送消息
python core/plugin_manager.py send -c console_plugin -m '{"text": "测试消息"}'

# 查看渠道状态
python core/plugin_manager.py status -c console_plugin

# 停用渠道
python core/plugin_manager.py deactivate -c console_plugin

# 重新加载渠道
python core/plugin_manager.py reload
```

## 开发自定义渠道插件

### 1. 创建插件文件

在 `channel_plugins/` 目录下创建一个新的Python文件，例如 `my_plugin.py`。

### 2. 实现插件接口

```python
from core.plugin_interface import ChannelPlugin


class MyPlugin(ChannelPlugin):
    """自定义渠道插件"""
    
    @property
    def name(self) -> str:
        return "My Channel"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "我的自定义渠道"
    
    def initialize(self, config: dict) -> bool:
        # 初始化逻辑
        return True
    
    def send_message(self, message: dict) -> bool:
        # 发送消息逻辑
        return True
    
    def get_status(self) -> dict:
        # 获取状态逻辑
        return {"status": "active"}
    
    def shutdown(self) -> bool:
        # 关闭逻辑
        return True
```

### 3. 加载并使用插件

```bash
# 重新加载渠道
python core/plugin_manager.py reload

# 激活新渠道
python core/plugin_manager.py activate -c my_plugin

# 发送消息
python core/plugin_manager.py send -c my_plugin -m '{"text": "测试消息"}'
```

## 系统特性

- **动态加载**：支持运行时动态加载插件
- **热插拔**：无需重启系统即可添加新渠道
- **统一接口**：所有渠道插件遵循相同的接口规范
- **灵活配置**：每个渠道可以有独立的配置
- **状态管理**：实时监控渠道状态
- **命令行工具**：提供便捷的命令行管理界面

## 测试

运行测试脚本验证系统功能：

```bash
python tests/test_plugin_system.py
```

## 扩展建议

- **添加网络渠道**：实现HTTP、WebSocket等网络渠道
- **添加消息队列**：集成RabbitMQ、Kafka等消息队列
- **添加监控**：实现渠道健康检查和监控
- **添加权限控制**：实现渠道访问权限管理
- **添加UI界面**：开发Web界面管理渠道

## 注意事项

- 插件文件必须放在 `channel_plugins/` 目录下
- 插件类必须继承 `ChannelPlugin` 接口
- 插件文件名不能以 `_` 开头
- 插件必须实现所有抽象方法
