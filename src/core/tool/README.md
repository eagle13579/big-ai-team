# 工具系统 (Tooling System)

## 系统概述

工具系统是超级 AI 团队架构中的核心组件，负责管理和执行各种工具，为 AI 智能体提供与外部世界交互的能力。

## 核心组件

### 1. 工具抽象基类 (`base.py`)

- `BaseTool`: 所有工具的抽象基类
- `ToolResult`: 工具执行结果模型
- `LLMProtocol`: LLM 协议接口

### 2. 工具分发器 (`dispatcher.py`)

- `ToolDispatcher`: 负责管理和分发工具调用
- `ToolCall`: 工具调用模型

### 3. 工具注册表 (`tool_registry.py`)

- `ToolRegistry`: 负责自动发现和注册工具

### 4. 异常管理 (`exceptions.py`)

- 提供详细的异常类层次结构

### 5. 缓存机制 (`cache.py`)

- `ToolCache`: 工具执行结果缓存

### 6. 安全管理 (`security.py`)

- `SecurityManager`: 权限管理
- `SecureSandbox`: 安全沙箱

### 7. 监控系统 (`monitoring.py`)

- `MonitoringManager`: 指标收集和审计日志
- `MetricsDecorator`: 指标收集装饰器

### 8. 架构优化 (`architecture.py`)

- `EnhancedToolRegistry`: 增强的工具注册表，支持版本管理和依赖管理
- `LLMProtocolFactory`: LLM 协议工厂
- `ToolChainExecutor`: 工具链执行器

## 快速开始

### 创建自定义工具

```python
from core.tool import BaseTool, ToolResult
from pydantic import BaseModel, Field

class MyToolArgs(BaseModel):
    param1: str = Field(..., description="First parameter")
    param2: int = Field(default=1, description="Second parameter")

class MyTool(BaseTool):
    name = "my_tool"
    description = "My custom tool"
    args_schema = MyToolArgs

    async def execute(self, param1: str, param2: int = 1) -> ToolResult:
        try:
            # 工具逻辑
            result_data = f"Processed {param1} with {param2}"
            return ToolResult(success=True, data=result_data)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

### 注册和使用工具

```python
from core.tool import tool_registry, ToolDispatcher

# 注册工具
tool_registry.register_tool(MyTool())

# 创建分发器
class MockLLMProtocol:
    async def generate(self, prompt: str) -> str:
        return '{"tool_name": "my_tool", "args": {"param1": "test", "param2": 42}}'

llm_protocol = MockLLMProtocol()
dispatcher = ToolDispatcher(llm_protocol)

# 注册工具到分发器
dispatcher.register_tool(MyTool())

# 分发工具调用
result = await dispatcher.dispatch("Run my tool with param1=test and param2=42")
print(result)
```

### 使用工具链

```python
from core.tool import tool_chain_executor, enhanced_tool_registry

# 注册工具到增强注册表
enhanced_tool_registry.register_tool(MyTool)

# 执行工具链
chain = [
    {"tool": "my_tool", "params": {"param1": "step1", "param2": 1}},
    {"tool": "web_search", "params": {"query": "AI tools", "num_results": 3}}
]

result = await tool_chain_executor.execute_chain(chain)
print(result)
```

## 配置和管理

### 权限管理

```python
from core.tool import security_manager, Permission, ToolPermission

# 注册权限
security_manager.register_permission(Permission(
    name="internet_access",
    description="Access to internet"
))

# 为工具设置权限
security_manager.register_tool_permission(ToolPermission(
    tool_name="web_search",
    required_permissions=["internet_access"]
))

# 授予权限
security_manager.grant_permission("internet_access")
```

### 缓存配置

```python
from core.tool import tool_cache

# 清理缓存
tool_cache.clear()

# 获取缓存大小
print(f"Cache size: {tool_cache.get_size()}")
```

### 监控和指标

```python
from core.tool import monitoring_manager

# 获取工具统计信息
stats = monitoring_manager.get_tool_stats("web_search")
print(stats)

# 获取审计日志
logs = monitoring_manager.get_audit_logs("web_search")
print(logs)
```

## 最佳实践

1. **工具设计**:
   - 每个工具应该专注于单一功能
   - 使用 Pydantic 模型定义参数
   - 提供清晰的错误处理

2. **性能优化**:
   - 对于频繁调用的工具，确保缓存有效
   - 合理设置超时时间

3. **安全性**:
   - 为敏感工具设置适当的权限
   - 使用安全沙箱执行可能危险的操作

4. **监控**:
   - 监控工具执行情况，及时发现问题
   - 分析工具使用模式，优化系统设计

## 版本管理

工具系统支持工具版本管理，允许同一工具的多个版本并存：

```python
from core.tool import enhanced_tool_registry

# 注册不同版本的工具
enhanced_tool_registry.register_tool(MyToolV1, version="1.0.0", is_default=True)
enhanced_tool_registry.register_tool(MyToolV2, version="2.0.0")

# 使用特定版本的工具
tool = enhanced_tool_registry.get_tool("my_tool", version="2.0.0")
```

## 依赖管理

工具系统支持工具依赖管理，确保工具在执行时所需的依赖都已满足：

```python
from core.tool import enhanced_tool_registry, ToolDependency

# 注册工具依赖
enhanced_tool_registry.register_dependency(
    tool_name="complex_tool",
    dependency=ToolDependency(
        tool_name="simple_tool",
        version="1.0.0",
        required=True
    )
)
```