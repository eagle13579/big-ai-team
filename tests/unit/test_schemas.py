import pytest

from src.shared.schemas import (
    EvolutionLogEntry,
    AnalysisResult,
    Decision,
    StrategyResult as SchemaStrategyResult,
    SystemState as SchemaSystemState,
    AssemblyStep,
    AssemblyPlan,
    AssemblyStepResult,
    AssemblyExecutionResult,
    FeedbackResult,
    IterationRecord,
    AgentTask,
    TaskAssignment,
    TaskResult,
    AggregationResult,
    ResolutionResult,
    CoordinationResult,
    TaskInput,
    TaskOutput,
    PlanStep,
    Plan,
    LLMProtocol,
    Executable,
    Evolvable,
)


class TestEvolutionTypes:

    def test_system_state_defaults(self):
        state = SchemaSystemState()
        assert state.cpu_usage == 0.0
        assert state.memory_usage == 0.0
        assert state.error_rate == 0.0

    def test_analysis_result_defaults(self):
        result = AnalysisResult()
        assert result.summary == ""
        assert result.bottlenecks == []
        assert result.opportunities == []

    def test_decision(self):
        d = Decision(strategy_name="perf", priority=0.8, rationale="high cpu")
        assert d.strategy_name == "perf"
        assert d.priority == 0.8

    def test_evolution_log_entry(self):
        entry = EvolutionLogEntry(phase="perceive")
        assert entry.phase == "perceive"
        assert entry.cycle_id is not None

    def test_strategy_result(self):
        r = SchemaStrategyResult(strategy_name="perf", success=True, improvement=0.1)
        assert r.strategy_name == "perf"
        assert r.success is True


class TestExecutionTypes:

    def test_assembly_step(self):
        step = AssemblyStep(tool="web_search", args={"query": "test"}, purpose="search")
        assert step.tool == "web_search"

    def test_assembly_plan(self):
        plan = AssemblyPlan(analysis="test", steps=[], expected_outcome="result")
        assert plan.analysis == "test"

    def test_assembly_step_result(self):
        r = AssemblyStepResult(step=1, tool="web_search", status="success")
        assert r.step == 1

    def test_assembly_execution_result(self):
        r = AssemblyExecutionResult(status="success", total_steps=3, successful_steps=3)
        assert r.status == "success"

    def test_feedback_result(self):
        r = FeedbackResult(status="success", iterations=2)
        assert r.status == "success"

    def test_iteration_record(self):
        r = IterationRecord(iteration=1, parsed_errors=0, status="success")
        assert r.iteration == 1


class TestSchedulerTypes:

    def test_agent_task(self):
        t = AgentTask(description="search task", priority=5)
        assert t.description == "search task"
        assert t.id is not None

    def test_task_assignment(self):
        a = TaskAssignment(task_id="t1", agent_id="a1", task_description="test")
        assert a.task_id == "t1"

    def test_task_result(self):
        r = TaskResult(task_id="t1", agent_id="a1", status="success", confidence=0.9)
        assert r.confidence == 0.9

    def test_aggregation_result(self):
        r = AggregationResult(total_tasks=5, successful_tasks=4, failed_tasks=1)
        assert r.total_tasks == 5

    def test_resolution_result(self):
        r = ResolutionResult(resolved=True, winner="agent_1")
        assert r.resolved is True

    def test_coordination_result(self):
        r = CoordinationResult(status="success", total_tasks=3, completed_tasks=3)
        assert r.completed_tasks == 3


class TestRoleTypes:

    def test_task_input(self):
        t = TaskInput(task_type="search", description="find info")
        assert t.task_type == "search"
        assert t.task_id is not None

    def test_task_output(self):
        o = TaskOutput(status="success", result="found")
        assert o.status == "success"


class TestPlannerTypes:

    def test_plan_step(self):
        s = PlanStep(description="search", assignee="agent_1")
        assert s.description == "search"
        assert s.step_id is not None

    def test_plan(self):
        p = Plan(goal="complete task")
        assert p.goal == "complete task"
        assert p.plan_id is not None


class TestProtocols:

    def test_llm_protocol_is_runtime_checkable(self):
        class MockLLM:
            async def generate(self, prompt: str, temperature: float = 0.7) -> str:
                return "test"
            async def generate_decision(self, goal: str, context: str) -> dict:
                return {}
        assert isinstance(MockLLM(), LLMProtocol)

    def test_executable_is_runtime_checkable(self):
        class MockExecutor:
            async def execute(self, tool_name: str, args: dict) -> dict:
                return {}
        assert isinstance(MockExecutor(), Executable)

    def test_evolvable_is_runtime_checkable(self):
        class MockEvolvable:
            async def evaluate(self, state) -> float:
                return 0.5
            async def evolve(self, state) -> SchemaStrategyResult:
                return SchemaStrategyResult(strategy_name="test")
        assert isinstance(MockEvolvable(), Evolvable)
