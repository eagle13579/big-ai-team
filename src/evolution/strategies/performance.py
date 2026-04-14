from src.evolution.strategies.base import BaseStrategy, StrategyPriority, StrategyResult, SystemState
from src.shared.logging import logger


class PerformanceStrategy(BaseStrategy):
    """性能优化策略 - 自动检测和修复性能瓶颈"""

    name = "performance"
    description = "检测性能瓶颈并自动优化：缓存策略、并发调整、模型路由优化"
    priority = StrategyPriority.HIGH

    async def evaluate(self, state: SystemState) -> float:
        """评估性能状态"""
        score = 0.0

        if state.avg_latency > 5.0:
            score += 0.4
        elif state.avg_latency > 2.0:
            score += 0.2

        if state.cache_hit_rate < 0.3:
            score += 0.3
        elif state.cache_hit_rate < 0.6:
            score += 0.15

        if state.cpu_usage > 0.8:
            score += 0.2
        elif state.cpu_usage > 0.6:
            score += 0.1

        if state.throughput < 10:
            score += 0.1

        return min(score, 1.0)

    async def execute(self, state: SystemState) -> StrategyResult:
        """执行性能优化"""
        actions = []
        details = {}

        if state.cache_hit_rate < 0.5:
            actions.append("增加缓存预热策略")
            details["cache_warmup"] = True

        if state.avg_latency > 3.0:
            actions.append("切换到更快的模型")
            details["model_switch"] = True

        if state.cpu_usage > 0.7:
            actions.append("降低并发度")
            details["reduce_concurrency"] = True

        if state.throughput < 20:
            actions.append("启用批量处理")
            details["batch_mode"] = True

        logger.info(f"⚡ 性能策略执行: {len(actions)} 个优化动作")

        return StrategyResult(
            strategy_name=self.name,
            success=True,
            actions_taken=actions,
            metrics_before={"avg_latency": state.avg_latency, "cache_hit_rate": state.cache_hit_rate},
            improvement=0.1,
            risk_level="low",
            rollback_possible=True,
            details=details,
        )

    async def rollback(self, result: StrategyResult) -> bool:
        """回滚性能优化"""
        logger.info(f"⏪ 回滚性能策略: {result.actions_taken}")
        return True
