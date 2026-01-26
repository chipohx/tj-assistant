from datetime import datetime
from typing import Annotated
from uuid import UUID


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select
from sqlalchemy.orm import defer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.schemas import (
    ChatRequest,
    ChatResponse,
    MessagesListResponse,
    NewChat,
    UserSchema,
    MessageSchema,
)
from app.core.user import get_current_active_user
from app.database.db import create_chat, create_message
from app.database.session_async import get_db
from app.models.models import Chat, Message, Role, User
from app.services.llm import request_llm_response


router = APIRouter()


@router.post("/new-chat")
async def new_chat(
    user: Annotated[UserSchema, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> NewChat:
    chat_id = await create_chat(db, title="Новый чат", user=user)
    return NewChat(chat_id=chat_id)


@router.post("/chat")
async def send_message(
    request: ChatRequest,
    user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:

    chat_created = None
    if not request.chat_id:
        chat_created = await create_chat(db, request.content[:30], user)
    chat_id = chat_created if chat_created else request.chat_id

    await create_message(db, request.content, Role.USER, chat_id)

    response_content = await request_llm_response(request.content)
    if response_content:
        await create_message(db, response_content, Role.SYSTEM, chat_id)

        return ChatResponse(
            content=response_content,
            timestamp=datetime.now(),
            chat_created=chat_id,
        )
    else:
        raise HTTPException(status_code=502, detail="Empty response from LLM service")


@router.get("/chats")
async def get_chats(
    user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.scalars(
            Select(Chat)
            .filter(Chat.user_id == user.id)
            .options(defer(Chat.user_id))
            .order_by(Chat.created.asc())
        )
        chats = result.all()
    except Exception as e:
        print(f"Ошибка при попытке получить чаты: {e}")
        return {"items": [], "count": 0}

    return {"items": chats, "count": len(chats)}


@router.get("/chat/{chat_id}/messages", response_model=MessagesListResponse)
async def get_chat_sessions(
    chat_id: UUID,
    user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=30),
    last_id: UUID | None = None,
):
    chat: Chat = await db.scalar(Select(Chat).filter(Chat.id == chat_id))

    if chat.user_id != user.id:
        raise HTTPException(status_code=401, detail="Access forbidden")

    db_messages = []
    try:
        db_messages = (
            await db.scalars(
                Select(Message)
                .filter(Message.chat_id == chat_id)
                .order_by(Message.created.asc())
                .limit(limit)
            )
        ).all()
    except Exception as e:
        print(f"Ошибка при попытке получить сообщения из чата {chat.title}: {e}")

    print(db_messages)

    response_data = {
        "count": len(db_messages),
        "next_id": db_messages[-1].id if db_messages else None,
        "items": [msg.__dict__ for msg in db_messages],
    }

    return MessagesListResponse[MessageSchema].model_validate(response_data)


# @router.post("/chat")
# async def send_message(
#     request: ChatRequest,
#     user: Annotated[User, Depends(get_current_active_user)],
#     db: AsyncSession = Depends(get_db),
# ) -> ChatResponse:
#     return ChatResponse(
#         content="Привет",
#         timestamp=datetime.now(),
#         chat_created=UUID("12345678-1234-5678-1234-567812345678"),
#     )
