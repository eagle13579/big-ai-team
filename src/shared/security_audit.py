import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

from loguru import logger


class SecurityAuditLogger:
    """
    安全审计日志记录器
    用于记录系统的安全事件，如认证、授权、敏感操作等
    """

    def __init__(self, log_file: str = "security_audit.log", max_log_size: int = 10 * 1024 * 1024, backup_count: int = 5):
        self.log_file = Path(log_file)
        # 确保日志目录存在
        self.log_file.parent.mkdir(exist_ok=True)
        
        # 配置日志记录器
        self.logger = logger.bind(logger="security_audit")
        
        # 日志文件大小限制和备份数
        self.max_log_size = max_log_size
        self.backup_count = backup_count

    def _rotate_log(self):
        """
        日志文件轮转
        """
        if self.log_file.exists() and self.log_file.stat().st_size >= self.max_log_size:
            # 备份日志文件
            for i in range(self.backup_count - 1, 0, -1):
                backup_file = self.log_file.with_suffix(f".{i}")
                if backup_file.exists():
                    backup_file.rename(self.log_file.with_suffix(f".{i+1}"))
            # 重命名当前日志文件为 .1
            self.log_file.rename(self.log_file.with_suffix(".1"))

    def log_event(self, event_type: str, user: str, action: str, resource: str, status: str, details: dict = None, ip_address: str = None, user_agent: str = None):
        """
        记录安全事件
        
        Args:
            event_type: 事件类型，如 'authentication', 'authorization', 'access', 'modification'
            user: 操作用户
            action: 操作类型
            resource: 操作的资源
            status: 操作状态，如 'success', 'failure', 'warning'
            details: 详细信息
            ip_address: 用户IP地址
            user_agent: 用户代理
        """
        # 检查是否需要轮转日志
        self._rotate_log()
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": f"{int(datetime.utcnow().timestamp() * 1000)}-{hash(f'{user}-{action}-{resource}') % 1000000}",
            "event_type": event_type,
            "user": user,
            "action": action,
            "resource": resource,
            "status": status,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {}
        }
        
        # 记录到控制台
        self.logger.info(
            f"SECURITY EVENT: {event_type} | {user} | {action} | {resource} | {status} | {ip_address or 'N/A'}",
            event=event
        )
        
        # 记录到文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def log_authentication(self, user: str, status: str, details: dict = None, ip_address: str = None, user_agent: str = None):
        """
        记录认证事件
        """
        self.log_event(
            event_type="authentication",
            user=user,
            action="login",
            resource="system",
            status=status,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_authorization(self, user: str, resource: str, action: str, status: str, details: dict = None, ip_address: str = None, user_agent: str = None):
        """
        记录授权事件
        """
        self.log_event(
            event_type="authorization",
            user=user,
            action=action,
            resource=resource,
            status=status,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_access(self, user: str, resource: str, action: str, status: str, details: dict = None, ip_address: str = None, user_agent: str = None):
        """
        记录访问事件
        """
        self.log_event(
            event_type="access",
            user=user,
            action=action,
            resource=resource,
            status=status,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_modification(self, user: str, resource: str, action: str, status: str, details: dict = None, ip_address: str = None, user_agent: str = None):
        """
        记录修改事件
        """
        self.log_event(
            event_type="modification",
            user=user,
            action=action,
            resource=resource,
            status=status,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_error(self, user: str, resource: str, action: str, error_message: str, details: dict = None, ip_address: str = None, user_agent: str = None):
        """
        记录错误事件
        """
        self.log_event(
            event_type="error",
            user=user,
            action=action,
            resource=resource,
            status="failure",
            details={"error_message": error_message, **(details or {})},
            ip_address=ip_address,
            user_agent=user_agent
        )

    def get_audit_logs(self, limit: int = 100, event_type: str = None, status: str = None, user: str = None, start_time: datetime = None, end_time: datetime = None):
        """
        获取审计日志
        
        Args:
            limit: 限制返回的日志数量
            event_type: 过滤事件类型
            status: 过滤状态
            user: 过滤用户
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            日志列表
        """
        logs = []
        try:
            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        log = json.loads(line)
                        
                        # 过滤事件类型
                        if event_type and log["event_type"] != event_type:
                            continue
                        
                        # 过滤状态
                        if status and log["status"] != status:
                            continue
                        
                        # 过滤用户
                        if user and log["user"] != user:
                            continue
                        
                        # 过滤时间范围
                        log_time = datetime.fromisoformat(log["timestamp"])
                        if start_time and log_time < start_time:
                            continue
                        if end_time and log_time > end_time:
                            continue
                        
                        logs.append(log)
        except FileNotFoundError:
            pass
        
        # 按时间倒序排列，返回最新的日志
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs[:limit]

    def get_event_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        获取事件统计信息
        
        Args:
            days: 统计天数
        
        Returns:
            统计信息
        """
        start_time = datetime.utcnow() - timedelta(days=days)
        logs = self.get_audit_logs(start_time=start_time)
        
        statistics = {
            "total_events": len(logs),
            "event_type_distribution": {},
            "status_distribution": {},
            "user_distribution": {},
            "daily_events": {}
        }
        
        for log in logs:
            # 事件类型分布
            event_type = log["event_type"]
            statistics["event_type_distribution"][event_type] = statistics["event_type_distribution"].get(event_type, 0) + 1
            
            # 状态分布
            status = log["status"]
            statistics["status_distribution"][status] = statistics["status_distribution"].get(status, 0) + 1
            
            # 用户分布
            user = log["user"]
            statistics["user_distribution"][user] = statistics["user_distribution"].get(user, 0) + 1
            
            # 每日事件数
            date = log["timestamp"].split("T")[0]
            statistics["daily_events"][date] = statistics["daily_events"].get(date, 0) + 1
        
        return statistics

    def export_logs(self, export_path: str, start_time: datetime = None, end_time: datetime = None) -> bool:
        """
        导出审计日志
        
        Args:
            export_path: 导出路径
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            导出是否成功
        """
        try:
            logs = self.get_audit_logs(start_time=start_time, end_time=end_time)
            export_file = Path(export_path)
            export_file.parent.mkdir(exist_ok=True)
            
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to export logs: {str(e)}")
            return False


# 实例化安全审计日志记录器
security_audit_logger = SecurityAuditLogger()