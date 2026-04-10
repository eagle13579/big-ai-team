from typing import Any

from ..core.factory import RoleFactory


class TeamMode:
    """团队协作模式"""

    def __init__(self):
        self.role_factory = RoleFactory()

    def create_team(self, project_type: str) -> dict[str, Any]:
        """创建团队"""
        roles = self._get_roles_for_project(project_type)
        team_members = []

        for role_name in roles:
            role = self.role_factory.create_role(role_name, {})
            if role:
                team_members.append(role)

        return {
            "team_id": self._generate_team_id(),
            "project_type": project_type,
            "members": team_members,
            "roles": roles,
        }

    def assign_tasks(self, team: dict[str, Any], tasks: list[dict[str, Any]]) -> dict[str, Any]:
        """分配任务"""
        assigned_tasks = []
        role_mapping = self._get_role_task_mapping()

        for task in tasks:
            task_description = task.get("description", "")
            assignee = self._determine_assignee(task_description, role_mapping, team["roles"])

            assigned_tasks.append({**task, "assignee": assignee})

        return {"team_id": team["team_id"], "assigned_tasks": assigned_tasks}

    def _get_roles_for_project(self, project_type: str) -> list[str]:
        """根据项目类型获取角色"""
        role_mapping = {
            "api_design": ["architect", "engineer", "analyst"],
            "web_development": ["engineer", "designer", "analyst"],
            "data_analysis": ["analyst", "engineer"],
            "devops": ["engineer", "manager"],
        }

        return role_mapping.get(project_type, ["engineer"])

    def _get_role_task_mapping(self) -> dict[str, list[str]]:
        """获取角色任务映射"""
        return {
            "architect": ["design", "architecture", "schema"],
            "engineer": ["code", "implement", "deploy"],
            "analyst": ["analyze", "requirement", "data"],
            "manager": ["manage", "coordinate", "plan"],
        }

    def _determine_assignee(
        self, task_description: str, role_mapping: dict[str, list[str]], available_roles: list[str]
    ) -> str:
        """确定任务负责人"""
        for role, keywords in role_mapping.items():
            if role in available_roles and any(
                keyword in task_description.lower() for keyword in keywords
            ):
                return role
        return available_roles[0] if available_roles else "engineer"

    def _generate_team_id(self) -> str:
        """生成团队ID"""
        import uuid

        return str(uuid.uuid4())

    def get_team_roles(self, team_id: str) -> list[str]:
        """获取团队角色"""
        # 实际项目中应该从数据库或缓存中获取
        return ["architect", "engineer", "analyst"]
