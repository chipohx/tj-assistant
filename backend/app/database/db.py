from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import Message, User, Chat
from app.api.schemas.schemas import Role


def create_message(db: Session, content: str, role: Role, chat_id: UUID) -> UUID:
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
