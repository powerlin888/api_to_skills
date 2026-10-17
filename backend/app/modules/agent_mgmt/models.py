from pydantic import BaseModel
from datetime import datetime


class ModelConfigDTO(BaseModel):
    provider: str = "modelscope"
    model_id: str = ""
    api_key: str = ""
    base_url: str = ""


class KnowledgeConfigDTO(BaseModel):
    enabled: bool = False
    table_name: str = "agent_knowledge"


class AgentCreateDTO(BaseModel):
    name: str
    description: str = ""
    llm_config: ModelConfigDTO
    skill_group_ids: list[str] = []
    knowledge_config: KnowledgeConfigDTO | None = None


class AgentUpdateDTO(BaseModel):
    name: str | None = None
    description: str | None = None
    llm_config: ModelConfigDTO | None = None
    skill_group_ids: list[str] | None = None
    is_active: bool | None = None


class AgentInstanceDTO(BaseModel):
    id: str
    name: str
    description: str
    model_provider: str
    model_id: str
    api_key_masked: str = ""
    skill_group_ids: list[str] = []
    is_active: bool = True
    created_at: datetime


class ChatRequestDTO(BaseModel):
    message: str
    session_id: str | None = None


class ChatMessageDTO(BaseModel):
    role: str
    content: str
    timestamp: datetime | None = None


class AgentMetricsDTO(BaseModel):
    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    latency_ms: int = 0
    cost: float = 0.0
