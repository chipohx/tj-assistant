from datetime import datetime

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.schemas.schemas import ChatRequest, ChatResponse, SessionListResponse

router = APIRouter()


# TODO Добавить Depends на авторизацию
@router.post("/chat")
async def send_message(
    message: ChatRequest, db: Session = Depends(get_db)
) -> ChatResponse:
    """Принимает запрос и возвращает ответ"""

    return ChatResponse(message_id=1, content=message.content, timestamp=datetime.now())


# TODO стриминг ответа (WebSocket)


# TODO Добавить Depends на авторизацию
@router.get("/chat", response_model=SessionListResponse)
async def get_chat_sessions(db: Session = Depends(get_db)):
    """Возвращает все чаты(сессии) пользователя"""

    return ""
