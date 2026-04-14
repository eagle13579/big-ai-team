import pytest

from src.evolution.strategies.base import BaseStrategy, StrategyResult, StrategyPriority, SystemState
from src.evolution.strategies.performance import PerformanceStrategy
from src.evolution.strategies.reliability import ReliabilityStrategy
from src.evolution.strategies.capability import CapabilityStrategy
from src.evolution.strategies.knowledge import KnowledgeStrategy


class TestSystemState:

    def test_default_values(self):
        state = SystemState()
        assert state.cpu_usage == 0.0
        assert state.memory_usage == 0.0
        assert state.error_rate == 0.0
        assert state.active_tasks == 0

    def test_custom_values(self):
        state = SystemState(cpu_usage=0.8, memory_usage=0.6, error_rate=0.05)
        assert state.cpu_usage == 0.8
        assert state.memory_usage == 0.6
        assert state.error_rate == 0.05


class TestStrategyResult:

    def test_default_values(self):
        result = StrategyResult(strategy_name="test", success=True)
        assert result.strategy_name == "test"
        assert result.improvement == 0.0
        assert result.rollback_possible is True

    def test_custom_values(self):
        result = StrategyResult(
            strategy_name="perf",
            success=True,
            improvement=0.15,
            actions_taken=["scaled_up"],
        )
        assert result.success is True
        assert result.improvement == 0.15
        assert len(result.actions_taken) == 1


class TestStrategyPriority:

    def test_priority_values(self):
        assert StrategyPriority.LOW == 1
        assert StrategyPriority.MEDIUM == 2
        assert StrategyPriority.HIGH == 3
        assert StrategyPriority.CRITICAL == 4


class TestPerformanceStrategy:

    @pytest.fixture
    def strategy(self):
        return PerformanceStrategy()

    def test_name(self, strategy):
        assert strategy.name == "performance"

    @pytest.mark.asyncio
    async def test_evaluate_high_cpu(self, strategy):
        state = SystemState(cpu_usage=0.9, memory_usage=0.5)
        score = await strategy.evaluate(state)
        assert score > 0.1

    @pytest.mark.asyncio
    async def test_evaluate_low_cpu(self, strategy):
        state = SystemState(cpu_usage=0.2, memory_usage=0.3)
        score = await strategy.evaluate(state)
        assert score < 0.5

    @pytest.mark.asyncio
    async def test_execute(self, strategy):
        state = SystemState(cpu_usage=0.9)
        result = await strategy.execute(state)
        assert result.strategy_name == "performance"
        assert isinstance(result.success, bool)
        assert isinstance(result.improvement, float)

    @pytest.mark.asyncio
    async def test_rollback(self, strategy):
        result = StrategyResult(strategy_name="performance", success=False)
        ok = await strategy.rollback(result)
        assert isinstance(ok, bool)


class TestReliabilityStrategy:

    @pytest.fixture
    def strategy(self):
        return ReliabilityStrategy()

    def test_name(self, strategy):
        assert strategy.name == "reliability"

    @pytest.mark.asyncio
    async def test_evaluate_high_error_rate(self, strategy):
        state = SystemState(error_rate=0.2)
        score = await strategy.evaluate(state)
        assert score > 0.1

    @pytest.mark.asyncio
    async def test_evaluate_low_error_rate(self, strategy):
        state = SystemState(error_rate=0.01)
        score = await strategy.evaluate(state)
        assert score < 0.5

    @pytest.mark.asyncio
    async def test_execute(self, strategy):
        state = SystemState(error_rate=0.2)
        result = await strategy.execute(state)
        assert result.strategy_name == "reliability"


class TestCapabilityStrategy:

    @pytest.fixture
    def strategy(self):
        return CapabilityStrategy()

    def test_name(self, strategy):
        assert strategy.name == "capability"

    @pytest.mark.asyncio
    async def test_evaluate(self, strategy):
        state = SystemState()
        score = await strategy.evaluate(state)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_execute(self, strategy):
        state = SystemState()
        result = await strategy.execute(state)
        assert result.strategy_name == "capability"


class TestKnowledgeStrategy:

    @pytest.fixture
    def strategy(self):
        return KnowledgeStrategy()

    def test_name(self, strategy):
        assert strategy.name == "knowledge"

    @pytest.mark.asyncio
    async def test_evaluate(self, strategy):
        state = SystemState()
        score = await strategy.evaluate(state)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_execute(self, strategy):
        state = SystemState()
        result = await strategy.execute(state)
        assert result.strategy_name == "knowledge"
