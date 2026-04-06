import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Protocol, Set
from pydantic import BaseModel, Field, field_validator
from ..llm.protocol import BaseLLMProtocol, LLMMessage
from ..llm.logger import logger
from ..llm.circuit_breaker import circuit_breaker
from ..state import StateManager


class TaskStep(BaseModel):
    """任务步骤模型"""
    id: str = Field(..., description="任务步骤的唯一标识符")
    description: str = Field(..., description="任务步骤的详细描述")
    priority: int = Field(..., ge=1, le=5, description="任务优先级，1-5，5最高")
    dependencies: List[str] = Field(default_factory=list, description="依赖的任务步骤ID列表")
    expected_output: Optional[str] = Field(None, description="预期输出描述")
    status: str = Field(default="pending", description="任务状态：pending, in_progress, completed, failed")
    actual_output: Optional[str] = Field(None, description="实际输出")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    @field_validator('priority')
    def validate_priority(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('优先级必须在1-5之间')
        return v


class ExecutionPlan(BaseModel):
    """执行计划模型"""
    plan_id: str = Field(..., description="计划的唯一标识符")
    original_input: str = Field(..., description="原始用户输入")
    steps: List[TaskStep] = Field(..., description="任务步骤列表")
    created_at: str = Field(..., description="计划创建时间")
    updated_at: str = Field(..., description="计划更新时间")
    status: str = Field(default="active", description="计划状态：active, completed, failed, cancelled")
    total_steps: int = Field(..., description="总任务数")
    completed_steps: int = Field(default=0, description="已完成任务数")


class TaskOrchestratorProtocol(Protocol):
    """任务编排器接口"""
    async def plan(self, user_input: str) -> ExecutionPlan:
        """生成任务计划"""
        ...
    
    async def update_plan(self, current_plan: ExecutionPlan, observation: str) -> ExecutionPlan:
        """更新任务计划"""
        ...
    
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """执行任务计划"""
        ...


class OrchestratorError(Exception):
    """编排器基础异常"""
    pass


class PlanGenerationError(OrchestratorError):
    """计划生成异常"""
    pass


class PlanUpdateError(OrchestratorError):
    """计划更新异常"""
    pass


class PlanExecutionError(OrchestratorError):
    """计划执行异常"""
    pass


class TaskOrchestrator:
    """任务编排器实现"""
    
    def __init__(self, llm_protocol: BaseLLMProtocol, state_manager: Optional[StateManager] = None):
        """
        初始化任务编排器
        
        Args:
            llm_protocol: LLM协议实例
            state_manager: 状态管理器实例
        """
        self.llm_protocol = llm_protocol
        self.state_manager = state_manager
        self._plan_cache: Dict[str, ExecutionPlan] = {}
        self._cache_ttl = 3600  # 缓存过期时间（秒）
    
    @circuit_breaker
    async def plan(self, user_input: str) -> ExecutionPlan:
        """
        生成任务计划
        
        Args:
            user_input: 用户输入
            
        Returns:
            ExecutionPlan: 执行计划
            
        Raises:
            PlanGenerationError: 计划生成失败
        """
        # 检查缓存
        cache_key = f"plan:{hash(user_input)}"
        if cache_key in self._plan_cache:
            cached_plan = self._plan_cache[cache_key]
            if self._is_cache_valid(cached_plan):
                logger.info(f"Using cached plan for input: {user_input[:50]}...")
                return cached_plan
        
        # 构建系统提示词，注入上下文
        system_prompt = self._build_system_prompt()
        
        # 构建消息列表
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_input)
        ]

        # 调用 LLM 生成计划
        try:
            response = await self.llm_protocol.generate(messages)
            
            # 解析 JSON 响应
            plan_data = self._parse_llm_response(response.text)
            
            # 验证并创建 ExecutionPlan 对象
            plan = self._create_execution_plan(plan_data, user_input)
            
            # 记录拆解出的子任务
            for step in plan.steps:
                logger.info(f"TaskStep created: ID={step.id}, Description={step.description}, Priority={step.priority}")
            
            # 缓存计划
            self._plan_cache[cache_key] = plan
            
            # 保存到状态管理器
            if self.state_manager:
                await self.state_manager.save_plan(plan)
            
            return plan
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response as JSON: {e}"
            logger.error(error_msg)
            logger.error(f"LLM response: {response.text}")
            # 处理非结构化回复，返回默认计划
            return self._create_default_plan(user_input)
        except Exception as e:
            error_msg = f"Error generating plan: {e}"
            logger.error(error_msg)
            # 出错时返回默认计划
            return self._create_default_plan(user_input)
    
    @circuit_breaker
    async def update_plan(self, current_plan: ExecutionPlan, observation: str) -> ExecutionPlan:
        """
        更新任务计划
        
        Args:
            current_plan: 当前执行计划
            observation: 执行观察结果
            
        Returns:
            ExecutionPlan: 更新后的执行计划
            
        Raises:
            PlanUpdateError: 计划更新失败
        """
        # 构建系统提示词，注入上下文
        system_prompt = self._build_update_system_prompt()
        
        # 构建消息列表
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=f"Current plan: {current_plan.model_dump_json()}\n\nObservation: {observation}")
        ]

        # 调用 LLM 更新计划
        try:
            response = await self.llm_protocol.generate(messages)
            
            # 解析 JSON 响应
            plan_data = self._parse_llm_response(response.text)
            
            # 验证并创建 ExecutionPlan 对象
            updated_plan = self._create_execution_plan(plan_data, current_plan.original_input)
            updated_plan.status = current_plan.status
            
            # 记录更新后的子任务
            for step in updated_plan.steps:
                logger.info(f"Updated TaskStep: ID={step.id}, Description={step.description}, Priority={step.priority}")
            
            # 保存到状态管理器
            if self.state_manager:
                await self.state_manager.update_plan(updated_plan)
            
            return updated_plan
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response as JSON: {e}"
            logger.error(error_msg)
            logger.error(f"LLM response: {response.text}")
            # 处理非结构化回复，返回当前计划
            return current_plan
        except Exception as e:
            error_msg = f"Error updating plan: {e}"
            logger.error(error_msg)
            # 出错时返回当前计划
            return current_plan
    
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """
        执行任务计划
        
        Args:
            plan: 执行计划
            
        Returns:
            ExecutionPlan: 执行完成的计划
            
        Raises:
            PlanExecutionError: 计划执行失败
        """
        logger.info(f"Starting execution of plan: {plan.plan_id}")
        
        # 按照优先级和依赖关系执行任务
        executed_steps: Set[str] = set()
        
        while plan.completed_steps < plan.total_steps:
            # 找出可执行的任务（依赖已完成）
            executable_steps = [
                step for step in plan.steps 
                if step.status == "pending" 
                and all(dep in executed_steps for dep in step.dependencies)
            ]
            
            if not executable_steps:
                # 没有可执行的任务，可能存在循环依赖
                logger.warning("No executable steps found, checking for circular dependencies")
                break
            
            # 按优先级排序
            executable_steps.sort(key=lambda x: x.priority, reverse=True)
            
            # 执行任务
            for step in executable_steps:
                try:
                    logger.info(f"Executing step: {step.id} - {step.description}")
                    step.status = "in_progress"
                    
                    # 这里应该调用实际的任务执行器
                    # 暂时模拟执行
                    await self._simulate_task_execution(step)
                    
                    step.status = "completed"
                    step.actual_output = f"Completed: {step.description}"
                    plan.completed_steps += 1
                    executed_steps.add(step.id)
                    
                    logger.info(f"Completed step: {step.id} - {step.description}")
                    
                except Exception as e:
                    logger.error(f"Failed to execute step {step.id}: {e}")
                    step.status = "failed"
                    step.error_message = str(e)
                    plan.status = "failed"
                    
                    # 保存失败状态
                    if self.state_manager:
                        await self.state_manager.update_plan(plan)
                    
                    raise PlanExecutionError(f"Failed to execute step {step.id}: {e}")
        
        # 更新计划状态
        if plan.completed_steps == plan.total_steps:
            plan.status = "completed"
            logger.info(f"Plan {plan.plan_id} completed successfully")
        
        # 保存到状态管理器
        if self.state_manager:
            await self.state_manager.update_plan(plan)
        
        return plan
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return f"""
你是超级AI团队的核心任务编排器，负责将复杂的用户请求拆解为结构化的任务计划。

当前上下文：
- 日期：2026-04-06
- 环境：超级AI团队生产环境

你的任务：
1. 分析用户输入，识别其中的复杂任务
2. 将任务拆解为多个子任务，每个子任务应该：
   - 有明确的目标和描述
   - 有合理的优先级（1-5，5最高）
   - 明确依赖关系（如果有的话）
3. 生成符合以下 JSON Schema 的计划：

{{
  "plan_id": "唯一标识符",
  "original_input": "原始用户输入",
  "steps": [
    {{
      "id": "步骤ID",
      "description": "步骤描述",
      "priority": 优先级,
      "dependencies": ["依赖步骤ID列表"],
      "expected_output": "预期输出描述"
    }}
  ],
  "created_at": "当前时间",
  "updated_at": "当前时间",
  "status": "active",
  "total_steps": 步骤总数,
  "completed_steps": 0
}}

重要要求：
- 只返回 JSON 格式的计划，不要有任何其他文字
- 确保 JSON 格式正确，可直接解析
- 任务拆解要合理，步骤之间逻辑清晰
- 优先级设置要符合任务的重要性和紧急性
"""
    
    def _build_update_system_prompt(self) -> str:
        """构建更新计划的系统提示词"""
        return f"""
你是超级AI团队的核心任务编排器，负责根据执行结果动态调整任务计划。

当前上下文：
- 日期：2026-04-06
- 环境：超级AI团队生产环境

你的任务：
1. 分析当前计划和执行观察结果
2. 如果执行结果符合预期，保持计划不变
3. 如果执行结果不符合预期或任务失败，重新思考并修改剩余的计划
4. 生成符合以下 JSON Schema 的更新计划：

{{
  "plan_id": "唯一标识符",
  "original_input": "原始用户输入",
  "steps": [
    {{
      "id": "步骤ID",
      "description": "步骤描述",
      "priority": 优先级,
      "dependencies": ["依赖步骤ID列表"],
      "expected_output": "预期输出描述"
    }}
  ],
  "created_at": "当前时间",
  "updated_at": "当前时间",
  "status": "active",
  "total_steps": 步骤总数,
  "completed_steps": 已完成步骤数
}}

重要要求：
- 只返回 JSON 格式的计划，不要有任何其他文字
- 确保 JSON 格式正确，可直接解析
- 基于观察结果合理调整计划
- 保持任务的逻辑连贯性
"""
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析LLM响应
        
        Args:
            response_text: LLM响应文本
            
        Returns:
            Dict[str, Any]: 解析后的计划数据
        """
        # 提取JSON部分
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx+1]
            return json.loads(json_str)
        raise json.JSONDecodeError("No valid JSON found in response", response_text, 0)
    
    def _create_execution_plan(self, plan_data: Dict[str, Any], original_input: str) -> ExecutionPlan:
        """
        创建执行计划
        
        Args:
            plan_data: 计划数据
            original_input: 原始用户输入
            
        Returns:
            ExecutionPlan: 执行计划
        """
        # 确保计划数据完整
        if "plan_id" not in plan_data:
            plan_data["plan_id"] = str(uuid.uuid4())
        if "original_input" not in plan_data:
            plan_data["original_input"] = original_input
        if "created_at" not in plan_data:
            plan_data["created_at"] = datetime.now().isoformat()
        if "updated_at" not in plan_data:
            plan_data["updated_at"] = datetime.now().isoformat()
        if "status" not in plan_data:
            plan_data["status"] = "active"
        if "total_steps" not in plan_data:
            plan_data["total_steps"] = len(plan_data.get("steps", []))
        if "completed_steps" not in plan_data:
            plan_data["completed_steps"] = 0
        
        # 确保步骤数据完整
        for step in plan_data.get("steps", []):
            if "id" not in step:
                step["id"] = str(uuid.uuid4())
            if "status" not in step:
                step["status"] = "pending"
        
        return ExecutionPlan(**plan_data)
    
    def _create_default_plan(self, user_input: str) -> ExecutionPlan:
        """
        创建默认计划，当 LLM 无法生成有效计划时使用
        
        Args:
            user_input: 用户输入
            
        Returns:
            ExecutionPlan: 默认执行计划
        """
        default_plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            original_input=user_input,
            steps=[
                TaskStep(
                    id=str(uuid.uuid4()),
                    description="分析用户请求",
                    priority=5,
                    dependencies=[],
                    expected_output="理解用户的具体需求"
                ),
                TaskStep(
                    id=str(uuid.uuid4()),
                    description="执行用户请求",
                    priority=4,
                    dependencies=[],
                    expected_output="完成用户要求的任务"
                ),
                TaskStep(
                    id=str(uuid.uuid4()),
                    description="验证执行结果",
                    priority=3,
                    dependencies=[],
                    expected_output="确保任务执行成功"
                )
            ],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            total_steps=3
        )
        
        logger.warning("Created default plan due to LLM failure")
        return default_plan
    
    def _is_cache_valid(self, plan: ExecutionPlan) -> bool:
        """
        检查缓存是否有效
        
        Args:
            plan: 执行计划
            
        Returns:
            bool: 缓存是否有效
        """
        created_time = datetime.fromisoformat(plan.created_at)
        current_time = datetime.now()
        return (current_time - created_time).total_seconds() < self._cache_ttl
    
    async def _simulate_task_execution(self, step: TaskStep) -> None:
        """
        模拟任务执行
        
        Args:
            step: 任务步骤
        """
        # 模拟执行延迟
        import asyncio
        await asyncio.sleep(0.5)
        # 这里可以集成实际的任务执行器
        pass


# 工厂函数
def create_task_orchestrator(
    llm_protocol: BaseLLMProtocol,
    state_manager: Optional[StateManager] = None
) -> TaskOrchestrator:
    """
    创建任务编排器实例
    
    Args:
        llm_protocol: LLM协议实例
        state_manager: 状态管理器实例
        
    Returns:
        TaskOrchestrator: 任务编排器实例
    """
    return TaskOrchestrator(llm_protocol, state_manager)
