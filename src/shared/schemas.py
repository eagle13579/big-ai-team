import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class IntentRequest(BaseModel):
    """意图请求模型"""

    raw_input: str
    platform: str
    user_id: str
    context: dict[str, Any]


class TaskRequest(BaseModel):
    """任务请求模型"""

    plan_id: str
    description: str
    assignee: str
    input_params: Optional[dict[str, Any]] = None
    dependencies: Optional[list[str]] = []


class TaskResponse(BaseModel):
    """任务响应模型"""

    task_id: str
    plan_id: str
    status: str
    created_at: datetime


class MCPRequest(BaseModel):
    """MCP请求模型"""

    method: str
    params: dict[str, Any]
    agent_token: Optional[str] = None
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


class MCPResponse(BaseModel):
    """MCP响应模型"""

    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[dict[str, Any]] = None
    id: Optional[str] = None


class MemoryCreate(BaseModel):
    """记忆创建模型"""

    session_id: str
    user_id: str
    role_name: Optional[str] = None
    content: str
    embedding: Optional[list[float]] = None
    metadata: Optional[dict[str, Any]] = {}


class MemoryResponse(BaseModel):
    """记忆响应模型"""

    id: str
    session_id: str
    user_id: str
    role_name: Optional[str] = None
    content: str
    created_at: datetime


class SkillManifest(BaseModel):
    """技能清单模型"""

    name: str
    version: str
    description: str
    parameters: dict[str, Any]
    return_type: str
