from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    # 数据库配置
    DATABASE_URL: str
    
    # Redis配置
    REDIS_URL: str
    
    # 安全配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "big-ai-team"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    # 外部服务配置
    OPENAI_API_KEY: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None
    
    # 沙箱配置
    E2B_API_KEY: Optional[str] = None
    
    # 监控配置
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
