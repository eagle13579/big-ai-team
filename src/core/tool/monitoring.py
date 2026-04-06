from typing import Dict, Any, Optional, List
import logging
import time
import datetime
from pydantic import BaseModel, Field
import threading

logger = logging.getLogger(__name__)


class ToolMetrics(BaseModel):
    """
    工具执行指标模型
    """
    tool_name: str
    execution_time: float  # 执行时间（秒）
    success: bool
    error: Optional[str] = None
    timestamp: datetime.datetime
    args: Dict[str, Any] = Field(default_factory=dict)


class ToolAuditLog(BaseModel):
    """
    工具审计日志模型
    """
    tool_name: str
    action: str  # 执行、注册、权限检查等
    user: Optional[str] = None
    timestamp: datetime.datetime
    details: Dict[str, Any] = Field(default_factory=dict)


class MonitoringManager:
    """
    监控管理器，负责收集工具执行指标和审计日志
    """
    def __init__(self):
        self.metrics: List[ToolMetrics] = []
        self.audit_logs: List[ToolAuditLog] = []
        self.lock = threading.Lock()
        self.metrics_buffer_size = 1000
        self.logs_buffer_size = 1000

    def record_metrics(self, tool_name: str, execution_time: float, success: bool, error: Optional[str] = None, args: Dict[str, Any] = None):
        """
        记录工具执行指标
        
        Args:
            tool_name: 工具名称
            execution_time: 执行时间（秒）
            success: 是否成功
            error: 错误信息
            args: 工具参数
        """
        with self.lock:
            metric = ToolMetrics(
                tool_name=tool_name,
                execution_time=execution_time,
                success=success,
                error=error,
                timestamp=datetime.datetime.now(),
                args=args or {}
            )
            self.metrics.append(metric)
            
            # 限制缓冲区大小
            if len(self.metrics) > self.metrics_buffer_size:
                self.metrics = self.metrics[-self.metrics_buffer_size:]
            
            # 记录日志
            logger.info(f"Tool {tool_name} executed in {execution_time:.3f}s, success: {success}")

    def record_audit_log(self, tool_name: str, action: str, user: Optional[str] = None, details: Dict[str, Any] = None):
        """
        记录审计日志
        
        Args:
            tool_name: 工具名称
            action: 操作类型
            user: 用户
            details: 详细信息
        """
        with self.lock:
            log = ToolAuditLog(
                tool_name=tool_name,
                action=action,
                user=user,
                timestamp=datetime.datetime.now(),
                details=details or {}
            )
            self.audit_logs.append(log)
            
            # 限制缓冲区大小
            if len(self.audit_logs) > self.logs_buffer_size:
                self.audit_logs = self.audit_logs[-self.logs_buffer_size:]
            
            # 记录日志
            logger.info(f"Audit: {action} for tool {tool_name} by {user or 'system'}")

    def get_metrics(self, tool_name: Optional[str] = None, limit: int = 100) -> List[ToolMetrics]:
        """
        获取工具执行指标
        
        Args:
            tool_name: 工具名称，None 表示所有工具
            limit: 限制数量
            
        Returns:
            List[ToolMetrics]: 指标列表
        """
        with self.lock:
            metrics = self.metrics
            if tool_name:
                metrics = [m for m in metrics if m.tool_name == tool_name]
            return metrics[-limit:]

    def get_audit_logs(self, tool_name: Optional[str] = None, limit: int = 100) -> List[ToolAuditLog]:
        """
        获取审计日志
        
        Args:
            tool_name: 工具名称，None 表示所有工具
            limit: 限制数量
            
        Returns:
            List[ToolAuditLog]: 日志列表
        """
        with self.lock:
            logs = self.audit_logs
            if tool_name:
                logs = [l for l in logs if l.tool_name == tool_name]
            return logs[-limit:]

    def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """
        获取工具统计信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self.lock:
            tool_metrics = [m for m in self.metrics if m.tool_name == tool_name]
            if not tool_metrics:
                return {
                    "tool_name": tool_name,
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "average_execution_time": 0,
                    "error_rate": 0
                }
            
            total = len(tool_metrics)
            successful = sum(1 for m in tool_metrics if m.success)
            failed = total - successful
            avg_time = sum(m.execution_time for m in tool_metrics) / total
            error_rate = failed / total if total > 0 else 0
            
            return {
                "tool_name": tool_name,
                "total_executions": total,
                "successful_executions": successful,
                "failed_executions": failed,
                "average_execution_time": avg_time,
                "error_rate": error_rate
            }


# 创建全局监控管理器实例
monitoring_manager = MonitoringManager()


class MetricsDecorator:
    """
    指标收集装饰器
    """
    @staticmethod
    def track_execution(func):
        """
        跟踪函数执行
        """
        async def wrapper(self, *args, **kwargs):
            start_time = time.time()
            try:
                result = await func(self, *args, **kwargs)
                execution_time = time.time() - start_time
                monitoring_manager.record_metrics(
                    tool_name=self.name,
                    execution_time=execution_time,
                    success=result.success,
                    error=result.error,
                    args=kwargs
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                monitoring_manager.record_metrics(
                    tool_name=self.name,
                    execution_time=execution_time,
                    success=False,
                    error=str(e),
                    args=kwargs
                )
                raise
        return wrapper