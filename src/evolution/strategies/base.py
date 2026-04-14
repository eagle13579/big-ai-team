from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StrategyPriority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class StrategyResult:
    strategy_name: str
    success: bool
    actions_taken: list[str] = field(default_factory=list)
    metrics_before: dict[str, float] = field(default_factory=dict)
    metrics_after: dict[str, float] = field(default_factory=dict)
    improvement: float = 0.0
    risk_level: str = "low"
    rollback_possible: bool = True
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemState:
    timestamp: str = ""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_rate: float = 0.0
    avg_latency: float = 0.0
    throughput: float = 0.0
    active_tasks: int = 0
    cache_hit_rate: float = 0.0
    model_cost: float = 0.0
    custom_metrics: dict[str, float] = field(default_factory=dict)


class BaseStrategy(ABC):
    """进化策略基类 - 所有策略必须继承此类"""

    name: str = "base"
    description: str = ""
    priority: StrategyPriority = StrategyPriority.MEDIUM

    @abstractmethod
    async def evaluate(self, state: SystemState) -> float:
        """评估当前状态是否需要此策略，返回评分 0-1"""
        ...

    @abstractmethod
    async def execute(self, state: SystemState) -> StrategyResult:
        """执行进化策略"""
        ...

    @abstractmethod
    async def rollback(self, result: StrategyResult) -> bool:
        """回滚进化操作"""
        ...

    def get_info(self) -> dict[str, Any]:
        """获取策略信息"""
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
        }
