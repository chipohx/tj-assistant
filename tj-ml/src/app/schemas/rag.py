"""
Pydantic-схемы для RAG-эндпоинтов.

Определяет модели запроса и ответа для основного endpoint /rag/query,
а также вспомогательные модели для источников и сообщений.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """
    Сообщение из истории чата.

    Используется для передачи контекста предыдущей беседы,
    чтобы модель могла учитывать историю диалога при генерации ответа.

    Attributes:
        role: Роль отправителя — 'user' (пользователь) или 'assistant' (ассистент).
        content: Текстовое содержимое сообщения.
    """

    role: str = Field(..., description="Роль: 'user' или 'assistant'")
    content: str = Field(..., description="Содержимое сообщения")


class RAGQueryRequest(BaseModel):
    """
    Запрос к RAG-пайплайну.

    Attributes:
        question: Вопрос пользователя (минимум 1 символ).
        top_k: Количество документов для контекста (от 1 до 20, по умолчанию 5).
        chat_history: Необязательная история чата для поддержки многоходовых диалогов.
    """

    question: str = Field(..., min_length=1, description="Вопрос пользователя")
    top_k: int = Field(5, ge=1, le=20, description="Количество документов для контекста")
    chat_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="История чата для многоходового диалога (опционально)",
    )


class SourceDocument(BaseModel):
    """
    Документ-источник, найденный в базе знаний.

    Attributes:
        content: Текстовое содержимое фрагмента документа.
        metadata: Метаданные документа (source_url, article_title и др.).
    """

    content: str = Field(..., description="Текст фрагмента")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Метаданные: source_url, article_title и др.",
    )


class RAGQueryResponse(BaseModel):
    """
    Ответ RAG-пайплайна.

    Поле `answer` является обязательным и используется бэкендом.
    Остальные поля предоставляют дополнительную информацию для отладки и аналитики.

    Attributes:
        answer: Сгенерированный ответ модели (основное поле для бэкенда).
        context: Отформатированный контекст из базы знаний, переданный модели.
        sources: Список документов-источников с метаданными.
        token_usage: Детальная статистика использования токенов.
        agent_iterations: Количество итераций агентного цикла (0 = прямой RAG без агента).
    """

    answer: str = Field(..., description="Сгенерированный ответ модели")
    context: str = Field(default="", description="Контекст из базы знаний")
    sources: List[SourceDocument] = Field(
        default_factory=list,
        description="Документы-источники",
    )
    token_usage: Dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Детальная статистика использования токенов:\n"
            "- query_tokens: токены из запроса пользователя\n"
            "- context_tokens: токены из контекста RAG\n"
            "- prompt_tokens: общие входные токены\n"
            "- completion_tokens: токены ответа модели\n"
            "- total_tokens: общее количество токенов\n"
            "- successful_requests: количество успешных запросов к LLM"
        ),
    )
    agent_iterations: int = Field(
        default=0,
        description="Количество итераций агентного цикла",
    )


class RAGErrorResponse(BaseModel):
    """
    Ответ с ошибкой.

    Attributes:
        detail: Описание ошибки.
    """

    detail: str = Field(..., description="Описание ошибки")
