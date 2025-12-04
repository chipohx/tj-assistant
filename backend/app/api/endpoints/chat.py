from typing import Annotated
from datetime import datetime
from uuid import UUID
import httpx

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.core.user import get_current_active_user, get_user
from app.models.models import Message, Role, Chat, User
from app.database.session import get_db
from app.api.schemas.schemas import (
    ChatRequest,
    ChatResponse,
    SessionListResponse,
    UserSchema,
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


def create_chat(db: Session, title: str, username: str):
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
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
    username: Annotated[UserSchema, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    create_chat(db, title="Новый чат", username=username)


@router.post("/chat")
async def send_message(
    request: ChatRequest,
    username: Annotated[UserSchema, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> ChatResponse:

    if not request.chat_id:
        chat_created = create_chat(db, request.content[:30], username)

    create_message_in_db(db, request.content, Role.USER, request.chat_id)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8001/llm_response",
                json={"query": request.content},
                timeout=10.0,
            )
        except httpx.RequestError as e:
            print(f"Ошибка сети: {e}")
            raise HTTPException(status_code=500, detail="LLM service unreachable")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed generating response")

    try:
        response_dict = response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Invalid JSON from LLM service")

    response_content = response_dict["response"]

    if response_content:
        message_id = create_message_in_db(
            db, response_content, request.chat_id, Role.SYSTEM
        )

        return ChatResponse(
            message_id=message_id,
            content=response_content,
            timestamp=datetime.now(),
            chat_created=chat_created,
        )
    else:
        return {"detail": "empty response"}


# TODO стриминг ответа (WebSocket)


# TODO Добавить Depends на авторизацию
@router.get("/chat", response_model=SessionListResponse)
async def get_chat_sessions(db: Session = Depends(get_db)):
    """Возвращает все чаты(сессии) пользователя"""

    return ""
