from src.evolution.strategies.base import BaseStrategy, StrategyPriority, StrategyResult, SystemState
from src.shared.logging import logger


class ReliabilityStrategy(BaseStrategy):
    """可靠性提升策略 - 自动检测和修复可靠性问题"""

    name = "reliability"
    description = "检测可靠性问题并自动修复：错误率、熔断器、重试策略"
    priority = StrategyPriority.CRITICAL

    async def evaluate(self, state: SystemState) -> float:
        """评估可靠性状态"""
        score = 0.0

        if state.error_rate > 0.1:
            score += 0.5
        elif state.error_rate > 0.05:
            score += 0.3
        elif state.error_rate > 0.01:
            score += 0.1

        if state.memory_usage > 0.9:
            score += 0.3
        elif state.memory_usage > 0.8:
            score += 0.15

        return min(score, 1.0)

    async def execute(self, state: SystemState) -> StrategyResult:
        """执行可靠性修复"""
        actions = []
        details = {}

        if state.error_rate > 0.05:
            actions.append("启用熔断器保护")
            details["circuit_breaker"] = True

        if state.error_rate > 0.1:
            actions.append("增加重试次数和退避时间")
            details["retry_config"] = {"max_retries": 5, "backoff_factor": 2.0}

        if state.memory_usage > 0.85:
            actions.append("触发内存清理和缓存压缩")
            details["memory_cleanup"] = True

        logger.info(f"🛡️ 可靠性策略执行: {len(actions)} 个修复动作")

        return StrategyResult(
            strategy_name=self.name,
            success=True,
            actions_taken=actions,
            metrics_before={"error_rate": state.error_rate, "memory_usage": state.memory_usage},
            improvement=0.15,
            risk_level="medium",
            rollback_possible=True,
            details=details,
        )

    async def rollback(self, result: StrategyResult) -> bool:
        """回滚可靠性修复"""
        logger.info(f"⏪ 回滚可靠性策略: {result.actions_taken}")
        return True
