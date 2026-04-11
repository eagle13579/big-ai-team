import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.shared.logging import logger
from src.shared.monitoring import cache_monitor, performance_monitor, task_monitor


def init_core_monitoring():
    """初始化 core 服务监控"""
    try:
        # 启动 Prometheus 服务器
        from src.shared.monitoring import start_prometheus_server
        start_prometheus_server(port=8001)
        
        # 初始化 OpenTelemetry
        from src.shared.monitoring import init_telemetry
        init_telemetry()
        
        logger.info("✅ Core 监控系统已初始化")
    except Exception as e:
        logger.error(f"❌ Core 监控初始化失败: {str(e)}")


# 监控装饰器
core_performance_monitor = performance_monitor
core_task_monitor = task_monitor
core_cache_monitor = cache_monitor
