import asyncio
from app.core.database import engine, Base
from app.shared.dao.models import User, UserRole
from app.core.security import hash_password


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.core.database import async_session
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.role == UserRole.ADMIN))
        if result.scalar_one_or_none() is None:
            admin = User(
                id="admin-001",
                email="admin@platform.local",
                nickname="管理员",
                password_hash=hash_password("admin123"),
                role=UserRole.ADMIN,
                points=0,
            )
            session.add(admin)
            await session.commit()
            print("管理员种子数据已插入")
        else:
            print("管理员已存在，跳过")


if __name__ == "__main__":
    asyncio.run(init_db())
