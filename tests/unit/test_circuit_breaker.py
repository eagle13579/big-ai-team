import pytest
from src.core.llm import circuit_breaker, CircuitState


@pytest.mark.asyncio
async def test_circuit_breaker():
    """测试熔断器"""
    # 模拟一个会失败的函数
    async def failing_function():
        raise Exception("Test error")
    
    # 模拟一个会成功的函数
    async def successful_function():
        return "Success"
    
    # 重置熔断器
    circuit_breaker.reset()
    assert circuit_breaker.get_state() == CircuitState.CLOSED
    
    # 测试多次失败后熔断
    for i in range(6):  # 超过阈值 5
        try:
            await circuit_breaker.execute(failing_function)
        except Exception:
            pass
    
    # 验证熔断器状态变为 OPEN
    assert circuit_breaker.get_state() == CircuitState.OPEN
    
    # 测试熔断状态下拒绝请求
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        await circuit_breaker.execute(successful_function)
    
    # 重置熔断器
    circuit_breaker.reset()
    assert circuit_breaker.get_state() == CircuitState.CLOSED
    
    # 测试成功执行
    result = await circuit_breaker.execute(successful_function)
    assert result == "Success"
    assert circuit_breaker.get_state() == CircuitState.CLOSED
