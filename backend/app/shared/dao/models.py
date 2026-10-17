import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Text, Boolean, DateTime, ForeignKey, Enum, Float, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class PostStatus(str, enum.Enum):
    PUBLISHED = "published"
    PENDING = "pending"
    DELETED = "deleted"


class ConversionStatus(str, enum.Enum):
    PENDING = "pending"
    PARSING = "parsing"
    DEDUP_CHECK = "dedup_check"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    ENRICHING = "enriching"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class ModelProvider(str, enum.Enum):
    MODELSCOPE = "modelscope"
    OPENAI = "openai"
    LOCAL = "local"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nickname = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    points = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    check_ins = relationship("CheckIn", back_populates="user", lazy="selectin")
    posts = relationship("Post", back_populates="author", lazy="selectin")
    agents = relationship("Agent", back_populates="user", lazy="selectin")


class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    check_in_date = Column(DateTime, nullable=False)
    points_earned = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="check_ins")


class PdfGuide(Base):
    __tablename__ = "pdf_guides"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    markdown_path = Column(String(500), nullable=True)
    content_hash = Column(String(64), nullable=True)
    status = Column(Enum(ConversionStatus), default=ConversionStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    skill_groups = relationship("SkillGroup", back_populates="guide", lazy="selectin")
    conversion_tasks = relationship("ConversionTask", back_populates="guide", lazy="selectin")


class SkillGroup(Base):
    __tablename__ = "skill_groups"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    guide_id = Column(String(36), ForeignKey("pdf_guides.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dir_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    guide = relationship("PdfGuide", back_populates="skill_groups")
    skills = relationship("Skill", back_populates="group", lazy="selectin")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True)
    group_id = Column(String(36), ForeignKey("skill_groups.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    dir_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("SkillGroup", back_populates="skills")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model_provider = Column(Enum(ModelProvider), default=ModelProvider.MODELSCOPE)
    model_id = Column(String(255), nullable=False)
    api_key_encrypted = Column(Text, nullable=True)
    base_url = Column(String(500), nullable=True)
    skill_group_ids = Column(JSON, default=list)
    knowledge_enabled = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="agents")
    metrics = relationship("AgentMetric", back_populates="agent", lazy="selectin")


class AgentMetric(Base):
    __tablename__ = "agent_metrics"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    session_id = Column(String(36), nullable=True, index=True)
    model_calls = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    tool_calls = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="metrics")


class Post(Base):
    __tablename__ = "posts"

    id = Column(String(36), primary_key=True)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(PostStatus), default=PostStatus.PUBLISHED)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", lazy="selectin")
    likes = relationship("PostLike", back_populates="post", lazy="selectin")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String(36), primary_key=True)
    post_id = Column(String(36), ForeignKey("posts.id"), nullable=False, index=True)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")


class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(String(36), primary_key=True)
    post_id = Column(String(36), ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="likes")


class ConversionTask(Base):
    __tablename__ = "conversion_tasks"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    guide_id = Column(String(36), ForeignKey("pdf_guides.id"), nullable=True)
    status = Column(Enum(ConversionStatus), default=ConversionStatus.PENDING)
    current_stage = Column(String(50), nullable=True)
    stage_info = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    result_skill_group_id = Column(String(36), nullable=True)
    dedup_pending_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guide = relationship("PdfGuide", back_populates="conversion_tasks")
