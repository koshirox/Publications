from datetime import datetime
from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

Id = Annotated[int, Path(gt=0, le=2**63 - 1)]


class Credentials(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: SecretStr = Field(min_length=5, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmailUpdate(BaseModel):
    email: EmailStr = Field(max_length=255)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str


class Profile(UserOut):
    email: str


class SubscriptionList(BaseModel):
    count: int
    users: list[UserOut]


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class PostIn(BaseModel):
    category_id: int = Field(gt=0, le=2**63 - 1)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    category_id: int
    title: str
    body: str
    status: str
    created_at: datetime
    published_at: datetime | None


class CommentIn(BaseModel):
    body: str = Field(min_length=1)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    user_id: int
    body: str
    created_at: datetime


class LikeCount(BaseModel):
    count: int
