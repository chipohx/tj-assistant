from functools import lru_cache
from typing import Union
from langchain_core.language_models import BaseChatModel
from langchain_gigachat.chat_models import GigaChat
from langchain_openai import ChatOpenAI
from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    """
    Фабрика для создания инстанса ЛЛМ
    Сейчас поддержвает GigaChat and OpenRouter providers.
    
    Returns:
        BaseChatModel: Initialized LLM instance
    
    Raises:
        ValueError: If unsupported LLM provider is specified
    """
    settings = get_settings()
    provider = settings.llm_provider.lower()
    
    if provider == "gigachat":
        return _get_gigachat_llm()
    elif provider == "openrouter":
        return _get_openrouter_llm()
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: gigachat, openrouter"
        )


def _get_gigachat_llm() -> GigaChat:
    """Initialize GigaChat LLM."""
    settings = get_settings()
    return GigaChat(
        credentials=settings.gigachat_auth_key,
        model="GigaChat",
        verify_ssl_certs=False,
    )


def _get_openrouter_llm() -> ChatOpenAI:
    """Initialize OpenRouter LLM (OpenAI-compatible API)."""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openrouter_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=2000,
    )
