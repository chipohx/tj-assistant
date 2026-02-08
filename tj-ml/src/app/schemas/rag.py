from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=20)


class SourceDocument(BaseModel):
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGQueryResponse(BaseModel):
    answer: str
    context: str
    sources: List[SourceDocument]
    token_usage: Dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Детальная статистика использования токенов:\n"
            "- query_tokens: токены из запроса пользователя\n"
            "- context_tokens: токены из контекста RAG (векторная БД)\n"
            "- prompt_tokens: общие входные токены (query + context + промпт)\n"
            "- completion_tokens: токены ответа модели\n"
            "- total_tokens: общее количество токенов\n"
            "- successful_requests: количество успешных запросов"
        )
    )


class RAGErrorResponse(BaseModel):
    detail: str
