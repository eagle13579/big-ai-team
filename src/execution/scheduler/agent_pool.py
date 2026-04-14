import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.shared.logging import logger


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentInfo:
    agent_id: str
    role: str
    capabilities: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    current_task: str | None = None
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_execution_time: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        total = self.completed_tasks + self.failed_tasks
        return self.completed_tasks / total if total > 0 else 1.0

    @property
    def load_score(self) -> float:
        if self.status == AgentStatus.BUSY:
            return 1.0
        elif self.status == AgentStatus.ERROR:
            return 0.8
        elif self.status == AgentStatus.OFFLINE:
            return 1.0
        return 0.0


class AgentPool:
    """Agent池管理 - 基于角色+能力+负载动态管理Agent实例"""

    def __init__(self, max_agents: int = 20):
        self._agents: dict[str, AgentInfo] = {}
        self._max_agents = max_agents

    def register(self, agent: AgentInfo) -> bool:
        """注册Agent"""
        if len(self._agents) >= self._max_agents:
            logger.warning(f"⚠️ Agent池已满 ({self._max_agents})，无法注册 {agent.agent_id}")
            return False

        self._agents[agent.agent_id] = agent
        logger.info(f"🤖 注册Agent: {agent.agent_id} (角色: {agent.role}, 能力: {agent.capabilities})")
        return True

    def unregister(self, agent_id: str) -> bool:
        """注销Agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"🤖 注销Agent: {agent_id}")
            return True
        return False

    def get_agent(self, agent_id: str) -> AgentInfo | None:
        """获取Agent信息"""
        return self._agents.get(agent_id)

    def find_available(self, role: str | None = None, capability: str | None = None) -> list[AgentInfo]:
        """查找可用的Agent"""
        candidates = []

        for agent in self._agents.values():
            if agent.status != AgentStatus.IDLE:
                continue

            if role and agent.role != role:
                continue

            if capability and capability not in agent.capabilities:
                continue

            candidates.append(agent)

        candidates.sort(key=lambda a: (a.load_score, -a.success_rate, a.avg_execution_time))
        return candidates

    def find_best_for_task(self, required_role: str, required_capabilities: list[str]) -> AgentInfo | None:
        """为任务找到最佳Agent"""
        candidates = self.find_available(role=required_role)

        if required_capabilities:
            capable = [
                a for a in candidates
                if all(cap in a.capabilities for cap in required_capabilities)
            ]
            if capable:
                candidates = capable

        if not candidates:
            candidates = self.find_available()
            if not candidates:
                return None

        return candidates[0]

    def update_status(self, agent_id: str, status: AgentStatus, current_task: str | None = None):
        """更新Agent状态"""
        agent = self._agents.get(agent_id)
        if agent:
            agent.status = status
            agent.current_task = current_task
            agent.last_heartbeat = time.time()

    def record_task_completion(self, agent_id: str, success: bool, execution_time: float = 0.0):
        """记录任务完成"""
        agent = self._agents.get(agent_id)
        if agent:
            if success:
                agent.completed_tasks += 1
            else:
                agent.failed_tasks += 1

            if execution_time > 0:
                total = agent.completed_tasks + agent.failed_tasks
                agent.avg_execution_time = (
                    (agent.avg_execution_time * (total - 1) + execution_time) / total
                )

            agent.status = AgentStatus.IDLE
            agent.current_task = None

    def get_pool_stats(self) -> dict[str, Any]:
        """获取池统计"""
        status_counts = {}
        for status in AgentStatus:
            status_counts[status.value] = sum(
                1 for a in self._agents.values() if a.status == status
            )

        return {
            "total_agents": len(self._agents),
            "max_agents": self._max_agents,
            "status_distribution": status_counts,
            "avg_success_rate": (
                sum(a.success_rate for a in self._agents.values()) / len(self._agents)
                if self._agents else 0.0
            ),
        }

    def heartbeat_check(self, timeout_seconds: int = 300) -> list[str]:
        """心跳检查，返回超时的Agent ID"""
        now = time.time()
        timed_out = []

        for agent_id, agent in self._agents.items():
            if now - agent.last_heartbeat > timeout_seconds:
                agent.status = AgentStatus.OFFLINE
                timed_out.append(agent_id)

        if timed_out:
            logger.warning(f"⚠️ {len(timed_out)} 个Agent心跳超时: {timed_out}")

        return timed_out
