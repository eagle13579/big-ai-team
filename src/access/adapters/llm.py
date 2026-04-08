from typing import Dict, Any, Optional
from abc import abstractmethod
import httpx
from .base import BaseAdapter, AdapterContext
from .registry import adapter_registry


class LLMAdapter(BaseAdapter[Dict[str, Any]]):
    """LLM 适配器基类"""
    
    async def execute(self, operation: str, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """执行 LLM 操作"""
        if operation == "generate":
            return await self.generate(params, context)
        elif operation == "health_check":
            return await self._health_check(context)
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    @abstractmethod
    async def generate(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """生成文本"""
        pass
    
    async def _health_check(self, context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "platform": self.platform,
            "timestamp": context.timestamp.isoformat() if context else None
        }


class OpenAIAdapter(LLMAdapter):
    """OpenAI 适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = self.config.config.get("api_key")
        self.base_url = self.config.config.get("base_url", "https://api.openai.com/v1/chat/completions")
        self.client = None
    
    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self._set_initialized(True)
        return True
    
    async def generate(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """生成文本"""
        if not self.client:
            await self.initialize(context)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": params.get("model", "gpt-4"),
            "messages": params.get("messages", [{"role": "user", "content": params.get("prompt", "")}]),
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 1000),
            "stop": params.get("stop")
        }
        
        try:
            response = await self.client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data["model"],
                "token_usage": data.get("usage", {}),
                "finish_reason": data["choices"][0].get("finish_reason", "stop")
            }
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")
    
    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        if self.client:
            await self.client.aclose()
            self.client = None
        self._set_initialized(False)
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "api_key_set": bool(self.api_key),
            "base_url": self.base_url
        }


class DeepSeekAdapter(LLMAdapter):
    """DeepSeek 适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = self.config.config.get("api_key")
        self.base_url = self.config.config.get("base_url", "https://api.deepseek.com/v1/chat/completions")
        self.client = None
    
    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self._set_initialized(True)
        return True
    
    async def generate(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """生成文本"""
        if not self.client:
            await self.initialize(context)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": params.get("model", "deepseek-chat"),
            "messages": params.get("messages", [{"role": "user", "content": params.get("prompt", "")}]),
            "temperature": params.get("temperature", 0.7),
            "max_tokens": params.get("max_tokens", 1000),
            "stop": params.get("stop")
        }
        
        try:
            response = await self.client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data["model"],
                "token_usage": data.get("usage", {}),
                "finish_reason": data["choices"][0].get("finish_reason", "stop")
            }
        except Exception as e:
            raise Exception(f"DeepSeek API call failed: {str(e)}")
    
    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        if self.client:
            await self.client.aclose()
            self.client = None
        self._set_initialized(False)
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "api_key_set": bool(self.api_key),
            "base_url": self.base_url
        }


class MockLLMAdapter(LLMAdapter):
    """模拟 LLM 适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.response_template = self.config.config.get("response_template", "模拟响应: {prompt}")
    
    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        self._set_initialized(True)
        return True
    
    async def generate(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """生成文本"""
        prompt = params.get("prompt", "")
        messages = params.get("messages", [])
        if messages:
            prompt = messages[-1].get("content", prompt)
        
        content = self.response_template.format(prompt=prompt)
        
        return {
            "content": content,
            "model": "mock-llm",
            "token_usage": {"prompt_tokens": len(prompt), "completion_tokens": len(content), "total_tokens": len(prompt) + len(content)},
            "finish_reason": "stop"
        }
    
    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        self._set_initialized(False)
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "response_template": self.response_template
        }


# 注册 LLM 适配器
adapter_registry.register("openai", OpenAIAdapter)
adapter_registry.register("deepseek", DeepSeekAdapter)
adapter_registry.register("mock_llm", MockLLMAdapter)
