from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token, encrypt_api_key, decrypt_api_key, mask_api_key
from app.shared.dao.dao import AgentDAO

router = APIRouter(prefix="/api/model", tags=["model-config"])
security = HTTPBearer()


class ModelConfigSaveDTO(BaseModel):
    provider: str = "modelscope"
    model_id: str = ""
    api_key: str = ""
    base_url: str = ""


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="未认证")
    return payload["sub"]


@router.get("/providers")
async def get_providers():
    return [
        {"id": "modelscope", "name": "魔搭社区(ModelScope)", "default_base_url": "https://api-inference.modelscope.cn/v1/"},
        {"id": "openai", "name": "OpenAI", "default_base_url": "https://api.openai.com/v1/"},
        {"id": "local", "name": "本地模型", "default_base_url": "http://localhost:11434/v1/"},
    ]


@router.post("/config")
async def save_model_config(dto: ModelConfigSaveDTO,
                            user_id: str = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    return {
        "provider": dto.provider,
        "model_id": dto.model_id,
        "api_key_masked": mask_api_key(dto.api_key) if dto.api_key else "",
        "base_url": dto.base_url,
        "saved": True,
    }


@router.get("/config")
async def get_model_config(user_id: str = Depends(get_current_user)):
    return {"message": "请在前端管理模型配置"}
