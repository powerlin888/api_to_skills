from pathlib import Path
from agno.skills import Skills
from agno.skills.loaders.local import LocalSkills
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.dao.dao import SkillDAO


class SkillLoaderService:
    def __init__(self, db: AsyncSession):
        self.dao = SkillDAO(db)

    async def load_skill_group(self, group_id: str) -> Skills | None:
        group = await self.dao.get_group_by_id(group_id)
        if not group:
            return None
        group_path = Path(group.dir_path)
        if not group_path.is_dir():
            return None
        try:
            return Skills(loaders=[LocalSkills(path=str(group_path))])
        except Exception:
            return None

    async def load_multiple_groups(self, group_ids: list[str]) -> Skills | None:
        loaders = []
        for gid in group_ids:
            group = await self.dao.get_group_by_id(gid)
            if not group:
                continue
            group_path = Path(group.dir_path)
            if group_path.is_dir():
                try:
                    loaders.append(LocalSkills(path=str(group_path)))
                except Exception:
                    continue
        if not loaders:
            return None
        return Skills(loaders=loaders)

    async def get_available_skill_groups(self, user_id: str) -> list[dict]:
        groups = await self.dao.list_groups_by_user(user_id)
        result = []
        for g in groups:
            skills = await self.dao.list_skills_by_group(g.id)
            result.append({
                "id": g.id, "name": g.name, "description": g.description,
                "skill_count": len(skills), "dir_path": g.dir_path
            })
        return result
