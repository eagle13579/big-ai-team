from enum import Enum


class PlatformType(Enum):
    """平台类型枚举"""
    # LLM 平台
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"
    MISTRAL = "mistral"
    GEMINI = "gemini"
    MOCK_LLM = "mock_llm"
    
    # 数据库平台
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    
    # 缓存平台
    REDIS = "redis"
    MEMORY_CACHE = "memory_cache"
    
    # 存储平台
    LOCAL_STORAGE = "local_storage"
    S3 = "s3"
    GCS = "gcs"
    AZURE_BLOB = "azure_blob"
    
    # 执行沙箱平台
    E2B = "e2b"
    DOCKER = "docker"
    
    # 监控平台
    LANGSMITH = "langsmith"
    OPENTELEMETRY = "opentelemetry"
    
    # 消息队列平台
    RABBITMQ = "rabbitmq"
    KAFKA = "kafka"
    
    @classmethod
    def from_string(cls, value: str) -> 'PlatformType':
        """从字符串创建平台类型"""
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Unknown platform type: {value}")
    
    @property
    def category(self) -> str:
        """获取平台类别"""
        if self in [cls.OPENAI, cls.DEEPSEEK, cls.CLAUDE, cls.MISTRAL, cls.GEMINI, cls.MOCK_LLM]:
            return "llm"
        elif self in [cls.POSTGRESQL, cls.SQLITE, cls.MYSQL, cls.MONGODB]:
            return "database"
        elif self in [cls.REDIS, cls.MEMORY_CACHE]:
            return "cache"
        elif self in [cls.LOCAL_STORAGE, cls.S3, cls.GCS, cls.AZURE_BLOB]:
            return "storage"
        elif self in [cls.E2B, cls.DOCKER]:
            return "sandbox"
        elif self in [cls.LANGSMITH, cls.OPENTELEMETRY]:
            return "monitoring"
        elif self in [cls.RABBITMQ, cls.KAFKA]:
            return "messaging"
        else:
            return "unknown"
