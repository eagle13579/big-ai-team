import time
import sys
import psutil
import prometheus_client
from prometheus_client import Counter, Gauge, Histogram, Summary, Info
from ..shared.config import settings
from ..shared.logging import logger

# 尝试导入 OpenTelemetry 相关模块
trace = None
OTLPSpanExporter = None
TracerProvider = None
BatchSpanProcessor = None
FastAPIInstrumentor = None
AioHttpClientInstrumentor = None

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
except ImportError:
    logger.warning("⚠️  OpenTelemetry 依赖未安装，将禁用相关功能")

# 初始化 Prometheus 指标
REQUEST_COUNT = Counter('ace_agent_requests_total', 'Total number of requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('ace_agent_request_duration_seconds', 'Request latency', ['method', 'endpoint'])
TASK_COUNT = Counter('ace_agent_tasks_total', 'Total number of tasks', ['status'])
TASK_DURATION = Histogram('ace_agent_task_duration_seconds', 'Task duration')
MEMORY_USAGE = Gauge('ace_agent_memory_usage_bytes', 'Memory usage')
CPU_USAGE = Gauge('ace_agent_cpu_usage_percent', 'CPU usage')
DISK_USAGE = Gauge('ace_agent_disk_usage_percent', 'Disk usage')
NETWORK_BYTES_SENT = Counter('ace_agent_network_bytes_sent_total', 'Network bytes sent')
NETWORK_BYTES_RECEIVED = Counter('ace_agent_network_bytes_received_total', 'Network bytes received')
TOOL_EXECUTION_COUNT = Counter('ace_agent_tool_executions_total', 'Total number of tool executions', ['tool', 'status'])
TOOL_EXECUTION_DURATION = Histogram('ace_agent_tool_duration_seconds', 'Tool execution duration', ['tool'])
ERROR_COUNT = Counter('ace_agent_errors_total', 'Total number of errors', ['error_type'])
CACHE_HITS = Counter('ace_agent_cache_hits_total', 'Total number of cache hits', ['cache_name'])
CACHE_MISSES = Counter('ace_agent_cache_misses_total', 'Total number of cache misses', ['cache_name'])
SYSTEM_INFO = Info('ace_agent_system_info', 'System information')

# 初始化系统信息
SYSTEM_INFO.info({
    'version': settings.CONFIG_VERSION,
    'env_mode': settings.ENV_MODE,
    'python_version': f"{sys.version}",
    'system': f"{sys.platform}",
    'platform': f"{sys.platform} {sys.version.split()[0]}"
})

# 初始化 OpenTelemetry
def init_telemetry():
    """
    初始化 OpenTelemetry 追踪
    """
    if settings.OTEL_EXPORTER_OTLP_ENDPOINT and trace and OTLPSpanExporter and TracerProvider and BatchSpanProcessor:
        try:
            # 创建 OTLP 导出器
            exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
            
            # 创建批处理处理器
            span_processor = BatchSpanProcessor(exporter)
            
            # 设置追踪提供者
            tracer_provider = TracerProvider()
            tracer_provider.add_span_processor(span_processor)
            
            # 设置全局追踪提供者
            trace.set_tracer_provider(tracer_provider)
            
            logger.info(f"📡 OpenTelemetry 已初始化，导出到: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")
        except Exception as e:
            logger.error(f"❌ OpenTelemetry 初始化失败: {str(e)}")
    else:
        logger.warning("⚠️  OpenTelemetry 未初始化，相关功能已禁用")

# 性能监控装饰器
def performance_monitor(func):
    """
    性能监控装饰器
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            # 更新内存和 CPU 使用情况
            MEMORY_USAGE.set(psutil.virtual_memory().used)
            CPU_USAGE.set(psutil.cpu_percent())
            DISK_USAGE.set(psutil.disk_usage('/').percent)
    return wrapper

# 任务监控装饰器
def task_monitor(func):
    """
    任务监控装饰器
    """
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        status = "success"
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status = "error"
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.time() - start_time
            TASK_COUNT.labels(status=status).inc()
            TASK_DURATION.observe(duration)
    return wrapper

# 工具执行监控装饰器
def tool_monitor(func):
    """
    工具执行监控装饰器
    """
    async def wrapper(*args, **kwargs):
        tool_name = args[1] if len(args) > 1 else "unknown"
        start_time = time.time()
        status = "success"
        try:
            result = await func(*args, **kwargs)
            if not result.get("success", True):
                status = "error"
                ERROR_COUNT.labels(error_type="ToolError").inc()
            return result
        except Exception as e:
            status = "error"
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.time() - start_time
            TOOL_EXECUTION_COUNT.labels(tool=tool_name, status=status).inc()
            TOOL_EXECUTION_DURATION.labels(tool=tool_name).observe(duration)
    return wrapper

# 缓存监控装饰器
def cache_monitor(cache_name="default"):
    """
    缓存监控装饰器
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    CACHE_HITS.labels(cache_name=cache_name).inc()
                else:
                    CACHE_MISSES.labels(cache_name=cache_name).inc()
                return result
            except Exception as e:
                CACHE_MISSES.labels(cache_name=cache_name).inc()
                raise
        return wrapper
    return decorator

# 启动 Prometheus 服务器
def start_prometheus_server(port=8001):
    """
    启动 Prometheus 服务器
    """
    try:
        prometheus_client.start_http_server(port)
        logger.info(f"📊 Prometheus 监控服务器已启动，端口: {port}")
    except Exception as e:
        logger.error(f"❌ Prometheus 服务器启动失败: {str(e)}")

# 监控数据收集器
class MetricsCollector:
    """
    监控数据收集器
    """
    def __init__(self):
        self.start_time = time.time()
        self.last_network_stats = psutil.net_io_counters()
    
    def collect(self):
        """
        收集监控数据
        """
        uptime = time.time() - self.start_time
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # 计算网络流量
        bytes_sent = network.bytes_sent - self.last_network_stats.bytes_sent
        bytes_received = network.bytes_recv - self.last_network_stats.bytes_recv
        
        # 更新网络流量计数器
        if bytes_sent > 0:
            NETWORK_BYTES_SENT.inc(bytes_sent)
        if bytes_received > 0:
            NETWORK_BYTES_RECEIVED.inc(bytes_received)
        
        # 更新网络统计
        self.last_network_stats = network
        
        return {
            "uptime": uptime,
            "memory": {
                "total": memory.total,
                "used": memory.used,
                "percent": memory.percent
            },
            "cpu": cpu,
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_received": network.bytes_recv
            }
        }

# 健康检查
class HealthChecker:
    """
    健康检查器
    """
    def __init__(self):
        self.services = {}
    
    def register_service(self, name, check_func):
        """
        注册服务健康检查
        """
        self.services[name] = check_func
    
    async def check_health(self):
        """
        检查所有服务健康状态
        """
        import asyncio
        health_status = {}
        overall_status = "healthy"
        
        for service_name, check_func in self.services.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    status = await check_func()
                else:
                    status = check_func()
                health_status[service_name] = status
                if status.get("status") != "healthy":
                    overall_status = "unhealthy"
            except Exception as e:
                health_status[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "services": health_status
        }

# 初始化监控
def init_monitoring(app=None):
    """
    初始化监控
    """
    # 启动 Prometheus 服务器
    start_prometheus_server()
    
    # 初始化 OpenTelemetry
    init_telemetry()
    
    # 为 FastAPI 应用添加监控
    if app:
        # 集成 OpenTelemetry
        if FastAPIInstrumentor and AioHttpClientInstrumentor:
            try:
                FastAPIInstrumentor.instrument_app(app)
                AioHttpClientInstrumentor().instrument()
                logger.info("🔍 OpenTelemetry 已集成到 FastAPI")
            except Exception as e:
                logger.error(f"❌ OpenTelemetry 集成失败: {str(e)}")
        else:
            logger.warning("⚠️  OpenTelemetry 集成已跳过，相关模块未安装")
        
        # 添加 Prometheus 中间件
        @app.middleware("http")
        async def prometheus_middleware(request, call_next):
            method = request.method
            endpoint = request.url.path
            
            start_time = time.time()
            response = await call_next(request)
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=response.status_code).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            
            return response
        
        # 添加健康检查端点
        @app.get("/health")
        async def health_check():
            collector = MetricsCollector()
            metrics = collector.collect()
            return {
                "status": "healthy",
                "version": settings.CONFIG_VERSION,
                "metrics": metrics
            }
        
        logger.info("🔍 FastAPI 监控已集成")

    # 启动定期监控数据收集
    import asyncio
    async def collect_metrics():        
        collector = MetricsCollector()
        while True:
            try:
                collector.collect()
            except Exception as e:
                logger.error(f"❌ 监控数据收集失败: {str(e)}")
            await asyncio.sleep(5)  # 每 5 秒收集一次
    
    if app:
        import asyncio
        asyncio.create_task(collect_metrics())
        logger.info("🔍 定期监控数据收集已启动")

    logger.info("✅ 监控系统已初始化")

# 导出
__all__ = [
    "init_monitoring",
    "performance_monitor",
    "task_monitor",
    "tool_monitor",
    "cache_monitor",
    "MetricsCollector",
    "HealthChecker"
]