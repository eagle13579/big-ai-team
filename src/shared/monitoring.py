import asyncio
import sys
import time
from pathlib import Path

import prometheus_client
import psutil
from prometheus_client import Counter, Gauge, Histogram, Info

# --- 路径初始化 ---
# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.shared.config import settings
from src.shared.logging import logger


# --- OpenTelemetry 模块安全导入区 ---
def safe_import(module_path, class_name):
    """
    统一的尝试导入机制，确保单个模块失败不会崩溃
    """
    try:
        # 首先尝试导入pkg_resources，这是opentelemetry-instrumentation的依赖
        import pkg_resources
    except ImportError:
        # 如果缺少pkg_resources，我们可以尝试使用importlib.metadata作为替代
        import importlib.metadata
        # 然后继续导入其他模块
    
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.warning(f"⚠️ 导入 {module_path}.{class_name} 失败: {str(e)}")
        return None

# 核心追踪组件
trace = safe_import("opentelemetry", "trace")
OTLPSpanExporter = safe_import("opentelemetry.exporter.otlp.proto.http.trace_exporter", "OTLPSpanExporter")
TracerProvider = safe_import("opentelemetry.sdk.trace", "TracerProvider")
BatchSpanProcessor = safe_import("opentelemetry.sdk.trace.export", "BatchSpanProcessor")

# 仪器化组件 (Instrumentation)
FastAPIInstrumentor = safe_import("opentelemetry.instrumentation.fastapi", "FastAPIInstrumentor")
AioHttpClientInstrumentor = safe_import("opentelemetry.instrumentation.aiohttp_client", "AioHttpClientInstrumentor")
RedisInstrumentor = safe_import("opentelemetry.instrumentation.redis", "RedisInstrumentor")
SQLAlchemyInstrumentor = safe_import("opentelemetry.instrumentation.sqlalchemy", "SQLAlchemyInstrumentor")

# --- Prometheus 指标定义 ---
# HTTP 请求指标
REQUEST_COUNT = Counter(
    "ace_agent_requests_total", "Total number of requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "ace_agent_request_duration_seconds", "Request latency", ["method", "endpoint"]
)

# 任务执行指标
TASK_COUNT = Counter("ace_agent_tasks_total", "Total number of tasks", ["status"])
TASK_DURATION = Histogram("ace_agent_task_duration_seconds", "Task duration")
TASK_QUEUE_SIZE = Gauge("ace_agent_task_queue_size", "Task queue size")

# 系统资源指标
MEMORY_USAGE = Gauge("ace_agent_memory_usage_bytes", "Memory usage")
CPU_USAGE = Gauge("ace_agent_cpu_usage_percent", "CPU usage")
DISK_USAGE = Gauge("ace_agent_disk_usage_percent", "Disk usage")
NETWORK_BYTES_SENT = Counter("ace_agent_network_bytes_sent_total", "Network bytes sent")
NETWORK_BYTES_RECEIVED = Counter("ace_agent_network_bytes_received_total", "Network bytes received")

# 工具执行指标
TOOL_EXECUTION_COUNT = Counter(
    "ace_agent_tool_executions_total", "Total number of tool executions", ["tool", "status"]
)
TOOL_EXECUTION_DURATION = Histogram(
    "ace_agent_tool_duration_seconds", "Tool execution duration", ["tool"]
)

# 模型调用指标
MODEL_CALL_COUNT = Counter(
    "ace_agent_model_calls_total", "Total number of model calls", ["model", "status"]
)
MODEL_CALL_DURATION = Histogram(
    "ace_agent_model_duration_seconds", "Model call duration", ["model"]
)
MODEL_TOKEN_USAGE = Counter(
    "ace_agent_model_tokens_total", "Total number of tokens used", ["model", "type"]
)

# 缓存指标
CACHE_HITS = Counter("ace_agent_cache_hits_total", "Total number of cache hits", ["cache_name"])
CACHE_MISSES = Counter(
    "ace_agent_cache_misses_total", "Total number of cache misses", ["cache_name"]
)
CACHE_SIZE = Gauge("ace_agent_cache_size_bytes", "Cache size", ["cache_name"])

# 技能调用指标
SKILL_EXECUTION_COUNT = Counter(
    "ace_agent_skill_executions_total", "Total number of skill executions", ["skill", "status"]
)
SKILL_EXECUTION_DURATION = Histogram(
    "ace_agent_skill_duration_seconds", "Skill execution duration", ["skill"]
)

# 错误指标
ERROR_COUNT = Counter("ace_agent_errors_total", "Total number of errors", ["error_type"])

# 系统信息
SYSTEM_INFO = Info("ace_agent_system_info", "System information")
SYSTEM_INFO.info({
    "version": settings.CONFIG_VERSION,
    "env_mode": settings.ENV_MODE,
    "python_version": f"{sys.version}",
    "system": f"{sys.platform}",
})

# --- 核心逻辑控制 ---

def init_telemetry():
    """
    初始化 OpenTelemetry 追踪逻辑
    """
    # 1. 检查核心追踪组件是否完整
    core_deps = [trace, OTLPSpanExporter, TracerProvider, BatchSpanProcessor]
    if not all(core_deps):
        missing = [name for name, val in zip(["trace", "OTLPSpanExporter", "TracerProvider", "BatchSpanProcessor"], core_deps, strict=False) if val is None]
        logger.warning(f"⚠️ OpenTelemetry 基础依赖缺失 ({', '.join(missing)})，追踪功能已禁用")
        return

    # 2. 检查配置
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
    if not endpoint:
        logger.warning("⚠️ OTEL_EXPORTER_OTLP_ENDPOINT 未配置，跳过追踪初始化")
        return

    try:
        # 配置导出器和处理器
        exporter = OTLPSpanExporter(endpoint=endpoint)
        span_processor = BatchSpanProcessor(exporter)
        
        # 配置追踪提供者
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(tracer_provider)

        # 3. 激活 Redis 追踪 (解决您的核心问题)
        if RedisInstrumentor:
            try:
                logger.info(f"🔍 RedisInstrumentor 已成功导入: {RedisInstrumentor}")
                RedisInstrumentor().instrument()
                logger.info("🔍 Redis 追踪已启用")
            except Exception as e:
                logger.warning(f"⚠️ Redis 仪器化激活失败: {str(e)}")
                import traceback
                logger.warning(f"⚠️ 详细错误信息: {traceback.format_exc()}")
        else:
            logger.warning("⚠️ Redis 追踪初始化失败: 容器内未检测到 opentelemetry-instrumentation-redis 依赖")
            # 尝试直接导入以获取更详细的错误信息
            try:
                from opentelemetry.instrumentation.redis import RedisInstrumentor as DirectRedisInstrumentor
                logger.info(f"🔍 直接导入成功: {DirectRedisInstrumentor}")
            except Exception as e:
                logger.warning(f"⚠️ 直接导入失败: {str(e)}")
                import traceback
                logger.warning(f"⚠️ 详细错误信息: {traceback.format_exc()}")

        # 4. 激活 SQLAlchemy 追踪
        if SQLAlchemyInstrumentor:
            try:
                SQLAlchemyInstrumentor().instrument()
                logger.info("🔍 SQLAlchemy 追踪已启用")
            except Exception as e:
                logger.warning(f"⚠️ SQLAlchemy 仪器化激活失败: {str(e)}")

        logger.info(f"📡 OpenTelemetry 初始化成功，上报地址: {endpoint}")

    except Exception as e:
        logger.error(f"❌ OpenTelemetry 初始化过程发生致命错误: {str(e)}")

def init_monitoring(app=None):
    """
    一键初始化监控系统 (Prometheus + OpenTelemetry)
    """
    # 1. 启动 Prometheus HTTP Server
    try:
        # 注意：如果您在 Docker 中映射了端口，请确保此处端口一致
        prometheus_client.start_http_server(8001)
        logger.info("📊 Prometheus 监控端点已启动: http://localhost:8001/metrics")
    except Exception as e:
        logger.error(f"❌ Prometheus 启动失败: {str(e)}")

    # 2. 初始化追踪
    init_telemetry()

    # 3. FastAPI 深度集成
    if app:
        if FastAPIInstrumentor:
            try:
                FastAPIInstrumentor.instrument_app(app)
                if AioHttpClientInstrumentor:
                    AioHttpClientInstrumentor().instrument()
                logger.info("🔍 OpenTelemetry 已集成至 FastAPI 生命周期")
            except Exception as e:
                logger.error(f"❌ FastAPI Instrument 集成失败: {str(e)}")

        # 添加监控中间件
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

        # 注册健康检查路由
        @app.get("/health")
        async def health_check():
            hc = HealthChecker()
            status = await hc.check_health()
            metrics = MetricsCollector().collect()
            return {"status": status["status"], "metrics": metrics, "services": status["services"]}

        # 启动后台异步采集
        asyncio.create_task(collect_metrics_loop())
        logger.info("✅ 监控系统初始化完毕")

# --- 后台数据采集器 ---

async def collect_metrics_loop():
    """后台循环更新系统资源指标"""
    collector = MetricsCollector()
    while True:
        try:
            collector.collect()
        except Exception as e:
            logger.debug(f"Metrics collection skip: {e}")
        await asyncio.sleep(5)

class MetricsCollector:
    def __init__(self):
        self.last_net = psutil.net_io_counters()
        
    def collect(self):
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()
        
        # 更新指标
        MEMORY_USAGE.set(mem.used)
        CPU_USAGE.set(cpu)
        DISK_USAGE.set(disk.percent)
        NETWORK_BYTES_SENT.inc(max(0, net.bytes_sent - self.last_net.bytes_sent))
        NETWORK_BYTES_RECEIVED.inc(max(0, net.bytes_recv - self.last_net.bytes_recv))
        self.last_net = net
        
        return {"cpu": cpu, "memory_percent": mem.percent, "disk_percent": disk.percent}

class HealthChecker:
    def __init__(self):
        self.checks = {
            "system": self._check_system,
            "redis": self._check_redis
        }

    async def _check_system(self):
        cpu = psutil.cpu_percent()
        return {"status": "healthy" if cpu < 90 else "degraded", "cpu": cpu}

    async def _check_redis(self):
        try:
            from src.persistence.vector import get_redis
            r = await get_redis()
            await r.ping()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def check_health(self):
        results = {}
        overall = "healthy"
        for name, func in self.checks.items():
            res = await func()
            results[name] = res
            if res["status"] == "unhealthy": overall = "unhealthy"
        return {"status": overall, "services": results}

# --- 装饰器工具 ---

def performance_monitor(func):
    def wrapper(*args, **kwargs):
        time.time()
        try:
            return func(*args, **kwargs)
        finally:
            # 自动更新资源快照
            MEMORY_USAGE.set(psutil.virtual_memory().used)
            CPU_USAGE.set(psutil.cpu_percent())
    return wrapper

def task_monitor(func):
    async def wrapper(*args, **kwargs):
        start = time.time()
        status = "success"
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            status = "error"
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            TASK_COUNT.labels(status=status).inc()
            TASK_DURATION.observe(time.time() - start)
    return wrapper

def tool_monitor(func):
    async def wrapper(*args, **kwargs):
        # 尝试从参数中获取工具名称
        tool_name = "unknown"
        if args:
            if isinstance(args[0], str):
                tool_name = args[0]
            elif hasattr(args[0], "__class__"):
                tool_name = args[0].__class__.__name__
        
        start = time.time()
        status = "success"
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            status = "error"
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            TOOL_EXECUTION_COUNT.labels(tool=tool_name, status=status).inc()
            TOOL_EXECUTION_DURATION.labels(tool=tool_name).observe(time.time() - start)
    return wrapper

def cache_monitor(func):
    def wrapper(*args, **kwargs):
        # 尝试从参数中获取缓存名称
        cache_name = "unknown"
        if args:
            if isinstance(args[0], str):
                cache_name = args[0]
            elif hasattr(args[0], "__class__"):
                cache_name = args[0].__class__.__name__
        
        try:
            result = func(*args, **kwargs)
            if result is not None:
                CACHE_HITS.labels(cache_name=cache_name).inc()
            else:
                CACHE_MISSES.labels(cache_name=cache_name).inc()
            return result
        except Exception as e:
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            raise
    return wrapper

def core_performance_monitor(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.time() - start
            # 记录核心性能指标
            logger.debug(f"Core function {func.__name__} took {duration:.4f} seconds")
    return wrapper

def start_prometheus_server(port=8000):
    """
    启动 Prometheus 监控服务器
    """
    try:
        prometheus_client.start_http_server(port)
        logger.info(f"📊 Prometheus 监控服务器已启动，端口：{port}")
    except Exception as e:
        logger.error(f"❌ Prometheus 监控服务器启动失败: {str(e)}")

# 导出所有功能
__all__ = [
    "init_monitoring", "start_prometheus_server", "performance_monitor", "task_monitor", 
    "tool_monitor", "cache_monitor", "core_performance_monitor",
    "REQUEST_COUNT", "ERROR_COUNT" # 以及其他定义的指标...
]