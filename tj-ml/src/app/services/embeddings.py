"""
Модуль инициализации модели эмбеддингов.

Предоставляет функцию get_embeddings() для получения
кешированного экземпляра модели HuggingFace для создания векторных представлений текста.
Модель используется как при индексации документов, так и при поиске.
"""

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import get_settings
from app.core.logging import get_logger


logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Создать и закешировать экземпляр модели эмбеддингов HuggingFace.

    Имя модели берётся из конфигурации (EMBEDDING_MODEL_NAME).
    По умолчанию используется intfloat/multilingual-e5-large —
    многоязычная модель с хорошей поддержкой русского языка.

    Returns:
        HuggingFaceEmbeddings: Инициализированная модель эмбеддингов.
    """
    settings = get_settings()
    logger.info("Загрузка модели эмбеддингов: %s", settings.embedding_model_name)
    return HuggingFaceEmbeddings(model_name=settings.embedding_model_name)
