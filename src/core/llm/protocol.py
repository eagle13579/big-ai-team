from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str
    content: str


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class LLMResponse(BaseModel):
    text: str
    usage: Optional[Dict[str, int]] = None
    tool_calls: Optional[List[ToolCall]] = None


class BaseLLMProtocol(ABC):
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> AsyncGenerator[LLMResponse, None]:
        """Generate a stream of responses from the LLM"""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """Generate a single response from the LLM"""
        pass


class LLMProtocolError(Exception):
    """Base exception for LLM protocol errors"""
    pass


class LLMConnectionError(LLMProtocolError):
    """Exception raised when there's a connection error"""
    pass


class LLMEmptyResponseError(LLMProtocolError):
    """Exception raised when the LLM returns an empty response"""
    pass
