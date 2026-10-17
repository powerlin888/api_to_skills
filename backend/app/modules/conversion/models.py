from pydantic import BaseModel
from datetime import datetime


class StageInfoDTO(BaseModel):
    stage: str
    status: str
    message: str = ""
    timestamp: datetime | None = None


class ConversionTaskDTO(BaseModel):
    id: str
    status: str
    current_stage: str | None = None
    stage_info: dict = {}
    error_message: str | None = None
    created_at: datetime


class ConversionResultDTO(BaseModel):
    task_id: str
    skill_group_id: str | None = None
    skill_count: int = 0
    skill_names: list[str] = []


class ConfirmDedupRequestDTO(BaseModel):
    action: str


class DedupInfoDTO(BaseModel):
    match_type: str = "none"
    similar_guide_name: str | None = None
    similarity: float | None = None
    existing_group_id: str | None = None
    degraded: bool = False
    degradation_reason: str | None = None


class ConversionTaskDTO(BaseModel):
    id: str
    status: str
    current_stage: str | None = None
    stage_info: dict = {}
    dedup_info: DedupInfoDTO | None = None
    error_message: str | None = None
    created_at: datetime
