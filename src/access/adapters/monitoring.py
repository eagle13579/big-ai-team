from typing import Dict, Any, Optional
from abc import abstractmethod
from .base import BaseAdapter, AdapterContext
from .registry import adapter_registry
import logging

# 配置日志
logger = logging.getLogger("AceAgent.Adapters")


class MonitoringAdapter(BaseAdapter[Dict[str, Any]]):
    """监控适配器基类"""
    
    async def execute(self, operation: str, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """执行监控操作"""
        if operation == "trace":
            return await self.trace(params, context)
        elif operation == "metrics":
            return await self.metrics(params, context)
        elif operation == "log":
            return await self.log(params, context)
        elif operation == "health_check":
            return await self._health_check(context)
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    @abstractmethod
    async def trace(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """追踪操作"""
        pass
    
    @abstractmethod
    async def metrics(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """指标操作"""
        pass
    
    @abstractmethod
    async def log(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """日志操作"""
        pass
    
    async def _health_check(self, context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 尝试记录一个简单的日志
            await self.log({"level": "info", "message": "health check"}, context)
            return {
                "status": "healthy",
                "platform": self.platform,
                "timestamp": context.timestamp.isoformat() if context else None
            }
        except Exception as e:
            logger.error(f"Health check failed for {self.platform}: {str(e)}")
            return {
                "status": "unhealthy",
                "platform": self.platform,
                "error": str(e),
                "timestamp": context.timestamp.isoformat() if context else None
            }


class LangSmithAdapter(MonitoringAdapter):
    """LangSmith 监控适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = self.config.config.get("api_key")
        self.project_name = self.config.config.get("project_name", "default")
        self.client = None
    
    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        if not self.api_key:
            raise ValueError("LangSmith API key is required")
        
        try:
            # 导入 LangSmith 客户端
            import langsmith
            from langsmith import Client
            self.client = Client(api_key=self.api_key, project_name=self.project_name)
            self._set_initialized(True)
            logger.info(f"LangSmith adapter initialized successfully for project: {self.project_name}")
            return True
        except ImportError:
            logger.error("LangSmith SDK is not installed. Please run: pip install langsmith")
            raise Exception("LangSmith SDK is not installed. Please run: pip install langsmith")
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith adapter: {str(e)}")
            raise Exception(f"Failed to initialize LangSmith adapter: {str(e)}")
    
    async def trace(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """追踪操作"""
        if not self.client:
            await self.initialize(context)
        
        try:
            # 创建追踪
            trace_id = self.client.create_trace(
                name=params.get("name", "unnamed"),
                inputs=params.get("inputs", {}),
                metadata=params.get("metadata", {})
            )
            logger.debug(f"Created LangSmith trace with ID: {trace_id}")
            return {
                "trace_id": trace_id
            }
        except Exception as e:
            logger.error(f"Trace operation failed: {str(e)}")
            raise Exception(f"Trace operation failed: {str(e)}")
    
    async def metrics(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """指标操作"""
        if not self.client:
            await self.initialize(context)
        
        try:
            # 记录指标
            # LangSmith 主要用于追踪，指标功能有限
            logger.debug("Metrics operation executed")
            return {
                "success": True
            }
        except Exception as e:
            logger.error(f"Metrics operation failed: {str(e)}")
            raise Exception(f"Metrics operation failed: {str(e)}")
    
    async def log(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """日志操作"""
        if not self.client:
            await self.initialize(context)
        
        try:
            # 记录日志
            # LangSmith 主要用于追踪，日志功能有限
            logger.debug(f"Log operation executed: {params.get('message')}")
            return {
                "success": True
            }
        except Exception as e:
            logger.error(f"Log operation failed: {str(e)}")
            raise Exception(f"Log operation failed: {str(e)}")
    
    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        try:
            self.client = None
            self._set_initialized(False)
            logger.info("LangSmith adapter closed successfully")
            return True
        except Exception as e:
            logger.error(f"Error closing LangSmith adapter: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "project_name": self.project_name
        }


class OpenTelemetryAdapter(MonitoringAdapter):
    """OpenTelemetry 监控适配器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.service_name = self.config.config.get("service_name", "big-ai-team")
        self.exporter = self.config.config.get("exporter", "console")
        self.tracer = None
        self.meter = None
    
    async def initialize(self, context: Optional[AdapterContext] = None) -> bool:
        """初始化适配器"""
        try:
            # 导入 OpenTelemetry 相关模块
            from opentelemetry import trace
            from opentelemetry import metrics
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            
            # 配置追踪
            tracer_provider = TracerProvider()
            if self.exporter == "console":
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter
                span_processor = BatchSpanProcessor(ConsoleSpanExporter())
            elif self.exporter == "jaeger":
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter
                span_processor = BatchSpanProcessor(JaegerExporter())
            else:
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter
                span_processor = BatchSpanProcessor(ConsoleSpanExporter())
            
            tracer_provider.add_span_processor(span_processor)
            trace.set_tracer_provider(tracer_provider)
            
            # 配置指标
            meter_provider = MeterProvider()
            if self.exporter == "console":
                from opentelemetry.sdk.metrics.export import ConsoleMetricExporter
                metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
            else:
                from opentelemetry.sdk.metrics.export import ConsoleMetricExporter
                metric_reader = PeriodicExportingMetricReader(ConsoleMetricExporter())
            
            meter_provider.add_metric_reader(metric_reader)
            metrics.set_meter_provider(meter_provider)
            
            # 获取 tracer 和 meter
            self.tracer = trace.get_tracer(self.service_name)
            self.meter = metrics.get_meter(self.service_name)
            
            self._set_initialized(True)
            logger.info(f"OpenTelemetry adapter initialized successfully with {self.exporter} exporter")
            return True
        except ImportError:
            logger.error("OpenTelemetry SDK is not installed. Please run: pip install opentelemetry-sdk opentelemetry-exporter-console")
            raise Exception("OpenTelemetry SDK is not installed. Please run: pip install opentelemetry-sdk opentelemetry-exporter-console")
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry adapter: {str(e)}")
            raise Exception(f"Failed to initialize OpenTelemetry adapter: {str(e)}")
    
    async def trace(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """追踪操作"""
        if not self.tracer:
            await self.initialize(context)
        
        try:
            # 创建 span
            with self.tracer.start_as_current_span(params.get("name", "unnamed")) as span:
                # 设置属性
                for key, value in params.get("attributes", {}).items():
                    span.set_attribute(key, value)
                # 记录事件
                for event in params.get("events", []):
                    span.add_event(event.get("name"), event.get("attributes", {}))
            
            logger.debug(f"Trace operation executed: {params.get('name')}")
            return {
                "success": True
            }
        except Exception as e:
            logger.error(f"Trace operation failed: {str(e)}")
            raise Exception(f"Trace operation failed: {str(e)}")
    
    async def metrics(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """指标操作"""
        if not self.meter:
            await self.initialize(context)
        
        try:
            # 记录指标
            metric_name = params.get("name")
            value = params.get("value")
            if metric_name and value is not None:
                # 创建计数器
                counter = self.meter.create_counter(
                    metric_name,
                    description=params.get("description", ""),
                    unit=params.get("unit", "1")
                )
                counter.add(value, params.get("attributes", {}))
                logger.debug(f"Metrics operation executed: {metric_name} = {value}")
            
            return {
                "success": True
            }
        except Exception as e:
            logger.error(f"Metrics operation failed: {str(e)}")
            raise Exception(f"Metrics operation failed: {str(e)}")
    
    async def log(self, params: Dict[str, Any], context: Optional[AdapterContext] = None) -> Dict[str, Any]:
        """日志操作"""
        if not self.tracer:
            await self.initialize(context)
        
        try:
            # 记录日志
            with self.tracer.start_as_current_span("log") as span:
                span.add_event(
                    params.get("message", ""),
                    {
                        "level": params.get("level", "info"),
                        "timestamp": params.get("timestamp")
                    }
                )
            
            logger.debug(f"Log operation executed: {params.get('message')}")
            return {
                "success": True
            }
        except Exception as e:
            logger.error(f"Log operation failed: {str(e)}")
            raise Exception(f"Log operation failed: {str(e)}")
    
    async def close(self, context: Optional[AdapterContext] = None) -> bool:
        """关闭适配器"""
        try:
            self.tracer = None
            self.meter = None
            self._set_initialized(False)
            logger.info("OpenTelemetry adapter closed successfully")
            return True
        except Exception as e:
            logger.error(f"Error closing OpenTelemetry adapter: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "platform": self.platform,
            "initialized": self.is_initialized(),
            "service_name": self.service_name,
            "exporter": self.exporter
        }


# 注册监控适配器
adapter_registry.register("langsmith", LangSmithAdapter)
adapter_registry.register("opentelemetry", OpenTelemetryAdapter)
