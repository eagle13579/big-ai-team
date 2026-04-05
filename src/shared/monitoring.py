import time
import psutil
import prometheus_client
from prometheus_client import Counter, Gauge, Histogram, Summary
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from ..shared.config import settings

# 初始化 Prometheus 指标
REQUEST_COUNT = Counter('ace_agent_requests_total', 'Total number of requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('ace_agent_request_duration_seconds', 'Request latency', ['method', 'endpoint'])
TASK_COUNT = Counter('ace_agent_tasks_total', 'Total number of tasks', ['status'])
TASK_DURATION = Histogram('ace_agent_task_duration_seconds', 'Task duration')
MEMORY_USAGE = Gauge('ace_agent_memory_usage_bytes', 'Memory usage')
CPU_USAGE = Gauge('ace_agent_cpu_usage_percent', 'CPU usage')
TOOL_EXECUTION_COUNT = Counter('ace_agent_tool_executions_total', 'Total number of tool executions', ['tool', 'status'])
TOOL_EXECUTION_DURATION = Histogram('ace_agent_tool_duration_seconds', 'Tool execution duration', ['tool'])

# 初始化 OpenTelemetry
def init_telemetry():
    """
    初始化 OpenTelemetry 追踪
    """
    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        # 创建 OTLP 导出器
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        
        # 创建批处理处理器
        span_processor = BatchSpanProcessor(exporter)
        
        # 设置追踪提供者
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(span_processor)
        
        # 设置全局追踪提供者
        trace.set_tracer_provider(tracer_provider)
        
        print(f"📡 OpenTelemetry 已初始化，导出到: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")

# 性能监控中间件
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
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            TOOL_EXECUTION_COUNT.labels(tool=tool_name, status=status).inc()
            TOOL_EXECUTION_DURATION.labels(tool=tool_name).observe(duration)
    return wrapper

# 启动 Prometheus 服务器
def start_prometheus_server(port=8001):
    """
    启动 Prometheus 服务器
    """
    prometheus_client.start_http_server(port)
    print(f"📊 Prometheus 监控服务器已启动，端口: {port}")

# 监控数据收集器
class MetricsCollector:
    """
    监控数据收集器
    """
    def __init__(self):
        self.start_time = time.time()
    
    def collect(self):
        """
        收集监控数据
        """
        uptime = time.time() - self.start_time
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        disk = psutil.disk_usage('/')
        
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
            }
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
        FastAPIInstrumentor.instrument_app(app)
        AioHttpClientInstrumentor().instrument()
        
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
        
        print("🔍 FastAPI 监控已集成")

    print("✅ 监控系统已初始化")
