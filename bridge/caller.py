import http.server
import importlib
import socketserver
import sys
import threading
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
# 2. 健康检查服务器
# ==========================================
class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

def start_health_check_server():
    """启动健康检查服务器"""
    port = 8001
    with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
        print(f"✅ [Bridge] 健康检查服务器启动在端口 {port}")
        httpd.serve_forever()


# ==========================================
# 3. 外部标准调用接口 (统一契约)
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
# 4. 兼容性适配器 (可选，用于兼容你之前的调用习惯)
# ==========================================
class MemPalaceCaller:
    def add_memory(self, content: str, **kwargs):
        return run_task("add", content=content, **kwargs)

    def search(self, query: str, **kwargs):
        return run_task("search", query=query, **kwargs)


# ==========================================
# 5. 主函数
# ==========================================
if __name__ == "__main__":
    # 启动健康检查服务器
    health_thread = threading.Thread(target=start_health_check_server, daemon=True)
    health_thread.start()
    
    # 保持进程运行
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n❌ [Bridge] 服务已停止")
        sys.exit(0)
