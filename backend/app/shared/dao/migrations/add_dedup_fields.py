import asyncio
from sqlalchemy import text
from app.core.database import engine


async def upgrade():
    async with engine.begin() as conn:
        await conn.execute(text(
            "ALTER TABLE pdf_guides ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64) DEFAULT NULL"
        ))
        await conn.execute(text(
            "ALTER TABLE conversion_tasks ADD COLUMN IF NOT EXISTS dedup_pending_info JSONB DEFAULT NULL"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_pdf_guides_user_hash "
            "ON pdf_guides(user_id, content_hash) WHERE content_hash IS NOT NULL"
        ))
    print("迁移完成：content_hash字段、dedup_pending_info字段、idx_pdf_guides_user_hash索引")


async def downgrade():
    async with engine.begin() as conn:
        await conn.execute(text("DROP INDEX IF EXISTS idx_pdf_guides_user_hash"))
        await conn.execute(text("ALTER TABLE conversion_tasks DROP COLUMN IF EXISTS dedup_pending_info"))
        await conn.execute(text("ALTER TABLE pdf_guides DROP COLUMN IF EXISTS content_hash"))
    print("回滚完成")


if __name__ == "__main__":
    asyncio.run(upgrade())
