from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.community.auth import UserAuthService
from app.modules.community.checkin import CheckInService
from app.modules.community.forum import ForumService
from app.shared.dao.dao import UserDAO


class CommunityService:
    def __init__(self, db: AsyncSession):
        self.auth = UserAuthService(db)
        self.checkin = CheckInService(db)
        self.forum = ForumService(db)
        self.user_dao = UserDAO(db)

    async def register(self, email: str, nickname: str, password: str) -> dict:
        return await self.auth.register(email, nickname, password)

    async def login(self, email: str, password: str) -> dict:
        return await self.auth.login(email, password)

    async def refresh(self, refresh_token: str) -> dict:
        return await self.auth.refresh(refresh_token)

    async def get_me(self, user_id: str) -> dict:
        return await self.auth.get_me(user_id)

    async def check_in(self, user_id: str) -> dict:
        return await self.checkin.check_in(user_id)

    async def create_post(self, author_id: str, title: str, content: str) -> dict:
        return await self.forum.create_post(author_id, title, content)

    async def list_posts(self, page: int = 1, page_size: int = 20) -> dict:
        return await self.forum.list_posts(page, page_size)

    async def toggle_like(self, post_id: str, user_id: str) -> dict:
        return await self.forum.toggle_like(post_id, user_id)

    async def create_comment(self, post_id: str, author_id: str, content: str) -> dict:
        return await self.forum.create_comment(post_id, author_id, content)

    async def update_role(self, user_id: str, new_role: str, admin_id: str) -> dict:
        admin = await self.user_dao.get_by_id(admin_id)
        if not admin or admin.role.value != "admin":
            raise ValueError("需要管理员权限")
        await self.user_dao.update(user_id, role=new_role)
        return {"user_id": user_id, "new_role": new_role}
