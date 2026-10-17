import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.modules.agent_mgmt.service import AgentManager
from app.modules.agent_mgmt.models import (
    AgentCreateDTO, AgentUpdateDTO, AgentInstanceDTO, ChatRequestDTO, AgentMetricsDTO
)

router = APIRouter(prefix="/api", tags=["agent"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="未认证")
    return payload["sub"]


@router.post("/agent/create")
async def create_agent(dto: AgentCreateDTO, user_id: str = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    mgr = AgentManager(db)
    try:
        return await mgr.create_agent(user_id, dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agent/{agent_id}")
async def get_agent(agent_id: str, user_id: str = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    mgr = AgentManager(db)
    result = await mgr.get_agent(agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return result


@router.put("/agent/{agent_id}")
async def update_agent(agent_id: str, dto: AgentUpdateDTO,
                       user_id: str = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    mgr = AgentManager(db)
    return await mgr.update_agent(agent_id, dto)


@router.delete("/agent/{agent_id}")
async def delete_agent(agent_id: str, user_id: str = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    mgr = AgentManager(db)
    return await mgr.delete_agent(agent_id)


@router.get("/agent/list")
async def list_agents(user_id: str = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    mgr = AgentManager(db)
    return await mgr.list_agents(user_id)


@router.get("/agent/skill-groups")
async def get_skill_groups(user_id: str = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    mgr = AgentManager(db)
    return await mgr.get_skill_groups(user_id)


@router.post("/chat/{agent_id}")
async def chat_with_agent(agent_id: str, dto: ChatRequestDTO,
                          user_id: str = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    mgr = AgentManager(db)
    agent = await mgr.get_or_create_instance(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在或未激活")

    async def event_generator():
        async for event in mgr.chat_dispatch.dispatch(agent, dto.message, dto.session_id):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@router.get("/chat/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str, session_id: str | None = None,
                            user_id: str = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    mgr = AgentManager(db)
    if session_id:
        return await mgr.metrics.get_session_metrics(agent_id, session_id)
    record = await mgr.dao.get_by_id(agent_id)
    if not record:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return {"metrics": []}
