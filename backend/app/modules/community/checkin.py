from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.dao.dao import CommunityDAO, UserDAO


class CheckInService:
    def __init__(self, db: AsyncSession):
        self.dao = CommunityDAO(db)
        self.user_dao = UserDAO(db)

    async def check_in(self, user_id: str) -> dict:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        existing = await self.dao.get_today_check_in(user_id, today)
        if existing:
            return {"success": False, "points_earned": 0, "message": "今日已签到"}
        ci = await self.dao.create_check_in(user_id, today, points=10)
        user = await self.user_dao.get_by_id(user_id)
        new_points = (user.points if user else 0) + 10
        await self.user_dao.update(user_id, points=new_points)
        return {"success": True, "points_earned": 10, "total_points": new_points, "message": "签到成功，+10积分"}
