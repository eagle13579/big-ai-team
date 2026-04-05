from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..persistence.models import SkillRegistry
from ..shared.schemas import SkillManifest


class SkillRegistryManager:
    """技能注册中心管理器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_skill(self, manifest: SkillManifest) -> SkillRegistry:
        """注册技能"""
        # 检查技能是否已存在
        existing_skill = self.db.query(SkillRegistry).filter(
            SkillRegistry.name == manifest.name
        ).first()
        
        if existing_skill:
            # 更新现有技能
            existing_skill.version = manifest.version
            existing_skill.manifest = manifest.model_dump()
            existing_skill.is_active = True
            self.db.commit()
            self.db.refresh(existing_skill)
            return existing_skill
        else:
            # 创建新技能
            new_skill = SkillRegistry(
                name=manifest.name,
                version=manifest.version,
                manifest=manifest.model_dump(),
                is_active=True
            )
            self.db.add(new_skill)
            self.db.commit()
            self.db.refresh(new_skill)
            return new_skill
    
    def get_skill(self, name: str) -> Optional[SkillRegistry]:
        """获取技能"""
        return self.db.query(SkillRegistry).filter(
            SkillRegistry.name == name,
            SkillRegistry.is_active == True
        ).first()
    
    def list_skills(self) -> list[SkillRegistry]:
        """列出所有激活的技能"""
        return self.db.query(SkillRegistry).filter(
            SkillRegistry.is_active == True
        ).all()
    
    def deactivate_skill(self, name: str) -> bool:
        """停用技能"""
        skill = self.get_skill(name)
        if skill:
            skill.is_active = False
            self.db.commit()
            return True
        return False
    
    def update_skill_manifest(self, name: str, manifest: SkillManifest) -> Optional[SkillRegistry]:
        """更新技能清单"""
        skill = self.get_skill(name)
        if skill:
            skill.manifest = manifest.model_dump()
            skill.version = manifest.version
            self.db.commit()
            self.db.refresh(skill)
        return skill
    
    def get_skill_manifest(self, name: str) -> Optional[Dict[str, Any]]:
        """获取技能清单"""
        skill = self.get_skill(name)
        return skill.manifest if skill else None
