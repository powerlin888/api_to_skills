from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge import Knowledge
from agno.skills import Skills
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.knowledge.embedder.openai import OpenAIEmbedder
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_api_key, encrypt_api_key
from app.modules.agent_mgmt.skill_loader import SkillLoaderService
from app.modules.agent_mgmt.models import ModelConfigDTO, KnowledgeConfigDTO


PROVIDER_BASE_URLS = {
    "modelscope": "https://api-inference.modelscope.cn/v1/",
    "openai": "https://api.openai.com/v1/",
    "local": "http://localhost:11434/v1/",
}


class AgentFactory:
    def __init__(self, db: AsyncSession):
        self.skill_loader = SkillLoaderService(db)

    async def build(self, name: str, model_config: ModelConfigDTO,
                    skill_group_ids: list[str],
                    knowledge_config: KnowledgeConfigDTO | None = None,
                    description: str = "") -> Agent:
        if not model_config.model_id:
            raise ValueError("必须配置模型ID")
        if not model_config.api_key and model_config.provider != "local":
            raise ValueError("必须配置API Key")

        model = self._create_model(model_config)
        skills = await self._load_skills(skill_group_ids)
        knowledge = self._setup_knowledge(knowledge_config, model_config)

        agent_kwargs = {
            "name": name,
            "model": model,
            "description": description or f"编程智能体 {name}",
            "markdown": True,
        }
        if skills:
            agent_kwargs["skills"] = skills
        if knowledge:
            agent_kwargs["knowledge"] = knowledge
            agent_kwargs["search_knowledge"] = True

        return Agent(**agent_kwargs)

    def _create_model(self, config: ModelConfigDTO) -> OpenAIChat:
        base_url = config.base_url or PROVIDER_BASE_URLS.get(config.provider, "")
        api_key = config.api_key
        return OpenAIChat(
            id=config.model_id,
            api_key=api_key,
            base_url=base_url,
        )

    async def _load_skills(self, group_ids: list[str]) -> Skills | None:
        if not group_ids:
            return None
        return await self.skill_loader.load_multiple_groups(group_ids)

    def _setup_knowledge(self, config: KnowledgeConfigDTO | None,
                         model_config: ModelConfigDTO) -> Knowledge | None:
        if not config or not config.enabled:
            return None
        try:
            api_key = model_config.api_key
            return Knowledge(
                vector_db=LanceDb(
                    table_name=config.table_name,
                    search_type=SearchType.vector,
                    embedder=OpenAIEmbedder(id="text-embedding-3-small", api_key=api_key),
                ),
            )
        except Exception:
            return None
