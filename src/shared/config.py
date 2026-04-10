from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field, validator
from typing import Optional, Dict, Any, List
import os
import json
import time
import logging
from pathlib import Path
from functools import lru_cache

# 导入敏感信息管理器
try:
    from .secret_manager import SecretManager
    secret_manager = SecretManager()
except ImportError:
    secret_manager = None

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    🚀 Ace Agent 全局配置中心 (2026 生产级标准)
    整合了数据库、安全、Agent 决策及监控链路
    """
    
    # 配置版本管理
    CONFIG_VERSION: str = "3.0.0"
    
    # --- 1. 基础项目配置 ---
    PROJECT_NAME: str = "big-ai-team"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # --- 2. 数据库与缓存配置 ---
    DATABASE_URL: str
    REDIS_URL: str

    # --- 3. 安全与认证配置 ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=1440)

    # --- 4. AI 与 Agent 核心配置 ---
    # 外部模型 API
    OPENAI_API_KEY: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None
    MOONSHOT_API_KEY: Optional[str] = None
    
    # Agent 行为控制
    AGENT_MAX_STEPS: int = Field(default=10, ge=1, le=100)  # 允许 Agent 自适应循环的最大次数
    AGENT_OUTPUT_DIR: str = "output"  # Agent 生成文档的存放路径
    AGENT_TIMEOUT: int = Field(default=300, ge=30, le=3600)  # 任务强制超时时间 (秒)
    AGENT_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=1.0)  # 模型采样温度
    
    # 沙箱与执行环境
    E2B_API_KEY: Optional[str] = None

    # --- 5. 链路追踪与监控 ---
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None

    # --- 6. 环境配置 ---
    ENV_MODE: str = Field(default="development", pattern="^(development|production|test)$")
    TIMEZONE: str = "Asia/Shanghai"

    # 模型配置
    DEFAULT_MODEL_NAME: str = "deepseek-chat"
    OPENAI_MODEL_NAME: str = "gpt-4o-2026"
    ANTHROPIC_MODEL_NAME: str = "claude-3-5-sonnet-latest"
    GEMINI_MODEL_NAME: str = "gemini-1.5-pro"
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"
    ZHIPU_MODEL_NAME: str = "glm-4"
    MOONSHOT_MODEL_NAME: str = "moonshot-v1-128k"

    # 浏览器配置
    ACE_PRIVACY_MODE: bool = True
    ALLOWED_DOMAINS: str = "github.com,google.com,wikipedia.org,arxiv.org"

    # 性能配置
    CACHE_TTL: int = 3600  # 缓存过期时间（秒）
    MAX_CONCURRENT_TASKS: int = 10  # 最大并发任务数
    RATE_LIMIT_PER_MINUTE: int = 60  # 每分钟请求限制

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    @field_validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    @field_validator('REDIS_URL')
    def validate_redis_url(cls, v):
        if not v:
            raise ValueError("REDIS_URL is required")
        return v

    @field_validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    # 获取解密后的敏感信息
    def get_secret(self, key: str) -> Optional[str]:
        """
        获取解密后的敏感信息
        """
        if secret_manager:
            return secret_manager.get_secret(key)
        return getattr(self, key, None)

    # 获取允许的域名列表
    @property
    def allowed_domains_list(self) -> List[str]:
        """
        获取允许的域名列表
        """
        return [domain.strip() for domain in self.ALLOWED_DOMAINS.split(",")]


class ConfigManager:
    """
    配置管理器，支持配置热重载和版本管理
    """
    def __init__(self):
        # 根据环境变量加载不同的配置文件
        env_mode = os.environ.get("ENV_MODE", "development")
        env_file = f".env.{env_mode}"
        
        # 如果环境特定配置文件不存在，使用默认配置文件
        if not Path(env_file).exists():
            env_file = ".env"
        
        self._env_file = Path(env_file)
        self._settings = self._load_settings()
        self._last_load_time = time.time()
        self._config_file_mtime = self._env_file.stat().st_mtime if self._env_file.exists() else 0
        logger.info(f"🔧 配置管理器初始化完成，加载配置文件: {self._env_file}")

    def _load_settings(self) -> Settings:
        """
        加载配置
        """
        # 临时设置环境变量，指定配置文件
        os.environ["PYDANTIC_SETTINGS_ENV_FILE"] = str(self._env_file)
        return Settings()

    @lru_cache(maxsize=1)
    def get_settings(self) -> Settings:
        """
        获取配置，支持热重载
        """
        # 检查配置文件是否被修改
        if self._env_file.exists():
            current_mtime = self._env_file.stat().st_mtime
            if current_mtime > self._config_file_mtime:
                # 清除缓存
                self.get_settings.cache_clear()
                self._settings = self._load_settings()
                self._config_file_mtime = current_mtime
                self._last_load_time = time.time()
                logger.info(f"📝 配置文件已更新，重新加载配置 (版本: {self._settings.CONFIG_VERSION})")
        return self._settings

    def get_config_version(self) -> str:
        """
        获取配置版本
        """
        return self.get_settings().CONFIG_VERSION

    def export_config(self, path: str) -> None:
        """
        导出配置到文件
        """
        config_dict = self.get_settings().model_dump()
        # 移除敏感信息
        sensitive_keys = ["SECRET_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "DEEPSEEK_API_KEY", "ZHIPU_API_KEY", "MOONSHOT_API_KEY", "E2B_API_KEY"]
        for key in sensitive_keys:
            if key in config_dict:
                config_dict[key] = "[REDACTED]"
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        logger.info(f"📤 配置已导出到 {path}")

    def import_config(self, path: str) -> None:
        """
        从文件导入配置
        """
        if not Path(path).exists():
            raise FileNotFoundError(f"配置文件 {path} 不存在")
        
        with open(path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
        
        # 更新环境变量
        for key, value in config_dict.items():
            if value is not None and value != "[REDACTED]":
                os.environ[key] = str(value)
        
        # 清除缓存并重新加载配置
        self.get_settings.cache_clear()
        self._settings = self._load_settings()
        self._last_load_time = time.time()
        logger.info(f"📥 配置已从 {path} 导入")

    def validate_config(self) -> bool:
        """
        验证配置的有效性
        """
        try:
            settings = self.get_settings()
            # 验证必填字段
            required_fields = ["DATABASE_URL", "REDIS_URL", "SECRET_KEY"]
            for field in required_fields:
                if not getattr(settings, field):
                    logger.error(f"❌ 配置验证失败: {field} 不能为空")
                    return False
            
            # 验证 SECRET_KEY 长度
            if len(settings.SECRET_KEY) < 32:
                logger.error("❌ 配置验证失败: SECRET_KEY 长度必须至少为 32 个字符")
                return False
            
            logger.info("✅ 配置验证通过")
            return True
        except Exception as e:
            logger.error(f"❌ 配置验证失败: {str(e)}")
            return False


# 实例化配置管理器
config_manager = ConfigManager()

# 获取配置实例
settings = config_manager.get_settings()

# 自动创建 Agent 输出目录
if not os.path.exists(settings.AGENT_OUTPUT_DIR):
    os.makedirs(settings.AGENT_OUTPUT_DIR)
    logger.info(f"📁 已创建 Agent 工作目录: {settings.AGENT_OUTPUT_DIR}")

# 验证配置
config_manager.validate_config()