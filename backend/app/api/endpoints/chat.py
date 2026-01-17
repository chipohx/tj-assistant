from typing import Annotated
from datetime import datetime
from uuid import UUID
import httpx
import requests

from fastapi import Depends, APIRouter, HTTPException, Query
from sqlalchemy.orm import Session, defer
from sqlalchemy import Select

from app.core.user import get_current_active_user, get_user
from app.models.models import Message, Role, Chat, User
from app.database.session import get_db
from app.api.schemas.schemas import (
    MessageSchema,
    ChatRequest,
    ChatResponse,
    MessagesListResponse,
    UserSchema,
    NewChat,
)

router = APIRouter()


def create_message_in_db(db: Session, content: str, role: Role, chat_id: UUID) -> UUID:
    try:
        new_message = Message(chat_id=chat_id, content=content, role=role)
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return new_message.id
    except Exception as e:
        print(f"Error: {e}")


def create_chat(db: Session, title: str, user: User):
    try:
        new_chat = Chat(title=title, user_id=user.id)
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        return new_chat.id
    except Exception as e:
        print(f"Error: {e}")
        return


@router.post("/new-chat")
async def new_chat(
    user: Annotated[UserSchema, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> NewChat:
    chat_id = create_chat(db, title="Новый чат", user=user)
    return NewChat(chat_id=chat_id)


@router.post("/chat")
async def send_message(
    request: ChatRequest,
    user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> ChatResponse:
    return ChatResponse(
        content="Привет",
        timestamp=datetime.now(),
        chat_created=UUID("12345678-1234-5678-1234-567812345678"),
    )


# @router.post("/chat")
# async def send_message(
#     request: ChatRequest,
#     user: Annotated[User, Depends(get_current_active_user)],
#     db: Session = Depends(get_db),
# ) -> ChatResponse:

#     if not request.chat_id:
#         chat_created = create_chat(db, request.content[:30], user)
#     chat_id = chat_created if chat_created else request.chat_id

#     create_message_in_db(db, request.content, Role.USER, chat_id)

#     async with httpx.AsyncClient() as client:
#         try:
#             health_check = await client.get("http://main:8001/health", timeout=30.0)

#             if health_check.status_code != 200:
#                 print(f"Health check failed: {health_check.status_code}")
#                 raise HTTPException(
#                     status_code=503,
#                     detail=f"LLM service health check failed: {health_check.text}",
#                 )

#             response = await client.post(
#                 "http://main:8001/llm_response",
#                 json={"query": request.content},
#                 timeout=60.0,
#             )
#         except httpx.RequestError as e:
#             print(f"Ошибка сети: {e}")
#             raise HTTPException(status_code=500, detail="LLM service unreachable")

#     if response.status_code != 200:
#         raise HTTPException(status_code=502, detail="Failed generating response")

#     try:
#         response_dict = response.json()
#     except ValueError:
#         raise HTTPException(status_code=502, detail="Invalid JSON from LLM service")

#     response_content = response_dict["response"]

#     if response_content:
#         message_id = create_message_in_db(db, response_content, Role.SYSTEM, chat_id)

#         return ChatResponse(
#             content=response_content,
#             timestamp=datetime.now(),
#             chat_created=chat_id,
#         )
#     else:
#         raise HTTPException(status_code=502, detail="Empty response from LLM service")


@router.get("/chats")
async def get_chats(
    user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    try:
        chats = db.scalars(
            Select(Chat)
            .filter(Chat.user_id == user.id)
            .options(defer(Chat.user_id))
            .order_by(Chat.created.asc())
        )
    except Exception as e:
        print(f"Ошибка при попытке получить чаты: {e}")

    return {"items": [chat.__dict__ for chat in chats]}


@router.get("/chat/{chat_id}/messages", response_model=MessagesListResponse)
async def get_chat_sessions(
    chat_id: UUID,
    user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=30),
    last_id: UUID | None = None,
):
    chat = db.scalar(Select(Chat).filter(Chat.id == chat_id))

    if chat.user_id != user.id:
        raise HTTPException(status_code=401, detail="Access forbidden")

    try:
        db_messages = db.scalars(
            Select(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.created.asc())
            .limit(limit)
        ).all()
    except Exception as e:
        print(f"Ошибка при попытке получить сообщения из чата {chat.title}: {e}")

    response_data = {
        "count": len(db_messages),
        "next_id": db_messages[-1].id if db_messages else None,
        "items": [msg.__dict__ for msg in db_messages],
    }

    return MessagesListResponse[MessageSchema].model_validate(response_data)
