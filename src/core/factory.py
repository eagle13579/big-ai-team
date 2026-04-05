from typing import Dict, Any, Optional
from ..shared.utils import generate_uuid


class RoleFactory:
    """角色工厂"""
    
    def __init__(self):
        self.roles = {
            "architect": self._create_architect,
            "engineer": self._create_engineer,
            "analyst": self._create_analyst,
            "manager": self._create_manager
        }
    
    def create_role(self, role_name: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建角色"""
        if role_name in self.roles:
            return self.roles[role_name](context)
        return None
    
    def _create_architect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """创建架构师角色"""
        return {
            "role_id": generate_uuid(),
            "name": "architect",
            "description": "负责系统架构设计和技术选型",
            "capabilities": ["system_design", "technical_architecture", "solution_architecture"],
            "context": context
        }
    
    def _create_engineer(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """创建工程师角色"""
        return {
            "role_id": generate_uuid(),
            "name": "engineer",
            "description": "负责代码实现和技术问题解决",
            "capabilities": ["coding", "debugging", "performance_optimization"],
            "context": context
        }
    
    def _create_analyst(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """创建分析师角色"""
        return {
            "role_id": generate_uuid(),
            "name": "analyst",
            "description": "负责需求分析和数据处理",
            "capabilities": ["requirement_analysis", "data_analysis", "business_intelligence"],
            "context": context
        }
    
    def _create_manager(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """创建项目经理角色"""
        return {
            "role_id": generate_uuid(),
            "name": "manager",
            "description": "负责项目管理和协调",
            "capabilities": ["project_management", "resource_allocation", "risk_management"],
            "context": context
        }
    
    def list_roles(self) -> Dict[str, str]:
        """列出所有可用角色"""
        return {
            "architect": "系统架构设计",
            "engineer": "代码实现",
            "analyst": "需求分析",
            "manager": "项目管理"
        }
