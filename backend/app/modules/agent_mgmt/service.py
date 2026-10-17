import json
from sqlalchemy.ext.asyncio import AsyncSession
from agno.agent import Agent

from app.core.security import encrypt_api_key, decrypt_api_key, mask_api_key
from app.shared.dao.dao import AgentDAO, SkillDAO
from app.modules.agent_mgmt.factory import AgentFactory
from app.modules.agent_mgmt.skill_loader import SkillLoaderService
from app.modules.agent_mgmt.chat_dispatch import ChatDispatchService
from app.modules.agent_mgmt.metrics import MetricsCollector
from app.modules.agent_mgmt.models import AgentCreateDTO, AgentUpdateDTO, ModelConfigDTO


class AgentManager:
    _instances: dict[str, Agent] = {}

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dao = AgentDAO(db)
        self.factory = AgentFactory(db)
        self.skill_loader = SkillLoaderService(db)
        self.chat_dispatch = ChatDispatchService()
        self.metrics = MetricsCollector(db)

    async def create_agent(self, user_id: str, dto: AgentCreateDTO) -> dict:
        if not dto.skill_group_ids:
            raise ValueError("至少需要选择一个Skills群")
        if not dto.llm_config.model_id:
            raise ValueError("必须配置模型")

        encrypted_key = ""
        if dto.llm_config.api_key:
            encrypted_key = encrypt_api_key(dto.llm_config.api_key)

        agent_record = await self.dao.create(
            user_id=user_id, name=dto.name,
            model_provider=dto.llm_config.provider,
            model_id=dto.llm_config.model_id,
            description=dto.description,
            api_key_encrypted=encrypted_key,
            base_url=dto.llm_config.base_url,
            skill_group_ids=dto.skill_group_ids,
            knowledge_enabled=dto.knowledge_config.enabled if dto.knowledge_config else False,
            config={"knowledge_table": dto.knowledge_config.table_name if dto.knowledge_config else ""},
        )

        try:
            agno_agent = await self.factory.build(
                name=dto.name, model_config=dto.llm_config,
                skill_group_ids=dto.skill_group_ids,
                knowledge_config=dto.knowledge_config,
                description=dto.description
            )
            self._instances[agent_record.id] = agno_agent
        except Exception:
            pass

        return {
            "id": agent_record.id, "name": agent_record.name,
            "model_provider": agent_record.model_provider,
            "model_id": agent_record.model_id,
            "skill_group_ids": agent_record.skill_group_ids,
            "is_active": agent_record.is_active,
        }

    async def get_agent(self, agent_id: str) -> dict | None:
        record = await self.dao.get_by_id(agent_id)
        if not record:
            return None
        key_masked = ""
        if record.api_key_encrypted:
            try:
                key_masked = mask_api_key(decrypt_api_key(record.api_key_encrypted))
            except Exception:
                key_masked = "****"
        return {
            "id": record.id, "name": record.name, "description": record.description,
            "model_provider": record.model_provider, "model_id": record.model_id,
            "api_key_masked": key_masked, "base_url": record.base_url,
            "skill_group_ids": record.skill_group_ids, "is_active": record.is_active,
            "created_at": record.created_at,
        }

    async def list_agents(self, user_id: str) -> list[dict]:
        agents = await self.dao.list_by_user(user_id)
        result = []
        for a in agents:
            key_masked = ""
            if a.api_key_encrypted:
                try:
                    key_masked = mask_api_key(decrypt_api_key(a.api_key_encrypted))
                except Exception:
                    key_masked = "****"
            result.append({
                "id": a.id, "name": a.name, "description": a.description,
                "model_provider": a.model_provider, "model_id": a.model_id,
                "api_key_masked": key_masked, "skill_group_ids": a.skill_group_ids,
                "is_active": a.is_active, "created_at": a.created_at,
            })
        return result

    async def update_agent(self, agent_id: str, dto: AgentUpdateDTO) -> dict:
        update_data = {}
        if dto.name is not None:
            update_data["name"] = dto.name
        if dto.description is not None:
            update_data["description"] = dto.description
        if dto.is_active is not None:
            update_data["is_active"] = dto.is_active
        if dto.llm_config is not None:
            update_data["model_provider"] = dto.llm_config.provider
            update_data["model_id"] = dto.llm_config.model_id
            update_data["base_url"] = dto.llm_config.base_url
            if dto.llm_config.api_key:
                update_data["api_key_encrypted"] = encrypt_api_key(dto.llm_config.api_key)
        if dto.skill_group_ids is not None:
            update_data["skill_group_ids"] = dto.skill_group_ids

        await self.dao.update(agent_id, **update_data)
        self._instances.pop(agent_id, None)
        return {"id": agent_id, "updated": True}

    async def delete_agent(self, agent_id: str) -> dict:
        await self.dao.delete(agent_id)
        self._instances.pop(agent_id, None)
        return {"id": agent_id, "deleted": True}

    async def get_or_create_instance(self, agent_id: str) -> Agent | None:
        if agent_id in self._instances:
            return self._instances[agent_id]
        record = await self.dao.get_by_id(agent_id)
        if not record or not record.is_active:
            return None
        try:
            api_key = ""
            if record.api_key_encrypted:
                api_key = decrypt_api_key(record.api_key_encrypted)
            model_config = ModelConfigDTO(
                provider=record.model_provider, model_id=record.model_id,
                api_key=api_key, base_url=record.base_url or ""
            )
            agent = await self.factory.build(
                name=record.name, model_config=model_config,
                skill_group_ids=record.skill_group_ids or [],
                description=record.description
            )
            self._instances[agent_id] = agent
            return agent
        except Exception:
            return None

    async def get_skill_groups(self, user_id: str) -> list[dict]:
        return await self.skill_loader.get_available_skill_groups(user_id)
