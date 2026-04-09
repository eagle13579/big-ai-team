import asyncio
import pytest
from src.access.adapters import (
    AdapterFactory,
    adapter_registry,
    PlatformType
)
from src.access.adapters.base import AdapterContext


@pytest.mark.asyncio
async def test_adapter_registry():
    """测试适配器注册中心"""
    # 检查注册中心是否包含所有预期的适配器
    platforms = adapter_registry.list_platforms()
    assert "openai" in platforms
    assert "deepseek" in platforms
    assert "mock_llm" in platforms
    assert "postgresql" in platforms
    assert "sqlite" in platforms
    assert "redis" in platforms
    assert "memory_cache" in platforms
    assert "local_storage" in platforms
    assert "s3" in platforms
    assert "docker" in platforms
    assert "e2b" in platforms
    assert "langsmith" in platforms
    assert "opentelemetry" in platforms
    assert "rabbitmq" in platforms
    assert "kafka" in platforms


@pytest.mark.asyncio
async def test_mock_llm_adapter():
    """测试模拟 LLM 适配器"""
    # 创建适配器
    adapter = AdapterFactory.create_llm_adapter(
        platform="mock_llm",
        name="test_mock_llm",
        api_key="test_key"
    )
    
    # 初始化适配器
    await adapter.initialize()
    assert adapter.is_initialized()
    
    # 测试生成功能
    context = AdapterContext(session_id="test_session")
    result = await adapter.execute(
        operation="generate",
        params={"prompt": "Hello, world!"},
        context=context
    )
    assert "content" in result
    assert "Hello, world!" in result["content"]
    
    # 测试健康检查
    health_result = await adapter.health_check(context)
    assert health_result["status"] == "healthy"
    
    # 关闭适配器
    await adapter.close()
    assert not adapter.is_initialized()


@pytest.mark.asyncio
async def test_memory_cache_adapter():
    """测试内存缓存适配器"""
    # 创建适配器
    adapter = AdapterFactory.create_cache_adapter(
        platform="memory_cache",
        name="test_memory_cache"
    )
    
    # 初始化适配器
    await adapter.initialize()
    assert adapter.is_initialized()
    
    # 测试设置缓存
    context = AdapterContext(session_id="test_session")
    await adapter.execute(
        operation="set",
        params={"key": "test_key", "value": "test_value", "ttl": 10},
        context=context
    )
    
    # 测试获取缓存
    result = await adapter.execute(
        operation="get",
        params={"key": "test_key"},
        context=context
    )
    assert result["value"] == "test_value"
    
    # 测试删除缓存
    delete_result = await adapter.execute(
        operation="delete",
        params={"key": "test_key"},
        context=context
    )
    assert delete_result["deleted"]
    
    # 测试健康检查
    health_result = await adapter.health_check(context)
    assert health_result["status"] == "healthy"
    
    # 关闭适配器
    await adapter.close()
    assert not adapter.is_initialized()


@pytest.mark.asyncio
async def test_local_storage_adapter():
    """测试本地存储适配器"""
    # 创建适配器
    adapter = AdapterFactory.create_storage_adapter(
        platform="local_storage",
        name="test_local_storage",
        base_path="./test_storage"
    )
    
    # 初始化适配器
    await adapter.initialize()
    assert adapter.is_initialized()
    
    # 测试写入文件
    context = AdapterContext(session_id="test_session")
    await adapter.execute(
        operation="write",
        params={"path": "test_file.txt", "content": "Hello, storage!"},
        context=context
    )
    
    # 测试读取文件
    result = await adapter.execute(
        operation="read",
        params={"path": "test_file.txt"},
        context=context
    )
    assert result["content"] == "Hello, storage!"
    
    # 测试列出文件
    list_result = await adapter.execute(
        operation="list",
        params={"directory": ""},
        context=context
    )
    assert "test_file.txt" in list_result["files"]
    
    # 测试删除文件
    delete_result = await adapter.execute(
        operation="delete",
        params={"path": "test_file.txt"},
        context=context
    )
    assert delete_result["deleted"]
    
    # 测试健康检查
    health_result = await adapter.health_check(context)
    assert health_result["status"] == "healthy"
    
    # 关闭适配器
    await adapter.close()
    assert not adapter.is_initialized()


if __name__ == "__main__":
    asyncio.run(test_adapter_registry())
    asyncio.run(test_mock_llm_adapter())
    asyncio.run(test_memory_cache_adapter())
    asyncio.run(test_local_storage_adapter())
    print("All tests passed!")
