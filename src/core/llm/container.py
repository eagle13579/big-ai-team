from dependency_injector import containers, providers
from .config import LLMConfig, LLMProviderConfig
from .factory import LLMFactory
from .client import OpenAICompatibleClient


class LLMContainer(containers.DeclarativeContainer):
    """LLM 依赖注入容器"""
    # 配置提供者
    config = providers.Singleton(LLMProviderConfig)
    
    # 客户端提供者
    openai_compatible_client = providers.Factory(
        OpenAICompatibleClient,
        base_url=config.provided.openai_compatible.base_url,
        model=config.provided.openai_compatible.model,
        api_key=config.provided.openai_compatible.api_key,
        timeout=config.provided.openai_compatible.timeout,
        max_retries=config.provided.openai_compatible.max_retries
    )
    
    # 工厂提供者
    factory = providers.Singleton(LLMFactory)
    
    # 协议客户端提供者
    llm_client = providers.Factory(
        factory.provided.create,
        protocol="openai_compatible",
        llm_config=config.provided.openai_compatible
    )
