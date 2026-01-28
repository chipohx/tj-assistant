from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession\
from fastapi import HTTPException

from app.models.models import Message, User, Chat
from app.api.schemas.schemas import Role


async def create_message(
    db: AsyncSession, content: str, role: Role, chat_id: UUID
) -> UUID:
    try:
        new_message = Message(chat_id=chat_id, content=content, role=role)
        db.add(new_message)
        await db.commit()
        await db.refresh(new_message)
        return await new_message.awaitable_attrs.id
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save message")


async def create_chat(db: AsyncSession, title: str, user: User) -> UUID:
    try:
        new_chat = Chat(title=title, user_id=user.id)
        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)
        return new_chat.awaitable_attrs.id
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create chat")
