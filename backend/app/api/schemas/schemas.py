from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from typing import List, Generic, TypeVar
from app.models.models import Role

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    count: int
    next_id: UUID | None = None
    items: List[T]


class MessagesListResponse(PaginatedResponse):
    pass


class ChatRequest(BaseModel):
    content: str
    chat_id: UUID | None = None


class NewChat(BaseModel):
    chat_id: UUID


class MessageSchema(BaseModel):
    message_id: UUID
    content: str
    created: datetime
    role: Role


class ChatResponse(BaseModel):
    message_id: UUID
    content: str
    timestamp: datetime
    chat_created: UUID | None


class UserSchema(BaseModel):
    username: str


class UserDBSchema(UserSchema):
    hashed_password: str


class NewUser(BaseModel):
    username: str
    plain_password: str


class SessionResponse(BaseModel):
    id: UUID
    title: str
    created: datetime
    updated: datetime


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class DeleteChatResponse(BaseModel):
    message: str
    deleted_chat_id: UUID
