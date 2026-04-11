from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class CacheSettings(BaseSettings):
    """
    缓存配置
    """
    # 本地缓存配置
    LOCAL_CACHE_SIZE: int = 1000  # 本地缓存大小限制
    LOCAL_CACHE_DEFAULT_TTL: int = 300  # 本地缓存默认过期时间（秒）
    
    # Redis 缓存配置
    REDIS_URL: str = "redis://localhost:6379/0"  # Redis 连接 URL
    REDIS_DEFAULT_TTL: int = 3600  # Redis 默认过期时间（秒）
    
    # 缓存键前缀
    CACHE_KEY_PREFIX: str = "big_ai_team"  # 缓存键前缀
    
    # 缓存策略
    CACHE_ENABLED: bool = True  # 是否启用缓存
    CACHE_WARMUP_ENABLED: bool = True  # 是否启用缓存预热
    
    # 缓存统计
    CACHE_STATS_ENABLED: bool = True  # 是否启用缓存统计
    
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="allow"
    )


# 单例实例
cache_settings = CacheSettings()
