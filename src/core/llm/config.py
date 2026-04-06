from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional


class LLMConfig(BaseSettings):
    """LLM 配置类"""
    # 基础配置
    base_url: str = "https://api.ace-browser.com/v1"
    model: str = "ace-nova-2026-pro"
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    
    # 高级配置
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # 安全配置
    rate_limit: int = 100  # 每分钟请求数
    request_timeout: int = 30  # 请求超时时间（秒）
    
    class Config:
        env_file = ".env"
        env_prefix = "LLM_"


class LLMProviderConfig(BaseSettings):
    """LLM 提供商配置"""
    openai_compatible: LLMConfig = LLMConfig()
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
