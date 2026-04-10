from enum import Enum
from typing import Any, Optional, TypeVar

# 定义泛型，用于后续类型提示
T = TypeVar("T", bound="PlatformType")


class PlatformCategory(Enum):
    """
    平台大类定义。
    最佳实践：使用枚举管理分类，避免魔法字符串（Magic Strings）。
    """

    LLM = "llm"
    DATABASE = "database"
    CACHE = "cache"
    STORAGE = "storage"
    SANDBOX = "sandbox"
    MONITORING = "monitoring"
    MESSAGING = "messaging"
    UNKNOWN = "unknown"


class PlatformType(Enum):
    """
    平台类型枚举（增强版）。
    设计模式：元组初始化（Tuple Initialization）。
    优势：在定义时完成 O(1) 级别的类别绑定，彻底消除 if-else 逻辑。
    """

    # LLM 平台
    OPENAI = ("openai", PlatformCategory.LLM)
    DEEPSEEK = ("deepseek", PlatformCategory.LLM)
    CLAUDE = ("claude", PlatformCategory.LLM)
    GEMINI = ("gemini", PlatformCategory.LLM)
    MOCK_LLM = ("mock_llm", PlatformCategory.LLM)

    # 数据库 & 缓存
    POSTGRESQL = ("postgresql", PlatformCategory.DATABASE)
    SQLITE = ("sqlite", PlatformCategory.DATABASE)
    REDIS = ("redis", PlatformCategory.CACHE)

    # 存储 & 沙箱
    S3 = ("s3", PlatformCategory.STORAGE)
    LOCAL_STORAGE = ("local_storage", PlatformCategory.STORAGE)
    E2B = ("e2b", PlatformCategory.SANDBOX)
    DOCKER = ("docker", PlatformCategory.SANDBOX)

    def __init__(self, val: str, cat: PlatformCategory):
        """
        核心逻辑：正确处理多值枚举。
        Python Enum 内部使用 _value_ 来存储成员的主值。
        """
        self._value_ = val
        self.platform_category = cat

    @property
    def category(self) -> str:
        """获取类别字符串，用于前端展示或路径拼接"""
        return self.platform_category.value

    @classmethod
    def from_string(cls: type[T], value: str) -> T:
        """
        世界顶尖实践：高性能查找。
        相比 next(...) 迭代，使用字典映射在成员较多时速度更快。
        """
        if not hasattr(cls, "_value_map"):
            cls._value_map = {m.value: m for m in cls}

        member = cls._value_map.get(value)
        if member:
            return member
        raise ValueError(f"❌ [Security Alert] Unknown platform type requested: {value}")


# ==========================================
# 平台适配器层 (Platform Adapter Layer)
# ==========================================


class PlatformAdapter:
    """
    抽象基类。
    最佳实践：定义明确的类属性，强制子类实现。
    """

    PLATFORM: Optional[PlatformType] = None

    @classmethod
    def get_info(cls) -> str:
        """返回适配器的元数据信息"""
        if not cls.PLATFORM:
            return "Base Adapter"
        return f"Adapter for {cls.PLATFORM.value} (Category: {cls.PLATFORM.category})"

    @classmethod
    def validate_config(cls, config: dict[str, Any]) -> bool:
        """通用的配置验证接口"""
        raise NotImplementedError("Subclasses must implement validate_config")


class OpenAIAdapter(PlatformAdapter):
    """
    具体实现示例。
    """

    PLATFORM = PlatformType.OPENAI

    @classmethod
    def validate_config(cls, config: dict[str, Any]) -> bool:
        # 顶级实践：严格校验生产环境变量
        return bool(config.get("api_key") and config.get("api_key").startswith("sk-"))


# ==========================================
# 使用示例 (Usage)
# ==========================================
# p_type = PlatformType.from_string("openai")
# print(f"Current Category: {p_type.category}")  # 输出: llm
# print(OpenAIAdapter.get_info())                # 输出: Adapter for openai (Category: llm)
