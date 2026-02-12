from datetime import datetime
from typing import Annotated, List
from uuid import UUID


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, func
from sqlalchemy.orm import defer, selectinload
from sqlalchemy.ext.asyncio import AsyncSession


from app.api.schemas.schemas import (
    ChatRequest,
    ChatResponse,
    MessagesListResponse,
    NewChat,
    UserSchema,
    MessageSchema,
    DeleteChatResponse,
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

    chat_id = None
    if not request.chat_id:
        chat_id = await create_chat(db, request.content[:30], user)
    else:
        chat_id = request.chat_id

    await create_message(db, request.content, Role.USER, chat_id)

    response_content = await request_llm_response(request.content)

    # response_content = (
    #     f"Это тестовый ответ от ассистента на ваш запрос: '{request.content}'."
    #     "ML-сервис находится в разработке и будет подключен позже."
    # )

    assistant_message_id = await create_message(
        db, response_content, Role.SYSTEM, chat_id
    )

    return ChatResponse(
        message_id=assistant_message_id,
        content=response_content,
        timestamp=datetime.now(),
        chat_created=chat_id,
    )


@router.get("/chats")
async def get_chats(
    user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """Возвращяет список чатов"""

    try:
        chats = (
            await db.scalars(
                Select(Chat)
                .filter(Chat.user_id == user.id)
                .options(defer(Chat.user_id))
                .order_by(Chat.created.asc())
            )
        ).all()

        return {
            "items": [
                {
                    "id": str(chat.id),
                    "title": chat.title,
                    "created": chat.created,
                    "updated": chat.updated,
                }
                for chat in chats
            ],
            "count": len(chats),
        }

    except Exception:
        return {"items": [], "count": 0}


@router.get("/chat/{chat_id}/messages", response_model=MessagesListResponse)
async def get_chat_sessions(
    chat_id: UUID,
    user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=30),
    last_id: UUID | None = None,
):

    try:
        chat: Chat = await db.scalar(Select(Chat).filter(Chat.id == chat_id))

        if not chat:
            raise HTTPException(status_code=404, detail="Content not found")
        if chat.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access forbidden")

        # Базовый запрос
        query = (
            Select(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.created.asc())
        )

        # Если указан last_id, получаем сообщения после него
        if last_id:
            last_message = await db.scalar(
                Select(Message).filter(Message.id == last_id)
            )
            if last_message:
                query = query.filter(Message.created > last_message.created)

        # Применяем лимит
        query = query.limit(limit)

        db_messages = (await db.scalars(query)).all()

        response_data = {
            "count": len(db_messages),
            "next_id": db_messages[-1].id if db_messages else None,
            "items": [
                {
                    "message_id": str(msg.id),
                    "content": msg.content,
                    "created": msg.created,
                    "role": msg.role.value,
                }
                for msg in db_messages
            ],
        }

        return MessagesListResponse[MessageSchema].model_validate(response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.delete("/chat/{chat_id}")
async def delete_chat_with_messages(
    chat_id: UUID,
    user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Каскадно удаляет чат и все связанные с ним сообщения
    (ручное каскадное удаление).
    """

    chat = await db.scalar(Select(Chat).filter(Chat.id == chat_id))

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    try:
        messages_count = await db.scalar(
            Select(func.count(Message.id)).filter(Message.chat_id == chat_id)
        )

        await db.execute(Message.__table__.delete().where(Message.chat_id == chat_id))

        await db.delete(chat)
        await db.commit()

        return DeleteChatResponse(
            message=f"Chat and {messages_count} messages deleted successfully",
            deleted_chat_id=chat_id,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}")
