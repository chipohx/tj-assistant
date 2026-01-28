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


# def create_message_in_db(db: Session, content: str, role: Role, chat_id: UUID) -> UUID:
#     try:
#         new_message = Message(chat_id=chat_id, content=content, role=role)
#         db.add(new_message)
#         db.commit()
#         db.refresh(new_message)
#         return new_message.id
#     except Exception as e:
#         print(f"Error: {e}")
#         raise HTTPException(status_code=500, detail="Failed to create message")


# def create_chat(db: Session, title: str, user: User):
#     try:
#         new_chat = Chat(title=title, user_id=user.id)
#         db.add(new_chat)
#         db.commit()
#         db.refresh(new_chat)
#         return new_chat.id
#     except Exception as e:
#         print(f"Error: {e}")
#         raise HTTPException(status_code=500, detail="Failed to create chat")
        
        
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
        try:
          chat_created = await create_chat(db, request.content[:30], user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create chat: {str(e)}")
        chat_id = chat_created
    else:
        chat_id = request.chat_id

    try:
        await create_message(db, request.content, Role.USER, chat_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save user message: {str(e)}")

    #response_content = await request_llm_response(request.content)
    
    response_content = f"Это тестовый ответ от ассистента на ваш запрос: '{request.content}'. ML-сервис находится в разработке и будет подключен позже."
    
    if response_content:
        await create_message(db, response_content, Role.SYSTEM, chat_id)

        return ChatResponse(
            content=response_content,
            timestamp=datetime.now(),
            chat_created=chat_id,
        )
    else:
        raise HTTPException(status_code=502, detail="Empty response from LLM service")

    try:
        assistant_message_id = create_message_in_db(db, response_content, Role.SYSTEM, chat_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save assistant message: {str(e)}")

    return ChatResponse(
        message_id=assistant_message_id,
        content=response_content,
        timestamp=datetime.now(),
        chat_created=chat_created,
    )


@router.get("/chats")
async def get_chats(
    user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    try:
        chats = (await db.scalars(
            Select(Chat)
            .filter(Chat.user_id == user.id)
            .options(defer(Chat.user_id))
            .order_by(Chat.created.asc())
        ).all()

        return {
            "items": [
                {
                    "id": str(chat.id),
                    "title": chat.title,
                    "created": chat.created,
                    "updated": chat.updated
                }
                for chat in chats
            ],
            "count": len(chats)
        }
    except Exception as e:
        print(f"Ошибка при попытке получить чаты: {e}")
        raise HTTPException(status_code=500, detail="Server error")


# @router.get("/chat/{chat_id}/messages", response_model=MessagesListResponse)
# async def get_chat_sessions(
#     chat_id: UUID,
#     user: Annotated[User, Depends(get_current_active_user)],
#     db: AsyncSession = Depends(get_db),
#     limit: int = Query(20, ge=1, le=30),
#     last_id: UUID | None = None,
# ):
#     try:
#         chat: Chat = await db.scalar(Select(Chat).filter(Chat.id == chat_id))

#         if not chat:
#             raise HTTPException(status_code=404, detail="Chat not found")
#         if chat.user_id != user.id:
#             raise HTTPException(status_code=403, detail="Access forbidden")

#         # Базовый запрос
#         query = await Select(Message).filter(Message.chat_id == chat_id).order_by(Message.created.asc())

#         # Если указан last_id, получаем сообщения после него
#         if last_id:
#             last_message = await db.scalar(Select(Message).filter(Message.id == last_id))
#             if last_message:
#                 query = query.filter(Message.created > last_message.created)

#         # Применяем лимит
#         query = query.limit(limit)

#         db_messages = db.scalars(query).all()

#         response_data = {
#             "count": len(db_messages),
#             "next_id": db_messages[-1].id if db_messages else None,
#             "items": [
#                 {
#                     "id": str(msg.id),
#                     "content": msg.content,
#                     "created": msg.created,
#                     "role": msg.role.value
#                 }
#                 for msg in db_messages
#             ],
#         }

#         return MessagesListResponse[MessageSchema].model_validate(response_data)
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Ошибка при получении сообщений: {e}")
#         raise HTTPException(status_code=500, detail="Server error")
