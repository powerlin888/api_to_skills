from pydantic import BaseModel
from datetime import datetime


class SkillMetaDTO(BaseModel):
    id: str
    name: str
    description: str | None = None
    tags: list[str] = []
    group_id: str
    group_name: str


class SkillGroupDTO(BaseModel):
    id: str
    name: str
    description: str | None = None
    guide_id: str | None = None
    skill_count: int = 0
    dir_path: str
    created_at: datetime
