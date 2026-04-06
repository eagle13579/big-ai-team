import time
from enum import Enum
from typing import Optional, Callable, Any
from .logger import logger


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        reset_timeout: float = 5.0
    ):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败次数阈值，超过此值将触发熔断
            recovery_timeout: 熔断后恢复时间（秒）
            reset_timeout: 半开状态下的重置时间（秒）
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.reset_timeout = reset_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.last_state_change_time = 0
    
    def __call__(self, func: Callable) -> Callable:
        """装饰器方法"""
        async def wrapper(*args, **kwargs) -> Any:
            return await self.execute(func, *args, **kwargs)
        return wrapper
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数并应用熔断器逻辑"""
        current_time = time.time()
        
        # 检查是否需要从 OPEN 状态转换到 HALF_OPEN
        if self.state == CircuitState.OPEN:
            if current_time - self.last_state_change_time > self.recovery_timeout:
                logger.info("Circuit breaker changing from OPEN to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.last_state_change_time = current_time
            else:
                logger.warning("Circuit breaker is OPEN, rejecting request")
                raise Exception("Circuit breaker is OPEN")
        
        try:
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 成功执行，重置状态
            if self.state == CircuitState.HALF_OPEN:
                logger.info("Circuit breaker changing from HALF_OPEN to CLOSED")
                self.state = CircuitState.CLOSED
                self.last_state_change_time = current_time
            self.failure_count = 0
            return result
        except Exception as e:
            # 执行失败，更新状态
            self.failure_count += 1
            self.last_failure_time = current_time
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    logger.warning(f"Circuit breaker changing from CLOSED to OPEN after {self.failure_count} failures")
                    self.state = CircuitState.OPEN
                    self.last_state_change_time = current_time
            elif self.state == CircuitState.HALF_OPEN:
                # 半开状态下失败，回到 OPEN 状态
                logger.warning("Circuit breaker changing from HALF_OPEN to OPEN")
                self.state = CircuitState.OPEN
                self.last_state_change_time = current_time
            
            raise
    
    def get_state(self) -> CircuitState:
        """获取当前状态"""
        return self.state
    
    def reset(self):
        """重置熔断器"""
        logger.info("Resetting circuit breaker")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.last_state_change_time = 0


# 全局熔断器实例
circuit_breaker = CircuitBreaker()
