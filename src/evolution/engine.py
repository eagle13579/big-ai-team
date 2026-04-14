import asyncio
import time
from datetime import datetime
from typing import Any

from src.evolution.strategies.base import BaseStrategy, StrategyResult, SystemState
from src.evolution.strategies.performance import PerformanceStrategy
from src.evolution.strategies.reliability import ReliabilityStrategy
from src.evolution.strategies.capability import CapabilityStrategy
from src.evolution.strategies.knowledge import KnowledgeStrategy
from src.evolution.knowledge_base import EvolutionKnowledgeBase
from src.shared.logging import logger
from src.shared.schemas import EvolutionLogEntry, AnalysisResult, Decision


class EvolutionEngine:
    """
    自进化引擎主控 - 6阶段循环: 感知→认知→决策→规划→执行→反馈
    """

    def __init__(self, llm_client=None, knowledge_base: EvolutionKnowledgeBase | None = None):
        self._llm_client = llm_client
        self._knowledge_base = knowledge_base or EvolutionKnowledgeBase()
        self._strategies: dict[str, BaseStrategy] = {}
        self._running = False
        self._cycle_count = 0
        self._last_state: SystemState | None = None
        self._evolution_log: list[EvolutionLogEntry] = []
        self._lock = asyncio.Lock()

        self._register_default_strategies()

    def _register_default_strategies(self):
        """注册默认策略"""
        default_strategies = [
            PerformanceStrategy(),
            ReliabilityStrategy(),
            CapabilityStrategy(),
            KnowledgeStrategy(),
        ]
        for strategy in default_strategies:
            self._strategies[strategy.name] = strategy

    def register_strategy(self, strategy: BaseStrategy):
        """注册自定义策略"""
        self._strategies[strategy.name] = strategy
        logger.info(f"🧬 注册进化策略: {strategy.name}")

    def unregister_strategy(self, name: str):
        """注销策略"""
        if name in self._strategies:
            del self._strategies[name]

    async def run_cycle(self) -> dict[str, Any]:
        """运行一次完整的进化循环"""
        async with self._lock:
            self._cycle_count += 1
            cycle_start = time.time()
            logger.info(f"🧬 ===== 进化循环 #{self._cycle_count} 开始 =====")

            state = await self._perceive()
            self._last_state = state

            analysis = await self._cognize(state)

            decisions = await self._decide(state, analysis)

            plan = await self._plan(decisions)

            results = await self._execute_plan(plan)

            feedback = await self._feedback(results)

            cycle_duration = time.time() - cycle_start
            log_entry = EvolutionLogEntry(
                phase="feedback",
                state=state,
                analysis=analysis if isinstance(analysis, AnalysisResult) else None,
                decisions=decisions if decisions and isinstance(decisions[0], Decision) else [],
                result=feedback,
                duration_ms=cycle_duration * 1000,
            )
            self._evolution_log.append(log_entry)

            cycle_result = {
                "cycle": self._cycle_count,
                "timestamp": datetime.now().isoformat(),
                "state": self._state_to_dict(state),
                "analysis": analysis,
                "decisions": decisions,
                "plan": plan,
                "results": [self._result_to_dict(r) for r in results],
                "feedback": feedback,
                "duration_seconds": cycle_duration,
            }

            await self._knowledge_base.record_decision("evolution_cycle", self._state_to_dict(state), cycle_result)

            logger.info(f"🧬 ===== 进化循环 #{self._cycle_count} 完成 ({cycle_duration:.1f}s) =====")
            return cycle_result

    async def run_continuous(self, interval_seconds: int = 300, max_cycles: int = 0):
        """持续运行进化循环"""
        self._running = True
        logger.info(f"🧬 启动持续进化模式，间隔: {interval_seconds}s")

        while self._running:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"❌ 进化循环异常: {e}")

            if max_cycles > 0 and self._cycle_count >= max_cycles:
                logger.info(f"🧬 达到最大循环次数 {max_cycles}，停止进化")
                break

            await asyncio.sleep(interval_seconds)

    def stop(self):
        """停止持续进化"""
        self._running = False
        logger.info("🧬 停止持续进化模式")

    # ========== 阶段1: 感知 ==========

    async def _perceive(self) -> SystemState:
        """感知系统状态"""
        logger.info("📡 阶段1: 感知系统状态")

        try:
            import psutil
            cpu_usage, memory_usage = await asyncio.to_thread(self._collect_system_metrics)
        except ImportError:
            cpu_usage = 0.0
            memory_usage = 0.0

        state = SystemState(
            timestamp=datetime.now().isoformat(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            error_rate=self._collect_error_rate(),
            avg_latency=self._collect_avg_latency(),
            throughput=self._collect_throughput(),
            active_tasks=self._collect_active_tasks(),
            cache_hit_rate=self._collect_cache_hit_rate(),
            model_cost=self._collect_model_cost(),
        )

        logger.info(
            f"📡 感知完成: CPU={cpu_usage:.1%}, 内存={memory_usage:.1%}, "
            f"错误率={state.error_rate:.2%}, 延迟={state.avg_latency:.2f}s"
        )
        return state

    # ========== 阶段2: 认知 ==========

    async def _cognize(self, state: SystemState) -> dict[str, Any]:
        """认知分析 - 检测异常和趋势"""
        logger.info("🧠 阶段2: 认知分析")

        analysis: dict[str, Any] = {
            "anomalies": [],
            "trends": [],
            "risk_level": "low",
        }

        if state.error_rate > 0.1:
            analysis["anomalies"].append({"type": "high_error_rate", "value": state.error_rate})
            analysis["risk_level"] = "high"

        if state.cpu_usage > 0.8:
            analysis["anomalies"].append({"type": "high_cpu", "value": state.cpu_usage})
            if analysis["risk_level"] == "low":
                analysis["risk_level"] = "medium"

        if state.memory_usage > 0.85:
            analysis["anomalies"].append({"type": "high_memory", "value": state.memory_usage})
            if analysis["risk_level"] == "low":
                analysis["risk_level"] = "medium"

        if state.avg_latency > 5.0:
            analysis["trends"].append({"type": "latency_increase", "value": state.avg_latency})

        if state.cache_hit_rate < 0.3:
            analysis["trends"].append({"type": "low_cache_efficiency", "value": state.cache_hit_rate})

        similar_decisions = self._knowledge_base.get_similar_decisions(
            "any", self._state_to_dict(state), limit=3
        )
        analysis["historical_context"] = len(similar_decisions)

        logger.info(f"🧠 认知完成: {len(analysis['anomalies'])} 个异常, 风险={analysis['risk_level']}")
        return analysis

    # ========== 阶段3: 决策 ==========

    async def _decide(self, state: SystemState, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """决策 - 评估策略，选择最优进化路径"""
        logger.info("⚖️ 阶段3: 决策评估")

        decisions = []
        for name, strategy in self._strategies.items():
            try:
                score = await strategy.evaluate(state)
                if score > 0.1:
                    decisions.append({
                        "strategy": name,
                        "score": score,
                        "priority": strategy.priority.value,
                        "info": strategy.get_info(),
                    })
            except Exception as e:
                logger.warning(f"⚠️ 策略 {name} 评估失败: {e}")

        decisions.sort(key=lambda x: (x["priority"], x["score"]), reverse=True)

        logger.info(f"⚖️ 决策完成: {len(decisions)} 个策略被选中")
        for d in decisions:
            logger.info(f"  - {d['strategy']}: 评分={d['score']:.2f}, 优先级={d['priority']}")

        return decisions

    # ========== 阶段4: 规划 ==========

    async def _plan(self, decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """规划 - 生成进化计划"""
        logger.info("📋 阶段4: 生成进化计划")

        plan = []
        for decision in decisions:
            plan.append({
                "strategy": decision["strategy"],
                "score": decision["score"],
                "priority": decision["priority"],
                "action": "execute",
            })

        logger.info(f"📋 规划完成: {len(plan)} 个进化动作")
        return plan

    # ========== 阶段5: 执行 ==========

    async def _execute_plan(self, plan: list[dict[str, Any]]) -> list[StrategyResult]:
        """执行进化计划"""
        logger.info("⚡ 阶段5: 执行进化计划")

        results = []
        for action in plan:
            strategy_name = action["strategy"]
            strategy = self._strategies.get(strategy_name)

            if strategy is None:
                logger.warning(f"⚠️ 策略 {strategy_name} 未注册，跳过")
                continue

            try:
                if self._last_state is None:
                    continue
                result = await strategy.execute(self._last_state)
                results.append(result)

                if result.success:
                    await self._knowledge_base.record_effect(
                        strategy_name, self._result_to_dict(result), result.improvement
                    )
                    logger.info(f"✅ 策略 {strategy_name} 执行成功，改进: {result.improvement:.1%}")
                else:
                    logger.warning(f"⚠️ 策略 {strategy_name} 执行失败")

            except Exception as e:
                logger.error(f"❌ 策略 {strategy_name} 执行异常: {e}")

        return results

    # ========== 阶段6: 反馈 ==========

    async def _feedback(self, results: list[StrategyResult]) -> dict[str, Any]:
        """反馈 - 评估进化效果"""
        logger.info("📊 阶段6: 反馈评估")

        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_improvement = sum(r.improvement for r in results if r.success)

        feedback = {
            "total_actions": len(results),
            "successful": successful,
            "failed": failed,
            "total_improvement": total_improvement,
            "needs_rollback": any(not r.rollback_possible for r in results if not r.success),
        }

        for result in results:
            if not result.success and result.rollback_possible:
                strategy = self._strategies.get(result.strategy_name)
                if strategy:
                    try:
                        rollback_ok = await strategy.rollback(result)
                        if not rollback_ok:
                            await self._knowledge_base.record_lesson(
                                "rollback_failure",
                                f"策略 {result.strategy_name} 回滚失败",
                                self._result_to_dict(result),
                            )
                    except Exception as e:
                        logger.error(f"❌ 回滚失败: {e}")

        logger.info(f"📊 反馈完成: {successful}/{len(results)} 成功, 总改进: {total_improvement:.1%}")
        return feedback

    # ========== 辅助方法 ==========

    def _collect_error_rate(self) -> float:
        """收集错误率"""
        try:
            from src.shared.monitoring import error_counter, request_counter
            errors = error_counter._value.get()
            requests = request_counter._value.get()
            return errors / max(requests, 1)
        except Exception:
            return 0.0

    def _collect_avg_latency(self) -> float:
        """收集平均延迟"""
        try:
            from src.shared.monitoring import task_duration_histogram
            return task_duration_histogram._sum.get() / max(task_duration_histogram._count.get(), 1)
        except Exception:
            return 0.0

    def _collect_throughput(self) -> float:
        """收集吞吐量"""
        try:
            from src.shared.monitoring import request_counter
            return request_counter._value.get()
        except Exception:
            return 0.0

    def _collect_active_tasks(self) -> int:
        """收集活跃任务数"""
        return 0

    def _collect_cache_hit_rate(self) -> float:
        """收集缓存命中率"""
        return 0.0

    def _collect_model_cost(self) -> float:
        """收集模型成本"""
        return 0.0

    def _state_to_dict(self, state: SystemState) -> dict[str, Any]:
        """将状态转换为字典"""
        return {
            "timestamp": state.timestamp,
            "cpu_usage": state.cpu_usage,
            "memory_usage": state.memory_usage,
            "error_rate": state.error_rate,
            "avg_latency": state.avg_latency,
            "throughput": state.throughput,
            "active_tasks": state.active_tasks,
            "cache_hit_rate": state.cache_hit_rate,
            "model_cost": state.model_cost,
        }

    def _result_to_dict(self, result: StrategyResult) -> dict[str, Any]:
        """将结果转换为字典"""
        return {
            "strategy_name": result.strategy_name,
            "success": result.success,
            "actions_taken": result.actions_taken,
            "improvement": result.improvement,
            "risk_level": result.risk_level,
        }

    def get_evolution_log(self) -> list[dict[str, Any]]:
        """获取进化日志"""
        return [entry.model_dump() if hasattr(entry, 'model_dump') else entry for entry in self._evolution_log]

    def get_status(self) -> dict[str, Any]:
        """获取引擎状态"""
        return {
            "running": self._running,
            "cycle_count": self._cycle_count,
            "strategies": list(self._strategies.keys()),
            "knowledge_stats": self._knowledge_base.get_stats(),
        }

    @staticmethod
    def _collect_system_metrics() -> tuple[float, float]:
        """收集系统指标（同步方法，通过 asyncio.to_thread 调用）"""
        import psutil
        cpu = psutil.cpu_percent(interval=1) / 100.0
        mem = psutil.virtual_memory().percent / 100.0
        return cpu, mem
