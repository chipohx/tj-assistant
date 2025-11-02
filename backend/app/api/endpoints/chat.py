from datetime import datetime

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.schemas.schemas import ChatRequest, ChatResponse

router = APIRouter()


# TODO Добавить Depends на авторизацию
@router.post("/chat")
async def send_message(
    message: ChatRequest, db: Session = Depends(get_db)
) -> ChatResponse:

    return ChatResponse(message_id=1, content=message.content, timestamp=datetime.now())


@router.get("/chat")
async def load_chat():
    return ""
