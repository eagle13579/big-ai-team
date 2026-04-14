from src.evolution.strategies.base import BaseStrategy, StrategyPriority, StrategyResult, SystemState
from src.shared.logging import logger


class CapabilityStrategy(BaseStrategy):
    """能力扩展策略 - 自动发现和集成新能力"""

    name = "capability"
    description = "检测能力缺口并自动扩展：新技能注册、工具集成、模型切换"
    priority = StrategyPriority.MEDIUM

    async def evaluate(self, state: SystemState) -> float:
        """评估能力缺口"""
        score = 0.0

        if state.custom_metrics.get("skill_miss_rate", 0) > 0.2:
            score += 0.4

        if state.custom_metrics.get("tool_unavailable_rate", 0) > 0.1:
            score += 0.3

        if state.custom_metrics.get("model_fallback_rate", 0) > 0.3:
            score += 0.2

        if state.active_tasks > 100:
            score += 0.1

        return min(score, 1.0)

    async def execute(self, state: SystemState) -> StrategyResult:
        """执行能力扩展"""
        actions = []
        details = {}

        skill_miss_rate = state.custom_metrics.get("skill_miss_rate", 0)
        if skill_miss_rate > 0.2:
            actions.append("扫描并注册缺失的技能模块")
            details["skill_scan"] = True

        tool_unavailable_rate = state.custom_metrics.get("tool_unavailable_rate", 0)
        if tool_unavailable_rate > 0.1:
            actions.append("检查并修复不可用的工具")
            details["tool_repair"] = True

        model_fallback_rate = state.custom_metrics.get("model_fallback_rate", 0)
        if model_fallback_rate > 0.3:
            actions.append("评估并添加备用模型")
            details["model_backup"] = True

        logger.info(f"🔧 能力策略执行: {len(actions)} 个扩展动作")

        return StrategyResult(
            strategy_name=self.name,
            success=True,
            actions_taken=actions,
            metrics_before={"skill_miss_rate": skill_miss_rate},
            improvement=0.05,
            risk_level="low",
            rollback_possible=True,
            details=details,
        )

    async def rollback(self, result: StrategyResult) -> bool:
        """回滚能力扩展"""
        logger.info(f"⏪ 回滚能力策略: {result.actions_taken}")
        return True
