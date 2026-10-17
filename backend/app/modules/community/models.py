from pydantic import BaseModel, EmailStr
from datetime import datetime


class RegisterDTO(BaseModel):
    email: EmailStr
    nickname: str
    password: str


class LoginDTO(BaseModel):
    email: EmailStr
    password: str


class TokenDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserDTO(BaseModel):
    id: str
    email: str
    nickname: str
    role: str
    points: int
    created_at: datetime


class CheckInResultDTO(BaseModel):
    success: bool
    points_earned: int = 0
    total_points: int = 0
    message: str


class PostCreateDTO(BaseModel):
    title: str
    content: str


class PostDTO(BaseModel):
    id: str
    author_id: str
    author_nickname: str
    title: str
    content: str
    status: str
    like_count: int
    comment_count: int
    created_at: datetime


class CommentCreateDTO(BaseModel):
    content: str


class CommentDTO(BaseModel):
    id: str
    post_id: str
    author_id: str
    content: str
    created_at: datetime


class LikeResultDTO(BaseModel):
    liked: bool
    like_count: int
