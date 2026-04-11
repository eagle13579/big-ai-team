import os
import sys
from pathlib import Path
from typing import Any, TypedDict

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入监控模块
from core.monitoring import core_performance_monitor, init_core_monitoring
from src.shared.logging import logger

# 初始化监控
init_core_monitoring()


class MemoryContext(TypedDict, total=False):
    """记忆上下文类型定义"""
    importance: str
    project: str
    timestamp: float
    source: str


class MemoryItem(TypedDict):
    """记忆项类型定义"""
    content: Any
    context: MemoryContext | None
    tags: list[str] | None
    score: float


class RunParams(TypedDict, total=False):
    """run 方法参数类型定义"""
    action: str
    content: Any
    context: MemoryContext | None
    tags: list[str] | None
    query: str
    limit: int


class StatusResponse(TypedDict):
    """状态响应类型定义"""
    status: str
    path: str
    version: str


class MemPalaceCore:
    """
    [核心逻辑层] 负责处理具体的记忆存储与检索逻辑。

    设计准则：
    1. 独立性：不依赖 Bridge 层的具体实现。
    2. 稳定性：所有输入参数均经过默认值处理。
    3. 契约化：通过 run() 方法统一对接 Bridge 层。
    """

    def __init__(self, palace_path: str = "~/.mempalace/palace") -> None:
        """
        初始化核心引擎。

        Args:
            palace_path: 存储路径。支持 ~ 路径解析。
        """
        self.palace_path: str = os.path.abspath(os.path.expanduser(palace_path))
        # 工业级实践：在初始化阶段确保存储目录存在
        try:
            os.makedirs(self.palace_path, exist_ok=True)
            logger.info(f"核心引擎就绪，存储路径: {self.palace_path}")
        except Exception as e:
            logger.error(f"无法创建存储目录: {e}")

    @core_performance_monitor
    def add_memory(
        self, 
        content: Any, 
        context: MemoryContext | None = None, 
        tags: list[str] | None = None
    ) -> bool:
        """
        添加记忆项。

        Args:
            content: 记忆内容
            context: 记忆上下文信息
            tags: 记忆标签列表

        Returns:
            bool: 添加是否成功
        """
        # 实际业务逻辑应在此扩展，例如写入数据库或本地文件
        logger.info(f"✅ [Core] 已处理记忆内容: {content}")
        return True

    @core_performance_monitor
    def search(
        self, 
        query: str, 
        limit: int = 5, 
        context: MemoryContext | None = None
    ) -> list[MemoryItem]:
        """
        检索相关记忆。

        Args:
            query: 搜索查询字符串
            limit: 返回结果数量限制
            context: 搜索上下文信息

        Returns:
            List[MemoryItem]: 匹配的记忆项列表
        """
        logger.info(f"🔍 [Core] 正在检索: {query} (Limit: {limit})")
        return []

    @core_performance_monitor
    def run(self, params: RunParams) -> bool | list[MemoryItem] | StatusResponse:
        """
        [契约适配器]
        此方法是唯一暴露给 bridge/interface.py 的入口，
        确保了即使核心类增加 100 个方法，接口契约依然保持简洁。

        Args:
            params: 包含操作类型和参数的字典

        Returns:
            Union[bool, List[MemoryItem], StatusResponse]: 根据操作类型返回不同结果
        """
        action: str = params.get("action", "status")

        if action == "add":
            return self.add_memory(
                content=params.get("content"),
                context=params.get("context"),
                tags=params.get("tags"),
            )

        if action == "search":
            return self.search(
                query=params.get("query", ""),
                limit=params.get("limit", 5),
                context=params.get("context"),
            )

        # 默认返回状态信息
        return {"status": "active", "path": self.palace_path, "version": "1.0.0"}


# 向后兼容：如果外部直接引用函数而非类
@core_performance_monitor
def run(params: RunParams) -> bool | list[MemoryItem] | StatusResponse:
    """
    函数式调用入口。

    Args:
        params: 包含操作类型和参数的字典

    Returns:
        Union[bool, List[MemoryItem], StatusResponse]: 根据操作类型返回不同结果
    """
    return MemPalaceCore().run(params)
