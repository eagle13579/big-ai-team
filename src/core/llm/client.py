import json
import asyncio
from typing import List, AsyncGenerator, Optional, Dict, Any
from .protocol import (
    BaseLLMProtocol, LLMMessage, LLMResponse, ToolCall,
    LLMConnectionError, LLMEmptyResponseError, LLMProtocolError
)
from .logger import logger
from .http_client import http_client_manager
from .circuit_breaker import circuit_breaker


class OpenAICompatibleClient(BaseLLMProtocol):
    def __init__(
        self,
        base_url: str = "https://api.ace-browser.com/v1",
        model: str = "ace-nova-2026-pro",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {api_key}"} if api_key else {})
        }
        self.client = None

    async def __aenter__(self):
        self.client = await http_client_manager.get_client(self.base_url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 客户端由 http_client_manager 管理，不需要在这里关闭
        pass

    @circuit_breaker
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> AsyncGenerator[LLMResponse, None]:
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [msg.model_dump() for msg in messages],
            "stream": True,
            **kwargs
        }

        logger.debug(f"Generating stream with model: {self.model}")
        
        # 获取客户端
        if not self.client:
            self.client = await http_client_manager.get_client(self.base_url)
        
        retries = 0
        while retries < self.max_retries:
            try:
                async with self.client.post(
                    "/chat/completions", 
                    json=payload,
                    headers=self.headers
                ) as response:
                    response.raise_for_status()
                    logger.debug(f"Received response with status: {response.status_code}")

                    async for chunk in response.aiter_text():
                        if not chunk.strip():
                            continue

                        for line in chunk.splitlines():
                            line = line.strip()
                            if line.startswith("data:"):
                                data = line[5:]
                                if data == "[DONE]":
                                    logger.debug("Stream completed")
                                    return

                                try:
                                    chunk_data = json.loads(data)
                                    if "choices" in chunk_data:
                                        choice = chunk_data["choices"][0]
                                        if "delta" in choice:
                                            delta = choice["delta"]
                                            text = delta.get("content", "")
                                            tool_calls = None

                                            if "tool_calls" in delta:
                                                tool_calls = [
                                                    ToolCall(
                                                        name=tc["name"],
                                                        arguments=tc.get("arguments", {})
                                                    )
                                                    for tc in delta["tool_calls"]
                                                ]

                                            if text or tool_calls:
                                                response = LLMResponse(
                                                    text=text,
                                                    usage=chunk_data.get("usage"),
                                                    tool_calls=tool_calls
                                                )
                                                await self.on_response_received(response)
                                                yield response
                                except json.JSONDecodeError as e:
                                    logger.warning(f"Failed to decode chunk: {e}")
                                    continue
                return
            except Exception as e:
                retries += 1
                logger.warning(f"Error (attempt {retries}/{self.max_retries}): {str(e)}")
                if retries >= self.max_retries:
                    logger.error(f"Max retries reached: {str(e)}")
                    raise LLMConnectionError(
                        f"Failed to connect to LLM API: {str(e)}"
                    )
                # 指数退避
                await asyncio.sleep(2 ** retries * 0.1)


    @circuit_breaker
    async def generate(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [msg.model_dump() for msg in messages],
            "stream": False,
            **kwargs
        }

        logger.debug(f"Generating response with model: {self.model}")
        
        # 获取客户端
        if not self.client:
            self.client = await http_client_manager.get_client(self.base_url)
        
        retries = 0
        while retries < self.max_retries:
            try:
                # 尝试从缓存获取
                cache_key = f"{self.base_url}/chat/completions"
                cached_response = http_client_manager.get_from_cache(
                    cache_key, "POST", payload
                )
                if cached_response:
                    logger.debug("Using cached response")
                    return LLMResponse(**cached_response)
                
                response = await self.client.post(
                    "/chat/completions", 
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                logger.debug(f"Received response with status: {response.status_code}")

                data = response.json()
                if "choices" in data:
                    choice = data["choices"][0]
                    text = choice.get("message", {}).get("content", "")

                    if not text or text.strip() == "":
                        logger.warning("LLM returned an empty response")
                        raise LLMEmptyResponseError(
                            "LLM returned an empty response"
                        )

                    tool_calls = None
                    if "tool_calls" in choice.get("message", {}):
                        tool_calls = [
                            ToolCall(
                                name=tc["name"],
                                arguments=tc.get("arguments", {})
                            )
                            for tc in choice["message"]["tool_calls"]
                        ]

                    llm_response = LLMResponse(
                        text=text,
                        usage=data.get("usage"),
                        tool_calls=tool_calls
                    )
                    
                    # 缓存响应
                    http_client_manager.set_to_cache(
                        cache_key, "POST", payload, llm_response.model_dump()
                    )
                    
                    await self.on_response_received(llm_response)
                    logger.debug(f"Generated response successfully")
                    return llm_response
                else:
                    logger.error("Invalid response format from LLM API")
                    raise LLMProtocolError(
                        "Invalid response format from LLM API"
                    )
            except LLMEmptyResponseError:
                raise
            except Exception as e:
                retries += 1
                logger.warning(f"Error (attempt {retries}/{self.max_retries}): {str(e)}")
                if retries >= self.max_retries:
                    logger.error(f"Max retries reached: {str(e)}")
                    raise LLMConnectionError(
                        f"Failed to connect to LLM API: {str(e)}"
                    )
                # 指数退避
                await asyncio.sleep(2 ** retries * 0.1)


    async def on_response_received(self, response: LLMResponse) -> None:
        """Hook for processing responses, e.g., for multi-language consistency audit"""
        pass
