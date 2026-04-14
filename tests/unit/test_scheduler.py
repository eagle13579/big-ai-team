import pytest

from src.execution.scheduler.agent_pool import AgentPool, AgentInfo, AgentStatus
from src.execution.scheduler.task_distributor import TaskDistributor
from src.execution.scheduler.result_aggregator import ResultAggregator
from src.execution.scheduler.conflict_resolver import ConflictResolver


class TestAgentPool:

    @pytest.fixture
    def pool(self):
        return AgentPool()

    def test_register_agent(self, pool):
        agent = AgentInfo(agent_id="agent_1", role="worker", capabilities=["search", "analysis"])
        result = pool.register(agent)
        assert result is True
        assert pool.get_agent("agent_1") is not None

    def test_unregister_agent(self, pool):
        agent = AgentInfo(agent_id="agent_1", role="worker", capabilities=["search"])
        pool.register(agent)
        result = pool.unregister("agent_1")
        assert result is True
        assert pool.get_agent("agent_1") is None

    def test_find_available(self, pool):
        pool.register(AgentInfo(agent_id="agent_1", role="worker", capabilities=["search"], status=AgentStatus.IDLE))
        pool.register(AgentInfo(agent_id="agent_2", role="worker", capabilities=["search"], status=AgentStatus.BUSY))
        available = pool.find_available()
        assert len(available) == 1
        assert available[0].agent_id == "agent_1"

    def test_update_status(self, pool):
        pool.register(AgentInfo(agent_id="agent_1", role="worker", capabilities=["search"], status=AgentStatus.IDLE))
        pool.update_status("agent_1", AgentStatus.BUSY, "task_1")
        agent = pool.get_agent("agent_1")
        assert agent.status == AgentStatus.BUSY
        assert agent.current_task == "task_1"

    def test_find_by_capability(self, pool):
        pool.register(AgentInfo(agent_id="agent_1", role="worker", capabilities=["search", "analysis"]))
        pool.register(AgentInfo(agent_id="agent_2", role="worker", capabilities=["coding"]))
        found = pool.find_available(capability="search")
        assert len(found) == 1
        assert found[0].agent_id == "agent_1"

    def test_agent_success_rate(self):
        agent = AgentInfo(agent_id="a1", role="worker", completed_tasks=8, failed_tasks=2)
        assert agent.success_rate == 0.8

    def test_pool_stats(self, pool):
        pool.register(AgentInfo(agent_id="agent_1", role="worker"))
        stats = pool.get_pool_stats()
        assert stats["total_agents"] == 1


class TestTaskDistributor:

    @pytest.fixture
    def distributor(self):
        pool = AgentPool()
        return TaskDistributor(agent_pool=pool)

    def test_distribute_empty(self, distributor):
        result = distributor.distribute([])
        assert result == []


class TestResultAggregator:

    @pytest.fixture
    def aggregator(self):
        return ResultAggregator()

    def test_aggregate_empty(self, aggregator):
        result = aggregator.aggregate([])
        assert result is not None

    def test_aggregate_results(self, aggregator):
        results = [
            {"task_id": "t1", "status": "success", "data": {"answer": 42}},
            {"task_id": "t2", "status": "success", "data": {"answer": 43}},
        ]
        result = aggregator.aggregate(results)
        assert result is not None


class TestConflictResolver:

    @pytest.fixture
    def resolver(self):
        return ConflictResolver()

    def test_resolve_no_conflict(self, resolver):
        results = [{"task_id": "t1", "status": "success", "data": {"answer": 42}}]
        resolved = resolver.resolve(results)
        assert resolved is not None

    def test_resolve_with_conflict(self, resolver):
        results = [
            {"task_id": "t1", "status": "success", "data": {"answer": 42}, "confidence": 0.9},
            {"task_id": "t1", "status": "success", "data": {"answer": 43}, "confidence": 0.7},
        ]
        resolved = resolver.resolve(results)
        assert resolved is not None
