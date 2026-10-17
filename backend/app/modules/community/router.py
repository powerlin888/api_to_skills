from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.modules.community.service import CommunityService
from app.modules.community.models import (
    RegisterDTO, LoginDTO, TokenDTO, UserDTO, CheckInResultDTO,
    PostCreateDTO, PostDTO, CommentCreateDTO, CommentDTO, LikeResultDTO
)

router = APIRouter(prefix="/api", tags=["community"])
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")
    return payload["sub"]


async def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(optional_security)) -> str | None:
    if not credentials:
        return None
    payload = verify_token(credentials.credentials)
    return payload["sub"] if payload else None


@router.post("/auth/register", response_model=TokenDTO)
async def register(dto: RegisterDTO, db: AsyncSession = Depends(get_db)):
    svc = CommunityService(db)
    try:
        result = await svc.register(dto.email, dto.nickname, dto.password)
        return TokenDTO(access_token=result["access_token"], refresh_token=result["refresh_token"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login", response_model=TokenDTO)
async def login(dto: LoginDTO, db: AsyncSession = Depends(get_db)):
    svc = CommunityService(db)
    try:
        result = await svc.login(dto.email, dto.password)
        return TokenDTO(access_token=result["access_token"], refresh_token=result["refresh_token"])
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/refresh", response_model=TokenDTO)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    svc = CommunityService(db)
    try:
        result = await svc.refresh(refresh_token)
        return TokenDTO(access_token=result["access_token"], refresh_token=result["refresh_token"])
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/auth/me", response_model=UserDTO)
async def get_me(user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CommunityService(db)
    try:
        result = await svc.get_me(user_id)
        return UserDTO(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/community/check-in", response_model=CheckInResultDTO)
async def check_in(user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = CommunityService(db)
    result = await svc.check_in(user_id)
    return CheckInResultDTO(**result)


@router.post("/community/posts")
async def create_post(dto: PostCreateDTO, user_id: str = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    svc = CommunityService(db)
    try:
        return await svc.create_post(user_id, dto.title, dto.content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/community/posts")
async def list_posts(page: int = 1, page_size: int = 20,
                     user_id: str | None = Depends(get_optional_user),
                     db: AsyncSession = Depends(get_db)):
    svc = CommunityService(db)
    return await svc.list_posts(page, page_size)


@router.post("/community/posts/{post_id}/like", response_model=LikeResultDTO)
async def toggle_like(post_id: str, user_id: str = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    svc = CommunityService(db)
    result = await svc.toggle_like(post_id, user_id)
    return LikeResultDTO(**result)


@router.post("/community/posts/{post_id}/comments", response_model=CommentDTO)
async def create_comment(post_id: str, dto: CommentCreateDTO,
                         user_id: str = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    svc = CommunityService(db)
    try:
        result = await svc.create_comment(post_id, user_id, dto.content)
        return CommentDTO(id=result["id"], post_id=post_id, author_id=user_id,
                          content=result["content"], created_at=result["created_at"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
