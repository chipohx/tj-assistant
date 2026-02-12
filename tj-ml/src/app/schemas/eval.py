"""
Pydantic-схемы для эндпоинтов оценки (evaluation).

Определяет модели для запуска, отслеживания статуса
и получения отчётов по оценке качества RAG-пайплайна.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GoldenItem(BaseModel):
    """
    Элемент эталонного набора данных для оценки.

    Attributes:
        question: Вопрос, на который модель должна ответить.
        answer: Эталонный (правильный) ответ.
        reference_context: Необязательный эталонный контекст для сравнения.
    """

    question: str = Field(..., description="Вопрос для оценки")
    answer: str = Field(..., description="Эталонный ответ")
    reference_context: Optional[str] = Field(
        default=None,
        description="Эталонный контекст для сравнения",
    )


class EvalRunRequest(BaseModel):
    """
    Запрос на запуск оценки.

    Attributes:
        run_name: Необязательное имя запуска для удобства идентификации.
    """

    run_name: Optional[str] = Field(
        default=None,
        description="Имя запуска оценки",
    )


class EvalRunResponse(BaseModel):
    """
    Ответ при создании запуска оценки.

    Attributes:
        run_id: Уникальный идентификатор запуска (UUID).
        status: Текущий статус запуска ('running').
    """

    run_id: str = Field(..., description="UUID запуска")
    status: str = Field(..., description="Статус: 'running'")


class EvalStatusResponse(BaseModel):
    """
    Статус запуска оценки.

    Attributes:
        run_id: Уникальный идентификатор запуска.
        status: Текущий статус ('running', 'completed', 'failed').
        started_at: Время начала в формате ISO 8601.
        finished_at: Время окончания в формате ISO 8601 (None если ещё выполняется).
        error: Описание ошибки (None если без ошибок).
    """

    run_id: str
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None


class EvalItemResult(BaseModel):
    """
    Результат оценки одного вопроса.

    Attributes:
        question: Вопрос из эталонного набора.
        expected_answer: Ожидаемый (эталонный) ответ.
        predicted_answer: Ответ модели.
        exact_match: Метрика точного совпадения (0.0 или 1.0).
        f1: Метрика F1-score по токенам (0.0 — 1.0).
    """

    question: str
    expected_answer: str
    predicted_answer: str
    exact_match: float
    f1: float


class EvalReport(BaseModel):
    """
    Полный отчёт по запуску оценки.

    Attributes:
        run_id: Уникальный идентификатор запуска.
        status: Текущий статус запуска.
        metrics: Агрегированные метрики (count, exact_match_avg, f1_avg).
        items: Детальные результаты по каждому вопросу.
    """

    run_id: str
    status: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    items: List[EvalItemResult] = Field(default_factory=list)
