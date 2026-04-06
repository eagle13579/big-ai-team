from typing import Dict, Optional, List, Any
import asyncio
import logging
import json
import re
from pydantic import BaseModel, Field, ValidationError
from .base import BaseTool, ToolResult, LLMProtocol
from .exceptions import ToolNotFoundError, ToolTimeoutError, LLMError, ToolError
from .security import security_manager
from .monitoring import monitoring_manager

logger = logging.getLogger(__name__)

class ToolCall(BaseModel):
    """ 工具调用模型 """
    tool_name: str
    args: Dict[str, Any]

class ToolDispatcher:
    """ 工具分发器，负责管理和分发工具调用 """
    
    def __init__(self, llm_protocol: LLMProtocol):
        self.tools: Dict[str, BaseTool] = {}
        self.llm_protocol = llm_protocol

    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_available_tools(self) -> List[BaseTool]:
        return list(self.tools.values())

    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)

    async def dispatch(self, step_description: str, timeout: int = 30, user: Optional[str] = None) -> ToolResult:
        """ 分发工具调用 """
        try:
            monitoring_manager.record_audit_log(
                tool_name="dispatcher",
                action="dispatch_start",
                user=user,
                details={"step_description": step_description}
            )

            # 核心优化 1：通过强化的 LLM 分析获取结构化调用指令
            tool_call = await self._analyze_step_with_llm(step_description)
            
            monitoring_manager.record_audit_log(
                tool_name=tool_call.tool_name,
                action="llm_analysis",
                user=user,
                details={"args": tool_call.args}
            )

            # 验证工具是否存在
            if tool_call.tool_name not in self.tools:
                error = ToolNotFoundError(tool_call.tool_name)
                return ToolResult(success=False, error=str(error))

            # 检查权限
            if not security_manager.check_permission(tool_call.tool_name):
                error_msg = f"Tool {tool_call.tool_name} does not have required permissions"
                return ToolResult(success=False, error=error_msg)

            # 执行工具
            tool = self.tools[tool_call.tool_name]
            # 核心优化 2：在这里将 LLM 解析出的 Dict 传入，BaseTool 会通过 args_schema 进行二次强校验
            result = await asyncio.wait_for(
                tool._execute_with_validation(**tool_call.args),
                timeout=timeout
            )

            monitoring_manager.record_audit_log(
                tool_name=tool_call.tool_name,
                action="execution_complete",
                user=user,
                details={"success": result.success, "error": result.error}
            )
            
            return result

        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"Execution timed out after {timeout}s")
        except Exception as e:
            logger.error(f"Error in dispatch: {str(e)}")
            return ToolResult(success=False, error=str(e))

    async def _analyze_step_with_llm(self, step_description: str) -> ToolCall:
        """ 使用 LLM 分析步骤描述，并确保返回合法的结构化数据 """
        
        tools_info = "\n".join([
            f"- {tool.name}: {tool.description}\n  Args schema: {tool.args_schema.model_json_schema()}" 
            for tool in self.tools.values()
        ])
        
        prompt = f"""
Analyze the step description and return the appropriate tool and parameters in JSON format.
Available tools:
{tools_info}

Step description: {step_description}

You MUST return ONLY a JSON object:
{{
  "tool_name": "exact_tool_name",
  "args": {{ "key": "value" }}
}}
"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = await self.llm_protocol.generate(prompt)
                
                # 核心优化 3：鲁棒的 JSON 提取逻辑
                tool_call_data = self._extract_json_from_response(response)
                
                # 核心优化 4：使用 Pydantic 模型强制类型转换
                return ToolCall(**tool_call_data)

            except (json.JSONDecodeError, ValidationError, LLMError) as e:
                logger.warning(f"Attempt {attempt + 1} failed to parse LLM response: {str(e)}")
                if attempt == max_retries - 1:
                    raise LLMError(f"Failed to get valid tool call after {max_retries} attempts: {str(e)}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """ 从 LLM 响应中提取 JSON 块，处理 Markdown 标记和杂质文本 """
        # 1. 尝试寻找 Markdown 代码块 ```json ... ```
        json_block_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_block_match:
            content = json_block_match.group(1)
        else:
            # 2. 尝试寻找第一对花括号 { ... }
            braces_match = re.search(r'(\{.*\})', text, re.DOTALL)
            content = braces_match.group(1) if braces_match else text

        # 3. 清理不可见字符并解析
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            # 最后的尝试：清理可能干扰解析的常见字符
            cleaned_content = content.replace('\n', '').replace('\\', '')
            return json.loads(cleaned_content)