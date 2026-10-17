from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from app.shared.dao.dao import UserDAO


class UserAuthService:
    def __init__(self, db: AsyncSession):
        self.dao = UserDAO(db)

    async def register(self, email: str, nickname: str, password: str) -> dict:
        existing = await self.dao.get_by_email(email)
        if existing:
            raise ValueError("邮箱已被注册")
        if len(password) < 8:
            raise ValueError("密码至少8个字符")
        pw_hash = hash_password(password)
        user = await self.dao.create(email=email, nickname=nickname, password_hash=pw_hash)
        access = create_access_token({"sub": user.id, "role": user.role.value})
        refresh = create_refresh_token({"sub": user.id})
        return {"access_token": access, "refresh_token": refresh, "user_id": user.id}

    async def login(self, email: str, password: str) -> dict:
        user = await self.dao.get_by_email(email)
        if not user:
            raise ValueError("用户不存在")
        if user.is_locked and user.locked_until and user.locked_until > datetime.now(timezone.utc):
            raise ValueError(f"账户已锁定，请{int((user.locked_until - datetime.now(timezone.utc)).total_seconds()/60)}分钟后重试")
        if not verify_password(password, user.password_hash):
            new_attempts = user.failed_attempts + 1
            if new_attempts >= 5:
                await self.dao.update(user.id, is_locked=True, failed_attempts=new_attempts,
                                      locked_until=datetime.now(timezone.utc) + timedelta(minutes=15))
                raise ValueError("密码错误5次，账户已锁定15分钟")
            await self.dao.update(user.id, failed_attempts=new_attempts)
            raise ValueError("密码错误")
        await self.dao.update(user.id, failed_attempts=0, is_locked=False, locked_until=None)
        access = create_access_token({"sub": user.id, "role": user.role.value})
        refresh = create_refresh_token({"sub": user.id})
        return {"access_token": access, "refresh_token": refresh, "user_id": user.id}

    async def refresh(self, refresh_token: str) -> dict:
        payload = verify_token(refresh_token, expected_type="refresh")
        if not payload:
            raise ValueError("无效的refresh token")
        user = await self.dao.get_by_id(payload["sub"])
        if not user:
            raise ValueError("用户不存在")
        access = create_access_token({"sub": user.id, "role": user.role.value})
        new_refresh = create_refresh_token({"sub": user.id})
        return {"access_token": access, "refresh_token": new_refresh}

    async def get_me(self, user_id: str) -> dict:
        user = await self.dao.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        return {"id": user.id, "email": user.email, "nickname": user.nickname,
                "role": user.role.value, "points": user.points, "created_at": user.created_at}
