from abc import ABC, abstractmethod
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from src.shared.config import settings
from src.shared.logging import logger


class LLMRequest(BaseModel):
    """LLM 请求参数"""

    prompt: str = Field(..., description="提示词")
    model: str = Field(default="gpt-4", description="模型名称")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=1000, description="最大token数")
    stop: Optional[list[str]] = Field(default=None, description="停止词")


class LLMResponse(BaseModel):
    """LLM 响应结果"""

    content: str = Field(..., description="响应内容")
    model: str = Field(..., description="使用的模型")
    token_usage: dict[str, int] = Field(default_factory=dict, description="token使用情况")
    finish_reason: str = Field(default="stop", description="结束原因")


class LLMProtocol(ABC):
    """LLM 协议基类"""

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """生成响应"""
        pass


class OpenAIProtocol(LLMProtocol):
    """OpenAI 协议实现"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def generate(self, request: LLMRequest) -> LLMResponse:
        """生成响应"""
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        payload = {
            "model": request.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stop": request.stop,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                model = data["model"]
                token_usage = data.get("usage", {})
                finish_reason = data["choices"][0].get("finish_reason", "stop")

                return LLMResponse(
                    content=content,
                    model=model,
                    token_usage=token_usage,
                    finish_reason=finish_reason,
                )
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {str(e)}")
            raise


class ClaudeProtocol(LLMProtocol):
    """Claude 协议实现"""

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.base_url = "https://api.anthropic.com/v1/messages"

    def generate(self, request: LLMRequest) -> LLMResponse:
        """生成响应"""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": request.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stop_sequences": request.stop,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                content = data["content"][0]["text"]
                model = data["model"]
                token_usage = data.get("usage", {})
                finish_reason = data.get("stop_reason", "stop")

                return LLMResponse(
                    content=content,
                    model=model,
                    token_usage=token_usage,
                    finish_reason=finish_reason,
                )
        except Exception as e:
            logger.error(f"Claude API 调用失败: {str(e)}")
            raise


class MockLLMProtocol(LLMProtocol):
    """模拟 LLM 协议实现"""

    def generate(self, request: LLMRequest) -> LLMResponse:
        """生成响应"""
        return LLMResponse(
            content=f"Mock 响应: {request.prompt}",
            model=request.model,
            token_usage={
                "prompt_tokens": len(request.prompt),
                "completion_tokens": 100,
                "total_tokens": len(request.prompt) + 100,
            },
            finish_reason="stop",
        )


class LLMFactory:
    """LLM 工厂类"""

    @staticmethod
    def create_protocol(model_type: str) -> LLMProtocol:
        """创建 LLM 协议实例"""
        if model_type == "openai":
            return OpenAIProtocol()
        elif model_type == "claude":
            return ClaudeProtocol()
        else:
            return MockLLMProtocol()
