from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")
    return payload["sub"]


async def get_admin_user(user_id: str = Depends(get_current_user)) -> str:
    from app.core.database import async_session
    from app.shared.dao.dao import UserDAO
    async with async_session() as db:
        dao = UserDAO(db)
        user = await dao.get_by_id(user_id)
        if not user or user.role.value != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user_id
