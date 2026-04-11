import sys
import time
from pathlib import Path

import prometheus_client
import psutil
from prometheus_client import Counter, Gauge, Histogram, Info

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.shared.config import settings
from src.shared.logging import logger

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
    from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
except ImportError:
    logger.warning("⚠️  OpenTelemetry 依赖未安装，将禁用相关功能")

# 初始化 Prometheus 指标
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

# 初始化系统信息
SYSTEM_INFO.info(
    {
        "version": settings.CONFIG_VERSION,
        "env_mode": settings.ENV_MODE,
        "python_version": f"{sys.version}",
        "system": f"{sys.platform}",
        "platform": f"{sys.platform} {sys.version.split()[0]}",
    }
)


# 初始化 OpenTelemetry
def init_telemetry():
    """
    初始化 OpenTelemetry 追踪
    """
    if (
        settings.OTEL_EXPORTER_OTLP_ENDPOINT
        and trace
        and OTLPSpanExporter
        and TracerProvider
        and BatchSpanProcessor
    ):
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

            # 导入并初始化其他instrumentation
            try:
                from opentelemetry.instrumentation.redis import RedisInstrumentor
                RedisInstrumentor().instrument()
                logger.info("🔍 Redis 追踪已启用")
            except Exception as e:
                logger.warning(f"⚠️ Redis 追踪初始化失败: {str(e)}")

            logger.info(
                f"📡 OpenTelemetry 已初始化，导出到: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}"
            )
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
            time.time() - start_time
            # 更新内存和 CPU 使用情况
            MEMORY_USAGE.set(psutil.virtual_memory().used)
            CPU_USAGE.set(psutil.cpu_percent())
            DISK_USAGE.set(psutil.disk_usage("/").percent)

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
                # 尝试更新缓存大小
                try:
                    if hasattr(args[0], "_cache"):
                        cache_size = sum(len(str(v)) for v in args[0]._cache.values())
                        CACHE_SIZE.labels(cache_name=cache_name).set(cache_size)
                except Exception:
                    pass
                return result
            except Exception:
                CACHE_MISSES.labels(cache_name=cache_name).inc()
                raise

        return wrapper

    return decorator


# 模型调用监控装饰器
def model_monitor(model_name="default"):
    """
    模型调用监控装饰器
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                # 尝试提取token使用情况
                if isinstance(result, dict) and "usage" in result:
                    usage = result["usage"]
                    if "prompt_tokens" in usage:
                        MODEL_TOKEN_USAGE.labels(model=model_name, type="prompt").inc(usage["prompt_tokens"])
                    if "completion_tokens" in usage:
                        MODEL_TOKEN_USAGE.labels(model=model_name, type="completion").inc(usage["completion_tokens"])
                return result
            except Exception:
                status = "error"
                ERROR_COUNT.labels(error_type=f"ModelError_{model_name}").inc()
                raise
            finally:
                duration = time.time() - start_time
                MODEL_CALL_COUNT.labels(model=model_name, status=status).inc()
                MODEL_CALL_DURATION.labels(model=model_name).observe(duration)

        return wrapper

    return decorator


# 技能执行监控装饰器
def skill_monitor(skill_name="default"):
    """
    技能执行监控装饰器
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                if hasattr(result, "get") and not result.get("success", True):
                    status = "error"
                    ERROR_COUNT.labels(error_type=f"SkillError_{skill_name}").inc()
                return result
            except Exception:
                status = "error"
                ERROR_COUNT.labels(error_type=f"SkillError_{skill_name}").inc()
                raise
            finally:
                duration = time.time() - start_time
                SKILL_EXECUTION_COUNT.labels(skill=skill_name, status=status).inc()
                SKILL_EXECUTION_DURATION.labels(skill=skill_name).observe(duration)

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
        disk = psutil.disk_usage("/")
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
            "memory": {"total": memory.total, "used": memory.used, "percent": memory.percent},
            "cpu": cpu,
            "disk": {"total": disk.total, "used": disk.used, "percent": disk.percent},
            "network": {"bytes_sent": network.bytes_sent, "bytes_received": network.bytes_recv},
        }


# 健康检查
class HealthChecker:
    """
    健康检查器
    """

    def __init__(self):
        self.services = {}
        self._register_default_services()

    def _register_default_services(self):
        """
        注册默认服务健康检查
        """
        # 系统健康检查
        self.register_service("system", self._check_system_health)
        
        # 尝试注册数据库健康检查
        try:
            self.register_service("database", self._check_database_health)
        except Exception:
            pass
        
        # 尝试注册Redis健康检查
        try:
            self.register_service("redis", self._check_redis_health)
        except Exception:
            pass

    async def _check_system_health(self):
        """
        检查系统健康状态
        """
        import psutil
        
        try:
            # 检查CPU使用率
            cpu_usage = psutil.cpu_percent()
            
            # 检查内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 检查磁盘使用率
            disk = psutil.disk_usage("/")
            disk_usage = disk.percent
            
            # 检查系统负载
            load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0, 0, 0]
            
            # 确定健康状态
            status = "healthy"
            issues = []
            
            if cpu_usage > 90:
                status = "unhealthy"
                issues.append(f"CPU使用率过高: {cpu_usage}%")
            elif cpu_usage > 70:
                status = "degraded"
                issues.append(f"CPU使用率较高: {cpu_usage}%")
            
            if memory_usage > 90:
                status = "unhealthy"
                issues.append(f"内存使用率过高: {memory_usage}%")
            elif memory_usage > 70:
                status = "degraded"
                issues.append(f"内存使用率较高: {memory_usage}%")
            
            if disk_usage > 90:
                status = "unhealthy"
                issues.append(f"磁盘使用率过高: {disk_usage}%")
            elif disk_usage > 70:
                status = "degraded"
                issues.append(f"磁盘使用率较高: {disk_usage}%")
            
            return {
                "status": status,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "load_avg": load_avg,
                "issues": issues
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_database_health(self):
        """
        检查数据库健康状态
        """
        try:
            from src.persistence.database import get_db
            
            async for db in get_db():
                # 执行简单查询测试数据库连接
                await db.execute("SELECT 1")
                return {
                    "status": "healthy",
                    "connection": "ok"
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_redis_health(self):
        """
        检查Redis健康状态
        """
        try:
            from src.persistence.vector import get_redis
            
            redis = await get_redis()
            # 执行PING命令测试Redis连接
            pong = await redis.ping()
            if pong:
                # 获取Redis信息
                info = await redis.info()
                return {
                    "status": "healthy",
                    "connection": "ok",
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_rss": info.get("used_memory_rss", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                }
            else:
                return {"status": "unhealthy", "error": "Redis ping failed"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

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
                if status.get("status") == "unhealthy":
                    overall_status = "unhealthy"
                elif status.get("status") == "degraded" and overall_status != "unhealthy":
                    overall_status = "degraded"
            except Exception as e:
                health_status[service_name] = {"status": "unhealthy", "error": str(e)}
                overall_status = "unhealthy"

        return {"status": overall_status, "services": health_status}


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

            REQUEST_COUNT.labels(
                method=method, endpoint=endpoint, status=response.status_code
            ).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

            return response

        # 添加健康检查端点
        @app.get("/health")
        async def health_check():
            collector = MetricsCollector()
            metrics = collector.collect()
            
            # 使用HealthChecker进行详细健康检查
            health_checker = HealthChecker()
            health_status = await health_checker.check_health()
            
            return {
                "status": health_status["status"],
                "version": settings.CONFIG_VERSION,
                "metrics": metrics,
                "services": health_status["services"]
            }

        # 添加详细健康检查端点
        @app.get("/health/details")
        async def health_check_details():
            health_checker = HealthChecker()
            health_status = await health_checker.check_health()
            
            return health_status

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
    "model_monitor",
    "skill_monitor",
    "MetricsCollector",
    "HealthChecker",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "TASK_COUNT",
    "TASK_DURATION",
    "TASK_QUEUE_SIZE",
    "MEMORY_USAGE",
    "CPU_USAGE",
    "DISK_USAGE",
    "NETWORK_BYTES_SENT",
    "NETWORK_BYTES_RECEIVED",
    "TOOL_EXECUTION_COUNT",
    "TOOL_EXECUTION_DURATION",
    "MODEL_CALL_COUNT",
    "MODEL_CALL_DURATION",
    "MODEL_TOKEN_USAGE",
    "CACHE_HITS",
    "CACHE_MISSES",
    "CACHE_SIZE",
    "SKILL_EXECUTION_COUNT",
    "SKILL_EXECUTION_DURATION",
    "ERROR_COUNT",
    "SYSTEM_INFO",
]
