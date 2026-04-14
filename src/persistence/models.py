import enum

from sqlalchemy import ARRAY, JSON, TIMESTAMP, Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.sql import func

from .database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class Memory(Base):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    session_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False)
    role_name = Column(String(32))
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # 使用 JSON 存储嵌入向量
    mem_metadata = Column(JSON, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    plan_id = Column(UUID(as_uuid=True), nullable=False)
    parent_task_id = Column(UUID(as_uuid=True), nullable=True)
    description = Column(Text, nullable=False)
    assignee = Column(String(32), nullable=False)
    status = Column(ENUM(TaskStatus), default=TaskStatus.PENDING)
    input_params = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    dependencies = Column(JSON, default=[])
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class SkillRegistry(Base):
    """技能注册表"""
    __tablename__ = "skill_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(64), unique=True, nullable=False)
    version = Column(String(16), nullable=True)
    manifest = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    last_called_at = Column(TIMESTAMP(timezone=True), nullable=True)


class Feedback(Base):
    """用户反馈"""
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(String(64), nullable=False)
    task_id = Column(UUID(as_uuid=True), nullable=True)
    skill_name = Column(String(64), nullable=True)
    rating = Column(Integer, nullable=False)  # 1-5 星
    comment = Column(Text, nullable=True)
    feedback_type = Column(String(32), nullable=False)  # task, skill, system
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
