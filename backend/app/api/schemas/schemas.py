from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from typing import List


class ChatRequest(BaseModel):
    content: str
    chat_id: UUID


class ChatResponse(BaseModel):
    message_id: int
    content: str
    timestamp: datetime
    chat_created: str


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
