import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.shared.monitoring import init_monitoring, performance_monitor, task_monitor
from src.shared.logging import logger


def init_bridge_monitoring():
    """初始化 bridge 服务监控"""
    try:
        # 启动 Prometheus 服务器
        from src.shared.monitoring import start_prometheus_server
        start_prometheus_server(port=8000)
        
        # 初始化 OpenTelemetry
        from src.shared.monitoring import init_telemetry
        init_telemetry()
        
        logger.info("✅ Bridge 监控系统已初始化")
    except Exception as e:
        logger.error(f"❌ Bridge 监控初始化失败: {str(e)}")


# 监控装饰器
bridge_performance_monitor = performance_monitor
bridge_task_monitor = task_monitor
