from functools import lru_cache
from langchain_gigachat.chat_models import GigaChat
from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_llm() -> GigaChat:
    settings = get_settings()
    return GigaChat(
        credentials=settings.gigachat_auth_key,
        model="GigaChat",
        verify_ssl_certs=False,
    )
