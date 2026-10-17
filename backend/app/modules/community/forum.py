from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.dao.dao import CommunityDAO


class ForumService:
    def __init__(self, db: AsyncSession):
        self.dao = CommunityDAO(db)

    async def create_post(self, author_id: str, title: str, content: str) -> dict:
        if not title.strip():
            raise ValueError("标题不能为空")
        if not content.strip():
            raise ValueError("内容不能为空")
        if len(title) > 200:
            raise ValueError("标题不能超过200字符")
        if len(content) > 10000:
            raise ValueError("内容不能超过10000字符")
        post = await self.dao.create_post(author_id, title, content)
        return {"id": post.id, "title": post.title, "created_at": post.created_at}

    async def list_posts(self, page: int = 1, page_size: int = 20) -> dict:
        offset = (page - 1) * page_size
        posts = await self.dao.list_posts(offset=offset, limit=page_size)
        return {"items": posts, "page": page, "page_size": page_size}

    async def toggle_like(self, post_id: str, user_id: str) -> dict:
        liked = await self.dao.toggle_like(post_id, user_id)
        post = await self.dao.get_post_by_id(post_id)
        return {"liked": liked, "like_count": post.like_count if post else 0}

    async def create_comment(self, post_id: str, author_id: str, content: str) -> dict:
        if not content.strip():
            raise ValueError("评论内容不能为空")
        comment = await self.dao.create_comment(post_id, author_id, content)
        return {"id": comment.id, "content": comment.content, "created_at": comment.created_at}
