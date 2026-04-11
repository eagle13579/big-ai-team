import json
from datetime import datetime
from pathlib import Path

from loguru import logger


class SecurityAuditLogger:
    """
    安全审计日志记录器
    用于记录系统的安全事件，如认证、授权、敏感操作等
    """

    def __init__(self, log_file: str = "security_audit.log"):
        self.log_file = Path(log_file)
        # 确保日志目录存在
        self.log_file.parent.mkdir(exist_ok=True)
        
        # 配置日志记录器
        self.logger = logger.bind(logger="security_audit")

    def log_event(self, event_type: str, user: str, action: str, resource: str, status: str, details: dict = None):
        """
        记录安全事件
        
        Args:
            event_type: 事件类型，如 'authentication', 'authorization', 'access', 'modification'
            user: 操作用户
            action: 操作类型
            resource: 操作的资源
            status: 操作状态，如 'success', 'failure', 'warning'
            details: 详细信息
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user": user,
            "action": action,
            "resource": resource,
            "status": status,
            "details": details or {}
        }
        
        # 记录到控制台
        self.logger.info(
            f"SECURITY EVENT: {event_type} | {user} | {action} | {resource} | {status}",
            event=event
        )
        
        # 记录到文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def log_authentication(self, user: str, status: str, details: dict = None):
        """
        记录认证事件
        """
        self.log_event(
            event_type="authentication",
            user=user,
            action="login",
            resource="system",
            status=status,
            details=details
        )

    def log_authorization(self, user: str, resource: str, action: str, status: str, details: dict = None):
        """
        记录授权事件
        """
        self.log_event(
            event_type="authorization",
            user=user,
            action=action,
            resource=resource,
            status=status,
            details=details
        )

    def log_access(self, user: str, resource: str, action: str, status: str, details: dict = None):
        """
        记录访问事件
        """
        self.log_event(
            event_type="access",
            user=user,
            action=action,
            resource=resource,
            status=status,
            details=details
        )

    def log_modification(self, user: str, resource: str, action: str, status: str, details: dict = None):
        """
        记录修改事件
        """
        self.log_event(
            event_type="modification",
            user=user,
            action=action,
            resource=resource,
            status=status,
            details=details
        )

    def get_audit_logs(self, limit: int = 100, event_type: str = None, status: str = None):
        """
        获取审计日志
        
        Args:
            limit: 限制返回的日志数量
            event_type: 过滤事件类型
            status: 过滤状态
        
        Returns:
            日志列表
        """
        logs = []
        try:
            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        log = json.loads(line)
                        if event_type and log["event_type"] != event_type:
                            continue
                        if status and log["status"] != status:
                            continue
                        logs.append(log)
        except FileNotFoundError:
            pass
        
        # 按时间倒序排列，返回最新的日志
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs[:limit]


# 实例化安全审计日志记录器
security_audit_logger = SecurityAuditLogger()