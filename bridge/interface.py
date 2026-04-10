import logging
from typing import Any, Protocol, Union, runtime_checkable

# 获取当前模块的 Logger，用于接口契约校验失败时的追踪
logger = logging.getLogger("Bridge.Interface")


@runtime_checkable
class CoreInterface(Protocol):
    """
    [顶级契约] 核心业务接口协议 (Structural Subtyping)。

    设计优势：
    1. 兼容性：即便 core.algorithm 是由 Cython、PyArmor 编译的二进制文件，
       只要其内部导出了 run 方法，runtime_checkable 就能通过 isinstance 验证。
    2. 静态分析：MyPy 等类型检查工具可以跨模块验证调用合法性。
    """

    def run(self, params: dict[str, Any]) -> Any:
        """
        核心逻辑入口。

        Args:
            params: 业务参数字典。建议包含 'action' 和 'payload' 等核心键值。

        Returns:
            执行结果。通常为字典或特定的业务对象。

        Raises:
            BridgeError: 当核心执行过程中发生逻辑错误时抛出。
        """
        ...


# --- 异常体系定义 (Exception Hierarchy) ---
# 遵循世界顶尖实践：分层捕获，不直接使用基类 Exception


class BridgeError(Exception):
    """Bridge 层的基类异常。所有 Bridge 相关错误应继承此类。"""

    def __init__(self, message: str, context: dict[str, Any] = None):
        super().__init__(message)
        self.context = context or {}
        # 自动记录异常发生时的上下文，方便 GitHub Actions 日志排查
        logger.error(f"契约执行异常: {message} | 上下文: {self.context}")


class LoaderError(BridgeError):
    """加载核心模块失败异常。通常发生在二进制缺失、版本不匹配或脱敏损坏时。"""

    pass


class ValidationError(BridgeError):
    """参数校验异常。当输入参数不符合核心算法要求时抛出。"""

    pass


class ExecutionError(BridgeError):
    """核心算法内部执行异常。"""

    pass


# 定义类型别名，方便外部调用者引用
CoreResult = Union[dict[str, Any], Any]
