# from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ChatRequest(BaseModel):
    content: str


class ChatResponse(BaseModel):
    message_id: int
    content: str
    timestamp: datetime
