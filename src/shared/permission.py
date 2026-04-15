from typing import List, Dict, Set, Optional
from fastapi import HTTPException, status
from src.shared.auth import User


class PermissionManager:
    """
    细粒度权限管理器
    支持资源级别的权限控制
    """

    def __init__(self):
        # 定义权限矩阵
        self.permissions = {
            "admin": {
                "users": ["create", "read", "update", "delete"],
                "tasks": ["create", "read", "update", "delete", "execute"],
                "tools": ["create", "read", "update", "delete"],
                "configuration": ["read", "update"],
                "audit": ["read", "export"]
            },
            "manager": {
                "users": ["read", "update"],
                "tasks": ["create", "read", "update", "execute"],
                "tools": ["read", "update"],
                "configuration": ["read"],
                "audit": ["read"]
            },
            "user": {
                "tasks": ["create", "read", "execute"],
                "tools": ["read"]
            },
            "guest": {
                "tasks": ["read"],
                "tools": ["read"]
            }
        }

    def has_permission(self, user: User, resource: str, action: str) -> bool:
        """
        检查用户是否有指定资源的指定操作权限
        
        Args:
            user: 用户对象
            resource: 资源名称
            action: 操作名称
        
        Returns:
            是否有权限
        """
        # 获取用户角色的权限
        role_permissions = self.permissions.get(user.role, {})
        
        # 检查资源是否在权限列表中
        if resource not in role_permissions:
            return False
        
        # 检查操作是否在资源的权限列表中
        return action in role_permissions[resource]

    def get_user_permissions(self, user: User) -> Dict[str, List[str]]:
        """
        获取用户的所有权限
        
        Args:
            user: 用户对象
        
        Returns:
            用户权限字典
        """
        return self.permissions.get(user.role, {})

    def get_available_resources(self, user: User) -> List[str]:
        """
        获取用户可访问的资源列表
        
        Args:
            user: 用户对象
        
        Returns:
            资源列表
        """
        return list(self.permissions.get(user.role, {}).keys())

    def get_available_actions(self, user: User, resource: str) -> List[str]:
        """
        获取用户对指定资源的可用操作列表
        
        Args:
            user: 用户对象
            resource: 资源名称
        
        Returns:
            操作列表
        """
        role_permissions = self.permissions.get(user.role, {})
        return role_permissions.get(resource, [])

    def require_permission(self, user: User, resource: str, action: str):
        """
        检查用户权限，如果没有权限则抛出异常
        
        Args:
            user: 用户对象
            resource: 资源名称
            action: 操作名称
        
        Raises:
            HTTPException: 没有权限时抛出
        """
        if not self.has_permission(user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions for {action} on {resource}"
            )


# 实例化权限管理器
permission_manager = PermissionManager()


def require_permission(resource: str, action: str):
    """
    权限依赖装饰器
    
    Args:
        resource: 资源名称
        action: 操作名称
    
    Returns:
        依赖函数
    """
    from src.shared.auth import get_current_active_user
    
    async def permission_checker(current_user: User = await get_current_active_user()):
        permission_manager.require_permission(current_user, resource, action)
        return current_user
    
    return permission_checker
