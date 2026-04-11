import importlib
import sys
from pathlib import Path
from typing import Any

# ==========================================
# 1. 路径自愈 (确保能跨目录找到 core.algorithm)
# ==========================================
# 获取 bridge 目录的父目录（即项目根目录）
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入监控模块
from bridge.monitoring import bridge_task_monitor, init_bridge_monitoring
from src.shared.logging import logger

# 初始化监控
init_bridge_monitoring()


class LoaderError(Exception):
    """自定义加载异常"""

    pass


class CoreLoader:
    """
    [顶级实践] 核心加载器
    采用单例缓存模式，确保核心引擎只被实例化一次。
    """

    _cached_core = None

    @classmethod
    def get_core(cls) -> Any:
        if cls._cached_core is None:
            try:
                # 动态加载核心模块
                # 无论当前在哪个路径启动，都能通过 sys.path 找到 core.algorithm
                module = importlib.import_module("core.algorithm")

                # 自动探测核心类 MemPalaceCore
                if hasattr(module, "MemPalaceCore"):
                    target_class = module.MemPalaceCore
                    # 默认存储路径
                    default_path = "~/.mempalace/palace"
                    cls._cached_core = target_class(palace_path=default_path)
                else:
                    # 如果类名不匹配，降级使用模块内的 run 函数
                    cls._cached_core = module

                logger.info(f"✅ [Bridge] 核心引擎加载成功 (ROOT: {PROJECT_ROOT})")
            except ImportError as e:
                raise LoaderError(
                    f"CRITICAL: 找不到核心模块 core.algorithm。请检查文件是否存在。具体错误: {e}"
                )
            except Exception as e:
                raise LoaderError(f"CRITICAL: 核心引擎初始化失败: {e}")

        return cls._cached_core


# ==========================================
# 2. 外部标准调用接口 (统一契约)
# ==========================================
@bridge_task_monitor
def run_task(action: str, **kwargs) -> Any:
    """
    [契约入口]
    示例: run_task("add", content="这是一条记忆")
    """
    try:
        core = CoreLoader.get_core()
        # 构造参数字典传递给核心层
        params = {"action": action, **kwargs}
        return core.run(params)
    except Exception as e:
        logger.error(f"❌ [Bridge] 任务执行失败: {e}")
        return None


# ==========================================
# 3. 兼容性适配器 (可选，用于兼容你之前的调用习惯)
# ==========================================
class MemPalaceCaller:
    def add_memory(self, content: str, **kwargs):
        return run_task("add", content=content, **kwargs)

    def search(self, query: str, **kwargs):
        return run_task("search", query=query, **kwargs)
