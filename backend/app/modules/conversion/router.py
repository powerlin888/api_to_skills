import logging
import asyncio
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.core.config import get_settings
from app.modules.conversion.service import ConversionEngine
from app.modules.conversion.models import ConversionTaskDTO, ConversionResultDTO, ConfirmDedupRequestDTO

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pdf", tags=["pdf-conversion"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="未认证")
    return payload["sub"]


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...),
                     user_id: str = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    settings = get_settings()
    content = await file.read()
    logger.info(f"[PDF上传] user={user_id}, filename={file.filename}, size={len(content)}")
    engine = ConversionEngine(db)
    try:
        result = await engine.upload_and_convert(
            user_id=user_id, filename=file.filename or "upload.pdf",
            original_name=file.filename or "upload.pdf",
            file_size=len(content), file_content=content
        )
        logger.info(f"[PDF上传] 转换任务已创建: task_id={result.get('task_id')}, guide_id={result.get('guide_id')}")
        return result
    except ValueError as e:
        logger.warning(f"[PDF上传] 参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"[PDF上传] 上传处理异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_pipeline_in_bg(task_id: str, guide_id: str, user_id: str, pdf_path: str):
    from app.core.database import async_session
    from app.modules.conversion.service import ConversionEngine
    from pathlib import Path
    print(f"[Pipeline-后台] 启动: task={task_id[:8]}", flush=True)
    async with async_session() as db:
        try:
            engine = ConversionEngine(db)
            await engine._run_pipeline(task_id, guide_id, user_id, Path(pdf_path))
        except Exception as e:
            print(f"[Pipeline-后台] 异常: task={task_id[:8]}, error={e}", flush=True)


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, user_id: str = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    engine = ConversionEngine(db)
    result = await engine.get_task_status(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="任务不存在")
    return result


@router.get("/tasks")
async def list_tasks(user_id: str = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    engine = ConversionEngine(db)
    return await engine.list_tasks(user_id)


@router.get("/guides/{guide_id}/skills")
async def get_guide_skills(guide_id: str, user_id: str = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    from app.shared.dao.dao import SkillDAO
    from sqlalchemy import select
    from app.shared.dao.models import SkillGroup
    dao = SkillDAO(db)
    result = await db.execute(select(SkillGroup).where(SkillGroup.guide_id == guide_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="未找到对应的Skills群")
    skills = await dao.list_skills_by_group(group.id)
    return {"group_id": group.id, "group_name": group.name,
            "skills": [{"id": s.id, "name": s.name, "description": s.description} for s in skills]}


@router.post("/tasks/{task_id}/confirm-dedup")
async def confirm_dedup(task_id: str, request: ConfirmDedupRequestDTO,
                        user_id: str = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    engine = ConversionEngine(db)
    try:
        if request.action == "continue":
            return await engine.continue_conversion(task_id)
        elif request.action == "cancel":
            return await engine.cancel_as_duplicate(task_id)
        else:
            raise HTTPException(status_code=400, detail="action必须为continue或cancel")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
