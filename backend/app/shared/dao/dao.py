import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.shared.dao.models import (
    User, UserRole, PdfGuide, SkillGroup, Skill, Agent, AgentMetric,
    Post, Comment, PostLike, CheckIn, ConversionTask
)


def _new_id() -> str:
    return str(uuid.uuid4())


class UserDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, email: str, nickname: str, password_hash: str) -> User:
        user = User(id=_new_id(), email=email, nickname=nickname, password_hash=password_hash)
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update(self, user_id: str, **kwargs) -> None:
        await self.db.execute(update(User).where(User.id == user_id).values(**kwargs))

    async def list_users(self, offset: int = 0, limit: int = 20) -> list[User]:
        result = await self.db.execute(select(User).offset(offset).limit(limit))
        return list(result.scalars().all())


class GuideDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, filename: str, original_name: str, file_size: int) -> PdfGuide:
        guide = PdfGuide(id=_new_id(), user_id=user_id, filename=filename,
                         original_name=original_name, file_size=file_size)
        self.db.add(guide)
        await self.db.flush()
        return guide

    async def get_by_id(self, guide_id: str) -> PdfGuide | None:
        result = await self.db.execute(select(PdfGuide).where(PdfGuide.id == guide_id))
        return result.scalar_one_or_none()

    async def update(self, guide_id: str, **kwargs) -> None:
        await self.db.execute(update(PdfGuide).where(PdfGuide.id == guide_id).values(**kwargs))

    async def list_by_user(self, user_id: str, offset: int = 0, limit: int = 20) -> list[PdfGuide]:
        result = await self.db.execute(
            select(PdfGuide).where(PdfGuide.user_id == user_id).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def find_by_content_hash(self, user_id: str, content_hash: str) -> PdfGuide | None:
        result = await self.db.execute(
            select(PdfGuide).where(
                PdfGuide.user_id == user_id,
                PdfGuide.content_hash == content_hash
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def list_with_content_hash(self, user_id: str, limit: int = 50) -> list[PdfGuide]:
        result = await self.db.execute(
            select(PdfGuide).where(
                PdfGuide.user_id == user_id,
                PdfGuide.content_hash.isnot(None),
                PdfGuide.markdown_path.isnot(None)
            ).limit(limit)
        )
        return list(result.scalars().all())


class SkillDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_group(self, user_id: str, name: str, dir_path: str,
                           guide_id: str | None = None, description: str | None = None) -> SkillGroup:
        group = SkillGroup(id=_new_id(), user_id=user_id, name=name, dir_path=dir_path,
                           guide_id=guide_id, description=description)
        self.db.add(group)
        await self.db.flush()
        return group

    async def get_group_by_id(self, group_id: str) -> SkillGroup | None:
        result = await self.db.execute(select(SkillGroup).where(SkillGroup.id == group_id))
        return result.scalar_one_or_none()

    async def list_groups_by_user(self, user_id: str) -> list[SkillGroup]:
        result = await self.db.execute(select(SkillGroup).where(SkillGroup.user_id == user_id))
        return list(result.scalars().all())

    async def create_skill(self, group_id: str, name: str, dir_path: str,
                           description: str | None = None, tags: list | None = None) -> Skill:
        skill = Skill(id=_new_id(), group_id=group_id, name=name, dir_path=dir_path,
                      description=description, tags=tags or [])
        self.db.add(skill)
        await self.db.flush()
        return skill

    async def list_skills_by_group(self, group_id: str) -> list[Skill]:
        result = await self.db.execute(select(Skill).where(Skill.group_id == group_id))
        return list(result.scalars().all())


class AgentDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, name: str, model_provider: str, model_id: str,
                     **kwargs) -> Agent:
        agent = Agent(id=_new_id(), user_id=user_id, name=name,
                      model_provider=model_provider, model_id=model_id, **kwargs)
        self.db.add(agent)
        await self.db.flush()
        return agent

    async def get_by_id(self, agent_id: str) -> Agent | None:
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def update(self, agent_id: str, **kwargs) -> None:
        await self.db.execute(update(Agent).where(Agent.id == agent_id).values(**kwargs))

    async def delete(self, agent_id: str) -> None:
        await self.db.execute(delete(Agent).where(Agent.id == agent_id))

    async def list_by_user(self, user_id: str) -> list[Agent]:
        result = await self.db.execute(select(Agent).where(Agent.user_id == user_id))
        return list(result.scalars().all())

    async def add_metric(self, agent_id: str, session_id: str | None = None, **kwargs) -> AgentMetric:
        metric = AgentMetric(id=_new_id(), agent_id=agent_id, session_id=session_id, **kwargs)
        self.db.add(metric)
        await self.db.flush()
        return metric


class CommunityDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_check_in(self, user_id: str, check_in_date: datetime, points: int = 10) -> CheckIn:
        ci = CheckIn(id=_new_id(), user_id=user_id, check_in_date=check_in_date, points_earned=points)
        self.db.add(ci)
        await self.db.flush()
        return ci

    async def get_today_check_in(self, user_id: str, date: datetime) -> CheckIn | None:
        result = await self.db.execute(
            select(CheckIn).where(CheckIn.user_id == user_id, CheckIn.check_in_date == date)
        )
        return result.scalar_one_or_none()

    async def create_post(self, author_id: str, title: str, content: str) -> Post:
        post = Post(id=_new_id(), author_id=author_id, title=title, content=content)
        self.db.add(post)
        await self.db.flush()
        return post

    async def get_post_by_id(self, post_id: str) -> Post | None:
        result = await self.db.execute(select(Post).where(Post.id == post_id))
        return result.scalar_one_or_none()

    async def list_posts(self, offset: int = 0, limit: int = 20) -> list[Post]:
        result = await self.db.execute(
            select(Post).where(Post.status == "published").offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def create_comment(self, post_id: str, author_id: str, content: str) -> Comment:
        comment = Comment(id=_new_id(), post_id=post_id, author_id=author_id, content=content)
        self.db.add(comment)
        await self.db.flush()
        return comment

    async def toggle_like(self, post_id: str, user_id: str) -> bool:
        result = await self.db.execute(
            select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            await self.db.delete(existing)
            await self.db.execute(
                update(Post).where(Post.id == post_id).values(like_count=Post.like_count - 1)
            )
            return False
        else:
            like = PostLike(id=_new_id(), post_id=post_id, user_id=user_id)
            self.db.add(like)
            await self.db.execute(
                update(Post).where(Post.id == post_id).values(like_count=Post.like_count + 1)
            )
            return True


class ConversionTaskDAO:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, guide_id: str | None = None) -> ConversionTask:
        task = ConversionTask(id=_new_id(), user_id=user_id, guide_id=guide_id)
        self.db.add(task)
        await self.db.flush()
        return task

    async def get_by_id(self, task_id: str) -> ConversionTask | None:
        result = await self.db.execute(select(ConversionTask).where(ConversionTask.id == task_id))
        return result.scalar_one_or_none()

    async def update(self, task_id: str, **kwargs) -> None:
        await self.db.execute(update(ConversionTask).where(ConversionTask.id == task_id).values(**kwargs))

    async def list_by_user(self, user_id: str) -> list[ConversionTask]:
        result = await self.db.execute(
            select(ConversionTask).where(ConversionTask.user_id == user_id)
        )
        return list(result.scalars().all())
