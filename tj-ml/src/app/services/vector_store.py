"""
Модуль работы с векторным хранилищем Qdrant.

Предоставляет функции для подключения к существующей коллекции Qdrant
и выполнения различных типов поиска:
- similarity_search — поиск по косинусному сходству
- mmr_search — поиск с максимальной маргинальной релевантностью (MMR)

MMR обеспечивает баланс между релевантностью и разнообразием результатов,
что улучшает качество контекста для RAG-пайплайна.
"""

from functools import lru_cache
from typing import List

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.embeddings import get_embeddings


logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_vector_store() -> QdrantVectorStore:
    """
    Создать и закешировать подключение к коллекции Qdrant.

    Подключается к уже существующей коллекции (не создаёт новую).
    Параметры подключения берутся из конфигурации.

    Returns:
        QdrantVectorStore: Подключённое хранилище для поиска.

    Raises:
        Exception: При ошибке подключения к Qdrant или отсутствии коллекции.
    """
    settings = get_settings()
    embeddings = get_embeddings()

    logger.info(
        "Подключение к Qdrant: url=%s, collection=%s",
        settings.qdrant_url,
        settings.collection_name,
    )

    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url=settings.qdrant_url,
        collection_name=settings.collection_name,
    )


def search_similar(query: str, top_k: int = 5) -> List[Document]:
    """
    Поиск по косинусному сходству (similarity search).

    Возвращает top_k наиболее похожих документов.

    Args:
        query: Поисковый запрос.
        top_k: Количество возвращаемых документов.

    Returns:
        List[Document]: Список найденных документов с метаданными.
    """
    store = get_vector_store()
    return store.similarity_search(query, k=top_k)


def search_mmr(query: str, top_k: int = 5, fetch_k: int | None = None) -> List[Document]:
    """
    Поиск с максимальной маргинальной релевантностью (MMR).

    MMR балансирует между релевантностью и разнообразием:
    сначала извлекает fetch_k кандидатов, затем из них выбирает top_k
    с максимальной релевантностью при минимальном дублировании информации.

    Это даёт более разнообразный контекст для модели и снижает
    вероятность получения нескольких фрагментов из одной статьи.

    Args:
        query: Поисковый запрос.
        top_k: Количество возвращаемых документов.
        fetch_k: Количество кандидатов для предварительной выборки.
                  Если None, используется top_k * multiplier из конфигурации.

    Returns:
        List[Document]: Список найденных документов с метаданными.
    """
    settings = get_settings()
    store = get_vector_store()

    if fetch_k is None:
        fetch_k = top_k * settings.retrieval_fetch_k_multiplier

    return store.max_marginal_relevance_search(
        query,
        k=top_k,
        fetch_k=fetch_k,
        lambda_mult=0.7,  # 0.0 = максимальное разнообразие, 1.0 = максимальная релевантность
    )
