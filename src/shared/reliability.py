import asyncio
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, TypeVar

from src.shared.logging import logger

T = TypeVar('T')

class RetryMechanism:
    """
    重试机制
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0, 
                 backoff_factor: float = 2.0, retry_exceptions: tuple = (Exception,)):
        """
        初始化重试机制
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            backoff_factor: 退避因子
            retry_exceptions: 需要重试的异常类型
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retry_exceptions = retry_exceptions
    
    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        执行带重试的函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        retries = 0
        delay = self.base_delay
        
        while True:
            try:
                return await func(*args, **kwargs)
            except self.retry_exceptions as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"达到最大重试次数 {self.max_retries}，执行失败: {str(e)}")
                    raise
                
                logger.warning(f"执行失败，正在重试 ({retries}/{self.max_retries}): {str(e)}")
                await asyncio.sleep(delay)
                
                # 指数退避
                delay = min(delay * self.backoff_factor, self.max_delay)

class CircuitBreaker:
    """
    熔断机制
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30, 
                 half_open_timeout: int = 5, name: str = "default"):
        """
        初始化熔断机制
        
        Args:
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时时间（秒）
            half_open_timeout: 半开状态超时时间（秒）
            name: 熔断器名称
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_timeout = half_open_timeout
        
        # 状态：CLOSED, OPEN, HALF_OPEN
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        self.last_state_change_time = None
    
    def _should_transition_to_open(self) -> bool:
        """
        判断是否应该切换到 OPEN 状态
        """
        return self.failure_count >= self.failure_threshold
    
    def _should_transition_to_half_open(self) -> bool:
        """
        判断是否应该切换到 HALF_OPEN 状态
        """
        if self.state != "OPEN":
            return False
        
        if not self.last_state_change_time:
            return False
        
        elapsed = time.time() - self.last_state_change_time
        return elapsed >= self.recovery_timeout
    
    def _should_transition_to_closed(self) -> bool:
        """
        判断是否应该切换到 CLOSED 状态
        """
        return self.state == "HALF_OPEN" and self.failure_count == 0
    
    def _update_state(self):
        """
        更新熔断器状态
        """
        if self._should_transition_to_open():
            self.state = "OPEN"
            self.last_state_change_time = time.time()
            logger.warning(f"熔断器 {self.name} 切换到 OPEN 状态")
        elif self._should_transition_to_half_open():
            self.state = "HALF_OPEN"
            self.last_state_change_time = time.time()
            logger.info(f"熔断器 {self.name} 切换到 HALF_OPEN 状态")
        elif self._should_transition_to_closed():
            self.state = "CLOSED"
            self.last_state_change_time = time.time()
            logger.info(f"熔断器 {self.name} 切换到 CLOSED 状态")
    
    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        执行带熔断的函数
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        # 检查状态
        self._update_state()
        
        if self.state == "OPEN":
            logger.warning(f"熔断器 {self.name} 处于 OPEN 状态，拒绝执行")
            raise Exception(f"熔断器 {self.name} 处于 OPEN 状态")
        
        try:
            result = await func(*args, **kwargs)
            
            # 执行成功，重置失败计数
            if self.state == "HALF_OPEN":
                self.failure_count = 0
                self._update_state()
            elif self.state == "CLOSED":
                self.failure_count = 0
            
            return result
        except Exception:
            # 执行失败，增加失败计数
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            logger.warning(f"熔断器 {self.name} 执行失败，失败计数: {self.failure_count}/{self.failure_threshold}")
            
            self._update_state()
            raise

class ServiceDegrader:
    """
    服务降级策略
    """
    
    def __init__(self, name: str = "default"):
        """
        初始化服务降级器
        
        Args:
            name: 服务名称
        """
        self.name = name
        self.degraded = False
        self.degraded_services = set()
        self.degradation_time = None
    
    def degrade(self, services: List[str]):
        """
        降级服务
        
        Args:
            services: 要降级的服务列表
        """
        self.degraded = True
        self.degraded_services.update(services)
        self.degradation_time = time.time()
        logger.warning(f"服务 {self.name} 降级，降级服务: {services}")
    
    def recover(self):
        """
        恢复服务
        """
        self.degraded = False
        self.degraded_services.clear()
        self.degradation_time = None
        logger.info(f"服务 {self.name} 已恢复")
    
    def is_degraded(self, service: str) -> bool:
        """
        检查服务是否已降级
        
        Args:
            service: 服务名称
            
        Returns:
            是否已降级
        """
        return self.degraded and service in self.degraded_services
    
    def get_degraded_services(self) -> List[str]:
        """
        获取已降级的服务列表
        
        Returns:
            已降级的服务列表
        """
        return list(self.degraded_services)

class FaultRecoveryManager:
    """
    故障恢复机制
    """
    
    def __init__(self):
        """
        初始化故障恢复管理器
        """
        self.fault_history = []
        self.recovery_strategies = {}
    
    def record_fault(self, service: str, error: Exception, timestamp: datetime = None):
        """
        记录故障
        
        Args:
            service: 服务名称
            error: 错误信息
            timestamp: 故障时间
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        fault_record = {
            "service": service,
            "error": str(error),
            "timestamp": timestamp
        }
        
        self.fault_history.append(fault_record)
        logger.error(f"记录故障: {service} - {str(error)}")
    
    def register_recovery_strategy(self, service: str, strategy: Callable):
        """
        注册恢复策略
        
        Args:
            service: 服务名称
            strategy: 恢复策略函数
        """
        self.recovery_strategies[service] = strategy
        logger.info(f"注册恢复策略: {service}")
    
    async def recover(self, service: str) -> bool:
        """
        执行恢复策略
        
        Args:
            service: 服务名称
            
        Returns:
            是否恢复成功
        """
        strategy = self.recovery_strategies.get(service)
        if not strategy:
            logger.warning(f"服务 {service} 没有注册恢复策略")
            return False
        
        try:
            result = await strategy()
            logger.info(f"服务 {service} 恢复成功")
            return True
        except Exception as e:
            logger.error(f"服务 {service} 恢复失败: {str(e)}")
            return False
    
    def get_fault_history(self, service: str = None, hours: int = 24) -> List[Dict]:
        """
        获取故障历史
        
        Args:
            service: 服务名称（可选）
            hours: 时间范围（小时）
            
        Returns:
            故障历史记录
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_history = []
        for record in self.fault_history:
            if record["timestamp"] >= cutoff_time:
                if service is None or record["service"] == service:
                    filtered_history.append(record)
        
        return filtered_history

# 全局实例
retry_mechanism = RetryMechanism()
circuit_breaker = CircuitBreaker()
service_degrader = ServiceDegrader()
fault_recovery_manager = FaultRecoveryManager()

async def execute_with_reliability(func: Callable[..., T], *args, **kwargs) -> T:
    """
    执行带可靠性机制的函数
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果
    """
    try:
        # 应用熔断机制
        result = await circuit_breaker.execute(
            # 应用重试机制
            retry_mechanism.execute,
            func, *args, **kwargs
        )
        return result
    except Exception as e:
        # 记录故障
        fault_recovery_manager.record_fault(
            func.__name__ if hasattr(func, "__name__") else "unknown",
            e
        )
        raise
