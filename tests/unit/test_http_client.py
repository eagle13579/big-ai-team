import pytest
from src.core.llm import http_client_manager


@pytest.mark.asyncio
async def test_http_client_manager():
    """测试 HTTP 客户端管理器"""
    # 获取客户端
    client1 = await http_client_manager.get_client("https://api.ace-browser.com/v1")
    client2 = await http_client_manager.get_client("https://api.ace-browser.com/v1")
    
    # 验证是同一个客户端实例
    assert client1 is client2
    
    # 测试缓存
    test_url = "https://api.ace-browser.com/v1/test"
    test_data = {"key": "value"}
    test_value = {"result": "success"}
    
    # 设置缓存
    http_client_manager.set_to_cache(test_url, "POST", test_data, test_value)
    
    # 获取缓存
    cached_value = http_client_manager.get_from_cache(test_url, "POST", test_data)
    assert cached_value == test_value
    
    # 清除缓存
    http_client_manager.clear_cache()
    cached_value = http_client_manager.get_from_cache(test_url, "POST", test_data)
    assert cached_value is None
    
    # 关闭所有客户端
    await http_client_manager.close_all()
