from typing import Dict, Any, Optional
from .protocol import BaseLLMProtocol
from .client import OpenAICompatibleClient
from .config import LLMConfig, LLMProviderConfig


class LLMFactory:
    @staticmethod
    def create(
        protocol: str,
        config: Optional[Dict[str, Any]] = None,
        llm_config: Optional[LLMConfig] = None
    ) -> BaseLLMProtocol:
        """Create an LLM client based on the specified protocol and configuration"""
        if protocol == "openai_compatible":
            if llm_config:
                return OpenAICompatibleClient(
                    base_url=llm_config.base_url,
                    model=llm_config.model,
                    api_key=llm_config.api_key,
                    timeout=llm_config.timeout,
                    max_retries=llm_config.max_retries
                )
            elif config:
                return OpenAICompatibleClient(
                    base_url=config.get("base_url", "https://api.ace-browser.com/v1"),
                    model=config.get("model", "ace-nova-2026-pro"),
                    api_key=config.get("api_key"),
                    timeout=config.get("timeout", 30),
                    max_retries=config.get("max_retries", 3)
                )
            else:
                # 使用默认配置
                default_config = LLMConfig()
                return OpenAICompatibleClient(
                    base_url=default_config.base_url,
                    model=default_config.model,
                    api_key=default_config.api_key,
                    timeout=default_config.timeout,
                    max_retries=default_config.max_retries
                )
        else:
            raise ValueError(f"Unsupported LLM protocol: {protocol}")

    @staticmethod
    def create_from_provider_config(
        protocol: str,
        provider_config: LLMProviderConfig
    ) -> BaseLLMProtocol:
        """从提供商配置创建 LLM 客户端"""
        if protocol == "openai_compatible":
            return LLMFactory.create(protocol, llm_config=provider_config.openai_compatible)
        else:
            raise ValueError(f"Unsupported LLM protocol: {protocol}")

    @staticmethod
    def get_supported_protocols() -> list:
        """Get a list of supported LLM protocols"""
        return ["openai_compatible"]
