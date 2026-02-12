"""
Модуль инициализации языковой модели GigaChat.

Предоставляет фабричные функции для создания экземпляров LLM:
- get_llm() — основная модель для генерации ответов и агентного цикла.
- get_llm_for_tools() — модель с привязанными инструментами (tool calling).

Используется GigaChat API от Сбера. Поддерживаются модели:
GigaChat (базовая), GigaChat-Pro (рекомендуемая), GigaChat-Max (максимальная).
"""

from functools import lru_cache
from typing import List

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_gigachat.chat_models import GigaChat

from app.core.config import get_settings
from app.core.logging import get_logger


logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> GigaChat:
    """
    Создать и закешировать экземпляр GigaChat LLM.

    Параметры модели (model, temperature, max_tokens) берутся из конфигурации.
    SSL-верификация отключена для совместимости с корпоративными прокси.

    Returns:
        GigaChat: Инициализированный экземпляр языковой модели.

    Raises:
        Exception: При ошибке инициализации GigaChat (невалидный ключ и т.п.).
    """
    settings = get_settings()

    logger.info(
        "Инициализация GigaChat: model=%s, temperature=%.2f, max_tokens=%d",
        settings.gigachat_model,
        settings.gigachat_temperature,
        settings.gigachat_max_tokens,
    )

    return GigaChat(
        credentials=settings.gigachat_auth_key,
        model=settings.gigachat_model,
        temperature=settings.gigachat_temperature,
        max_tokens=settings.gigachat_max_tokens,
        verify_ssl_certs=False,
    )


def get_llm_with_tools(tools: List[BaseTool]) -> BaseChatModel:
    """
    Получить экземпляр LLM с привязанными инструментами для агентного цикла.

    Привязывает список LangChain-инструментов к модели через bind_tools().
    Это позволяет модели генерировать вызовы инструментов (function calling).

    Args:
        tools: Список инструментов LangChain (BaseTool), доступных модели.

    Returns:
        BaseChatModel: Модель GigaChat с привязанными инструментами.
    """
    llm = get_llm()
    return llm.bind_tools(tools)
