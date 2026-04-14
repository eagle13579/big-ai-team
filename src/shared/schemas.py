import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class IntentRequest(BaseModel):
    raw_input: str
    platform: str
    user_id: str
    context: dict[str, Any]


class TaskRequest(BaseModel):
    plan_id: str
    description: str
    assignee: str
    input_params: dict[str, Any] | None = None
    dependencies: list[str] | None = []


class TaskResponse(BaseModel):
    task_id: str
    plan_id: str
    status: str
    created_at: datetime


class MCPRequest(BaseModel):
    method: str
    params: dict[str, Any]
    agent_token: str | None = None
    id: str | None = Field(default_factory=lambda: str(uuid.uuid4()))


class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Any | None = None
    error: dict[str, Any] | None = None
    id: str | None = None


class MemoryCreate(BaseModel):
    session_id: str
    user_id: str
    role_name: str | None = None
    content: str
    embedding: list[float] | None = None
    metadata: dict[str, Any] | None = {}


class MemoryResponse(BaseModel):
    id: str
    session_id: str
    user_id: str
    role_name: str | None = None
    content: str
    created_at: datetime


class SkillManifest(BaseModel):
    name: str
    version: str
    description: str
    parameters: dict[str, Any]
    return_type: str


# ============================================================
# Evolution Module Types
# ============================================================

EvolutionPhase = Literal["perceive", "cognize", "decide", "plan", "execute", "feedback"]


class SystemState(BaseModel):
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    error_rate: float = 0.0
    active_tasks: int = 0
    completed_tasks: int = 0
    avg_response_time: float = 0.0
    uptime_seconds: float = 0.0
    extra: dict[str, float] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    summary: str = ""
    bottlenecks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)


class Decision(BaseModel):
    strategy_name: str
    priority: float = 0.5
    rationale: str = ""
    expected_improvement: float = 0.0
    actions: list[str] = Field(default_factory=list)


class EvolutionLogEntry(BaseModel):
    cycle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phase: EvolutionPhase = "perceive"
    timestamp: datetime = Field(default_factory=datetime.now)
    state: SystemState = Field(default_factory=SystemState)
    analysis: AnalysisResult | None = None
    decisions: list[Decision] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0


class StrategyResult(BaseModel):
    strategy_name: str
    success: bool = False
    actions_taken: list[str] = Field(default_factory=list)
    improvement: float = 0.0
    before_state: dict[str, float] = Field(default_factory=dict)
    after_state: dict[str, float] = Field(default_factory=dict)
    rollback_possible: bool = True
    error_message: str | None = None


# ============================================================
# Execution Module Types
# ============================================================

class AssemblyStep(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    purpose: str = ""


class AssemblyPlan(BaseModel):
    analysis: str = ""
    steps: list[AssemblyStep] = Field(default_factory=list)
    expected_outcome: str = ""


class AssemblyStepResult(BaseModel):
    step: int
    tool: str
    status: Literal["success", "failed", "error", "skipped"] = "success"
    result: Any | None = None
    error: str | None = None


class AssemblyExecutionResult(BaseModel):
    status: Literal["success", "partial", "error"] = "success"
    steps: list[AssemblyStepResult] = Field(default_factory=list)
    context_log: str = ""
    total_steps: int = 0
    successful_steps: int = 0


class FeedbackResult(BaseModel):
    status: Literal["success", "failed"] = "success"
    iterations: int = 0
    message: str = ""
    last_errors: int = 0


class IterationRecord(BaseModel):
    iteration: int = 0
    test_results: list[dict[str, Any]] = Field(default_factory=list)
    parsed_errors: int = 0
    status: str = ""
    feedback: str | None = None
    suggestions_count: int = 0


# ============================================================
# Scheduler Module Types
# ============================================================

AgentStatus = Literal["idle", "busy", "offline", "error"]


class AgentTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    assigned_agent: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    priority: int = 5
    async_execution: bool = False
    expected_output: str = ""
    output_schema: dict[str, Any] | None = None
    context_from: list[str] = Field(default_factory=list)
    max_retries: int = 3


class TaskAssignment(BaseModel):
    task_id: str
    agent_id: str
    task_description: str
    priority: int = 5


class TaskResult(BaseModel):
    task_id: str
    agent_id: str
    status: Literal["success", "failed", "timeout"] = "success"
    data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    execution_time_ms: float = 0.0
    error: str | None = None


class AggregationResult(BaseModel):
    status: Literal["success", "partial", "failed"] = "success"
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    results: list[TaskResult] = Field(default_factory=list)
    consistency_score: float = 1.0


class ResolutionResult(BaseModel):
    resolved: bool = True
    winner: str | None = None
    confidence: float = 0.0
    method: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class CoordinationResult(BaseModel):
    status: Literal["success", "partial", "failed"] = "success"
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    task_results: list[TaskResult] = Field(default_factory=list)
    execution_time_ms: float = 0.0


# ============================================================
# Role Module Types
# ============================================================

class TaskInput(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class TaskOutput(BaseModel):
    task_id: str = ""
    status: Literal["success", "failed", "partial"] = "success"
    result: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# Planner Module Types
# ============================================================

class PlanStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    assignee: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    priority: int = 5
    status: str = "pending"


class Plan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str = ""
    steps: list[PlanStep] = Field(default_factory=list)
    parallel_groups: list[list[str]] = Field(default_factory=list)
    dag: dict[str, list[str]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================
# LLM Protocol Interface
# ============================================================

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProtocol(Protocol):
    async def generate(self, prompt: str, temperature: float = 0.7) -> str: ...

    async def generate_decision(self, goal: str, context: str) -> dict[str, Any]: ...


@runtime_checkable
class Executable(Protocol):
    async def execute(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]: ...


@runtime_checkable
class Evolvable(Protocol):
    async def evaluate(self, state: SystemState) -> float: ...
    async def evolve(self, state: SystemState) -> StrategyResult: ...
