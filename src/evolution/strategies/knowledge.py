from src.evolution.strategies.base import BaseStrategy, StrategyPriority, StrategyResult, SystemState
from src.shared.logging import logger


class KnowledgeStrategy(BaseStrategy):
    """知识积累策略 - 自动从执行经验中学习和积累知识"""

    name = "knowledge"
    description = "从执行经验中学习：模式识别、最佳实践提取、错误预防"
    priority = StrategyPriority.MEDIUM

    async def evaluate(self, state: SystemState) -> float:
        """评估知识积累需求"""
        score = 0.0

        repeated_errors = state.custom_metrics.get("repeated_error_rate", 0)
        if repeated_errors > 0.3:
            score += 0.4
        elif repeated_errors > 0.1:
            score += 0.2

        knowledge_coverage = state.custom_metrics.get("knowledge_coverage", 1.0)
        if knowledge_coverage < 0.5:
            score += 0.3
        elif knowledge_coverage < 0.8:
            score += 0.1

        if state.custom_metrics.get("new_pattern_detected", False):
            score += 0.2

        return min(score, 1.0)

    async def execute(self, state: SystemState) -> StrategyResult:
        """执行知识积累"""
        actions = []
        details = {}

        repeated_errors = state.custom_metrics.get("repeated_error_rate", 0)
        if repeated_errors > 0.1:
            actions.append("提取重复错误模式并生成预防规则")
            details["error_pattern_extraction"] = True

        knowledge_coverage = state.custom_metrics.get("knowledge_coverage", 1.0)
        if knowledge_coverage < 0.7:
            actions.append("从最近执行记录中提取最佳实践")
            details["best_practice_extraction"] = True

        if state.custom_metrics.get("new_pattern_detected", False):
            actions.append("记录新发现的执行模式")
            details["pattern_recording"] = True

        logger.info(f"📚 知识策略执行: {len(actions)} 个积累动作")

        return StrategyResult(
            strategy_name=self.name,
            success=True,
            actions_taken=actions,
            metrics_before={
                "repeated_error_rate": repeated_errors,
                "knowledge_coverage": knowledge_coverage,
            },
            improvement=0.08,
            risk_level="low",
            rollback_possible=True,
            details=details,
        )

    async def rollback(self, result: StrategyResult) -> bool:
        """回滚知识积累（通常不需要回滚）"""
        logger.info(f"⏪ 回滚知识策略: {result.actions_taken}")
        return True
