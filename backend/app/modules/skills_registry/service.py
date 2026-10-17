import os
import yaml
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.dao.dao import SkillDAO
from app.core.config import get_settings


class SkillsRegistry:
    def __init__(self, db: AsyncSession):
        self.dao = SkillDAO(db)
        self.settings = get_settings()

    async def register_skills(self, user_id: str, group_name: str, group_dir: str,
                              guide_id: str | None = None, description: str | None = None) -> dict:
        group_path = Path(group_dir)
        if not group_path.is_dir():
            group_path = Path(self.settings.SKILLS_STORAGE_PATH) / group_dir
        if not group_path.is_dir():
            raise ValueError(f"Skills目录不存在: {group_dir}")

        group = await self.dao.create_group(
            user_id=user_id, name=group_name, dir_path=str(group_path),
            guide_id=guide_id, description=description
        )

        registered_skills = []
        for item in sorted(group_path.iterdir()):
            if item.is_dir() and (item / "SKILL.md").exists():
                skill_meta = self._parse_skill_md(item / "SKILL.md")
                skill = await self.dao.create_skill(
                    group_id=group.id, name=skill_meta["name"], dir_path=str(item),
                    description=skill_meta.get("description"), tags=skill_meta.get("tags", [])
                )
                registered_skills.append({"id": skill.id, "name": skill.name})

        return {"group_id": group.id, "group_name": group_name, "skills": registered_skills}

    async def get_skill_groups(self, user_id: str) -> list[dict]:
        groups = await self.dao.list_groups_by_user(user_id)
        result = []
        for g in groups:
            skills = await self.dao.list_skills_by_group(g.id)
            result.append({
                "id": g.id, "name": g.name, "description": g.description,
                "guide_id": g.guide_id, "skill_count": len(skills),
                "dir_path": g.dir_path, "created_at": g.created_at
            })
        return result

    async def get_skill_group(self, group_id: str) -> dict | None:
        group = await self.dao.get_group_by_id(group_id)
        if not group:
            return None
        skills = await self.dao.list_skills_by_group(group.id)
        return {
            "id": group.id, "name": group.name, "description": group.description,
            "guide_id": group.guide_id, "skill_count": len(skills),
            "dir_path": group.dir_path, "created_at": group.created_at,
            "skills": [{"id": s.id, "name": s.name, "description": s.description, "tags": s.tags} for s in skills]
        }

    async def search_skills(self, user_id: str, keyword: str) -> list[dict]:
        groups = await self.dao.list_groups_by_user(user_id)
        results = []
        for g in groups:
            skills = await self.dao.list_skills_by_group(g.id)
            for s in skills:
                if keyword.lower() in s.name.lower() or (s.description and keyword.lower() in s.description.lower()):
                    results.append({"id": s.id, "name": s.name, "description": s.description,
                                    "tags": s.tags, "group_id": g.id, "group_name": g.name})
        return results

    async def scan_and_sync(self, user_id: str) -> dict:
        storage = Path(self.settings.SKILLS_STORAGE_PATH)
        if not storage.is_dir():
            return {"scanned": 0, "new": 0, "removed": 0}

        existing_groups = await self.dao.list_groups_by_user(user_id)
        existing_paths = {g.dir_path for g in existing_groups}

        new_count = 0
        for item in sorted(storage.iterdir()):
            if item.is_dir() and str(item) not in existing_paths:
                has_skills = any((sub / "SKILL.md").exists() for sub in item.iterdir() if sub.is_dir())
                if has_skills:
                    await self.register_skills(user_id, item.name, str(item))
                    new_count += 1

        return {"scanned": len(list(storage.iterdir())), "new": new_count}

    @staticmethod
    def _parse_skill_md(skill_md_path: Path) -> dict:
        content = skill_md_path.read_text(encoding="utf-8")
        meta = {"name": skill_md_path.parent.name, "description": "", "tags": []}
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                try:
                    fm = yaml.safe_load(content[3:end])
                    if fm:
                        meta["name"] = fm.get("name", meta["name"])
                        meta["description"] = fm.get("description", "")
                        meta["tags"] = fm.get("tags", [])
                except yaml.YAMLError:
                    pass
        return meta
