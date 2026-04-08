import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.access.adapters import (
    AdapterFactory,
    adapter_registry,
    PlatformType
)
from src.access.adapters.base import AdapterContext


async def test_adapter_registry():
    """测试适配器注册中心"""
    print("测试适配器注册中心...")
    # 检查注册中心是否包含所有预期的适配器
    platforms = adapter_registry.list_platforms()
    print(f"已注册的平台: {platforms}")
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
    print("✅ 适配器注册中心测试通过")


async def test_mock_llm_adapter():
    """测试模拟 LLM 适配器"""
    print("\n测试模拟 LLM 适配器...")
    # 创建适配器
    adapter = AdapterFactory.create_llm_adapter(
        platform="mock_llm",
        name="test_mock_llm",
        api_key="test_key"
    )
    
    # 初始化适配器
    await adapter.initialize()
    assert adapter.is_initialized()
    print("✅ 适配器初始化成功")
    
    # 测试生成功能
    context = AdapterContext(session_id="test_session")
    result = await adapter.execute(
        operation="generate",
        params={"prompt": "Hello, world!"},
        context=context
    )
    assert "content" in result
    assert "Hello, world!" in result["content"]
    print(f"✅ 生成功能测试通过，结果: {result['content']}")
    
    # 测试健康检查
    health_result = await adapter.health_check(context)
    assert health_result["status"] == "healthy"
    print(f"✅ 健康检查测试通过，状态: {health_result['status']}")
    
    # 关闭适配器
    await adapter.close()
    assert not adapter.is_initialized()
    print("✅ 适配器关闭成功")


async def test_memory_cache_adapter():
    """测试内存缓存适配器"""
    print("\n测试内存缓存适配器...")
    # 创建适配器
    adapter = AdapterFactory.create_cache_adapter(
        platform="memory_cache",
        name="test_memory_cache"
    )
    
    # 初始化适配器
    await adapter.initialize()
    assert adapter.is_initialized()
    print("✅ 适配器初始化成功")
    
    # 测试设置缓存
    context = AdapterContext(session_id="test_session")
    await adapter.execute(
        operation="set",
        params={"key": "test_key", "value": "test_value", "ttl": 10},
        context=context
    )
    print("✅ 设置缓存成功")
    
    # 测试获取缓存
    result = await adapter.execute(
        operation="get",
        params={"key": "test_key"},
        context=context
    )
    assert result["value"] == "test_value"
    print(f"✅ 获取缓存测试通过，值: {result['value']}")
    
    # 测试删除缓存
    delete_result = await adapter.execute(
        operation="delete",
        params={"key": "test_key"},
        context=context
    )
    assert delete_result["deleted"]
    print("✅ 删除缓存成功")
    
    # 测试健康检查
    health_result = await adapter.health_check(context)
    assert health_result["status"] == "healthy"
    print(f"✅ 健康检查测试通过，状态: {health_result['status']}")
    
    # 关闭适配器
    await adapter.close()
    assert not adapter.is_initialized()
    print("✅ 适配器关闭成功")


async def test_local_storage_adapter():
    """测试本地存储适配器"""
    print("\n测试本地存储适配器...")
    # 创建适配器
    adapter = AdapterFactory.create_storage_adapter(
        platform="local_storage",
        name="test_local_storage",
        base_path="./test_storage"
    )
    
    # 初始化适配器
    await adapter.initialize()
    assert adapter.is_initialized()
    print("✅ 适配器初始化成功")
    
    # 测试写入文件
    context = AdapterContext(session_id="test_session")
    await adapter.execute(
        operation="write",
        params={"path": "test_file.txt", "content": "Hello, storage!"},
        context=context
    )
    print("✅ 写入文件成功")
    
    # 测试读取文件
    result = await adapter.execute(
        operation="read",
        params={"path": "test_file.txt"},
        context=context
    )
    assert result["content"] == "Hello, storage!"
    print(f"✅ 读取文件测试通过，内容: {result['content']}")
    
    # 测试列出文件
    list_result = await adapter.execute(
        operation="list",
        params={"directory": ""},
        context=context
    )
    assert "test_file.txt" in list_result["files"]
    print(f"✅ 列出文件测试通过，文件列表: {list_result['files']}")
    
    # 测试删除文件
    delete_result = await adapter.execute(
        operation="delete",
        params={"path": "test_file.txt"},
        context=context
    )
    assert delete_result["deleted"]
    print("✅ 删除文件成功")
    
    # 测试健康检查
    health_result = await adapter.health_check(context)
    assert health_result["status"] == "healthy"
    print(f"✅ 健康检查测试通过，状态: {health_result['status']}")
    
    # 关闭适配器
    await adapter.close()
    assert not adapter.is_initialized()
    print("✅ 适配器关闭成功")


async def main():
    """主测试函数"""
    print("开始测试多平台适配器...\n")
    
    try:
        await test_adapter_registry()
        await test_mock_llm_adapter()
        await test_memory_cache_adapter()
        await test_local_storage_adapter()
        print("\n🎉 所有测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
