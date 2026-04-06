import pytest
import time
from src.core.llm import global_rate_limiter, RequestSigner


def test_rate_limiter():
    """测试速率限制器"""
    # 重置速率限制器
    global_rate_limiter.reset()
    
    # 测试允许的请求
    test_key = "test_user"
    for i in range(100):  # 最大限制 100
        assert global_rate_limiter.is_allowed(test_key)
    
    # 测试超过限制
    assert not global_rate_limiter.is_allowed(test_key)
    
    # 重置
    global_rate_limiter.reset(test_key)
    assert global_rate_limiter.is_allowed(test_key)


def test_request_signer():
    """测试请求签名器"""
    test_data = {"key1": "value1", "key2": "value2"}
    secret = "test_secret"
    
    # 生成签名
    signature = RequestSigner.generate_signature(test_data, secret)
    assert isinstance(signature, str)
    
    # 验证签名
    assert RequestSigner.verify_signature(test_data, signature, secret)
    
    # 验证无效签名
    assert not RequestSigner.verify_signature(test_data, "invalid_signature", secret)
