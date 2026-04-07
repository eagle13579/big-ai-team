from sqlalchemy import Column, String, Text, Boolean, Integer, TIMESTAMP, ARRAY, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.sql import func
from .database import Base
import enum

class TaskStatus(str, enum.Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRYING = 'retrying'

class Memory(Base):
    __tablename__ = 'memories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    session_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False)
    role_name = Column(String(32))
    content = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float))  # 使用ARRAY类型替代vector
    memory_metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Task(Base):
    __tablename__ = 'tasks'
    
    task_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    plan_id = Column(UUID(as_uuid=True), nullable=False)
    parent_task_id = Column(UUID(as_uuid=True), nullable=True)
    description = Column(Text, nullable=False)
    assignee = Column(String(32), nullable=False)
    status = Column(ENUM(TaskStatus), default=TaskStatus.PENDING)
    input_params = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    dependencies = Column(ARRAY(UUID(as_uuid=True)), default=[])
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class SkillRegistry(Base):
    __tablename__ = 'skill_registry'
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(64), unique=True, nullable=False)
    version = Column(String(16), nullable=True)
    manifest = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    last_called_at = Column(TIMESTAMP(timezone=True), nullable=True)
