from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.modules.skills_registry.service import SkillsRegistry
from app.modules.skills_registry.models import SkillGroupDTO, SkillMetaDTO

router = APIRouter(prefix="/api/skills", tags=["skills"])
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="未认证")
    return payload["sub"]


async def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(optional_security)) -> str | None:
    if not credentials:
        return None
    payload = verify_token(credentials.credentials)
    return payload["sub"] if payload else None


@router.get("/groups")
async def list_skill_groups(user_id: str | None = Depends(get_optional_user),
                            db: AsyncSession = Depends(get_db)):
    svc = SkillsRegistry(db)
    return await svc.get_skill_groups(user_id or "")


@router.get("/groups/{group_id}")
async def get_skill_group(group_id: str, user_id: str | None = Depends(get_optional_user),
                          db: AsyncSession = Depends(get_db)):
    svc = SkillsRegistry(db)
    result = await svc.get_skill_group(group_id)
    if not result:
        raise HTTPException(status_code=404, detail="Skills群不存在")
    return result


@router.get("/search")
async def search_skills(keyword: str, user_id: str | None = Depends(get_optional_user),
                         db: AsyncSession = Depends(get_db)):
    svc = SkillsRegistry(db)
    return await svc.search_skills(user_id or "", keyword)


@router.post("/scan")
async def scan_and_sync(user_id: str = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    svc = SkillsRegistry(db)
    return await svc.scan_and_sync(user_id)
