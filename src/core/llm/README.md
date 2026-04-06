# LLM 适配器模块

## 概述

LLM 适配器模块是超级 AI 团队系统的核心组件，负责统一抽象和标准化各 LLM 服务的接入接口，实现"一次开发，多模型部署"的能力。

## 核心特性

- **统一协议**：通过抽象基类定义统一的 LLM 接口
- **异步支持**：全链路使用 asyncio 和 httpx，支持高并发
- **配置管理**：使用 pydantic-settings 管理配置
- **依赖注入**：使用 dependency-injector 实现依赖注入
- **日志系统**：集成 loguru 实现结构化日志
- **HTTP 优化**：实现连接池和缓存
- **错误处理**：添加指数退避和熔断器
- **安全性**：实现请求签名和速率限制
- **插件化**：支持插件扩展
- **中间件**：支持中间件机制

## 快速开始

### 安装依赖

```bash
pip install dependency-injector loguru httpx pydantic-settings
```

### 基本使用

```python
from src.core.llm import LLMFactory, LLMMessage

# 创建 LLM 客户端
client = LLMFactory.create("openai_compatible")

# 准备消息
messages = [
    LLMMessage(role="system", content="You are a helpful assistant"),
    LLMMessage(role="user", content="Hello, how are you?")
]

# 生成响应
response = await client.generate(messages)
print(response.text)

# 流式生成
async for chunk in client.generate_stream(messages):
    print(chunk.text, end="")
```

### 使用配置管理

```python
from src.core.llm import LLMConfig, LLMFactory

# 创建配置
config = LLMConfig(
    base_url="https://api.ace-browser.com/v1",
    model="ace-nova-2026-pro",
    api_key="your-api-key",
    timeout=30,
    max_retries=3
)

# 使用配置创建客户端
client = LLMFactory.create("openai_compatible", llm_config=config)
```

### 使用依赖注入

```python
from src.core.llm import LLMContainer

# 创建容器
container = LLMContainer()

# 获取客户端
client = container.llm_client()

# 使用客户端
response = await client.generate(messages)
```

## API 文档

### BaseLLMProtocol

抽象基类，定义了 LLM 客户端的统一接口。

#### 方法

- `async generate(messages: List[LLMMessage], **kwargs) -> LLMResponse`：生成单个响应
- `async generate_stream(messages: List[LLMMessage], **kwargs) -> AsyncGenerator[LLMResponse, None]`：流式生成响应

### OpenAICompatibleClient

OpenAI 兼容的客户端实现。

#### 构造参数

- `base_url`：API 基础 URL，默认 "https://api.ace-browser.com/v1"
- `model`：模型名称，默认 "ace-nova-2026-pro"
- `api_key`：API 密钥
- `timeout`：超时时间，默认 30 秒
- `max_retries`：最大重试次数，默认 3

### LLMFactory

工厂类，用于创建 LLM 客户端。

#### 方法

- `create(protocol: str, config: Dict[str, Any] = None, llm_config: LLMConfig = None) -> BaseLLMProtocol`：创建客户端
- `create_from_provider_config(protocol: str, provider_config: LLMProviderConfig) -> BaseLLMProtocol`：从提供商配置创建客户端
- `get_supported_protocols() -> list`：获取支持的协议列表

### 数据模型

#### LLMMessage

- `role`：消息角色，如 "system", "user", "assistant"
- `content`：消息内容

#### LLMResponse

- `text`：响应文本
- `usage`：使用情况，如 token 统计
- `tool_calls`：工具调用列表

#### ToolCall

- `name`：工具名称
- `arguments`：工具参数

## 高级功能

### 中间件

```python
from src.core.llm import middleware_manager, Middleware

class LoggingMiddleware(Middleware):
    async def process_request(self, request):
        print(f"Processing request: {request}")
        return request
    
    async def process_response(self, response):
        print(f"Processing response: {response}")
        return response

# 添加中间件
middleware_manager.add_middleware(LoggingMiddleware())
```

### 插件

```python
from src.core.llm import plugin_manager, Plugin

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "My custom plugin"
    
    def initialize(self, config):
        print("Initializing plugin")
        return True
    
    def shutdown(self):
        print("Shutting down plugin")
        return True

# 添加插件目录
plugin_manager.add_plugin_dir("plugins")

# 加载插件
plugin_manager.load_plugins()
```

### 熔断器

```python
from src.core.llm import circuit_breaker

@circuit_breaker
async def risky_operation():
    # 可能失败的操作
    pass

# 使用
result = await risky_operation()
```

### 速率限制

```python
from src.core.llm import global_rate_limiter

# 检查速率限制
if global_rate_limiter.is_allowed("user_123"):
    # 执行操作
    pass
else:
    # 速率限制
    pass
```

## 配置

可以通过环境变量或配置文件配置 LLM 客户端：

### 环境变量

```
LLM_BASE_URL=https://api.ace-browser.com/v1
LLM_MODEL=ace-nova-2026-pro
LLM_API_KEY=your-api-key
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3
```

### 配置文件

创建 `.env` 文件：

```
LLM_BASE_URL=https://api.ace-browser.com/v1
LLM_MODEL=ace-nova-2026-pro
LLM_API_KEY=your-api-key
```

## 测试

运行单元测试：

```bash
pytest tests/unit/test_llm_protocol.py tests/unit/test_http_client.py tests/unit/test_circuit_breaker.py tests/unit/test_security.py -v
```

## 故障排除

### 常见错误

1. **ConnectionError**：检查网络连接和 API URL
2. **AuthenticationError**：检查 API 密钥
3. **RateLimitError**：检查速率限制设置
4. **CircuitBreakerOpen**：服务暂时不可用，稍后重试

### 日志

日志文件位于 `logs/llm.log`，可用于排查问题。

## 贡献

欢迎提交问题和 pull request！

## 许可证

MIT
