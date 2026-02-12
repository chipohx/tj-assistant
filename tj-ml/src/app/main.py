"""
Точка входа FastAPI-приложения TJ-Assistant ML.

Определяет HTTP-эндпоинты:
- POST /rag/query — основной RAG-запрос с агентными возможностями
- POST /eval/run — запуск оценки качества
- GET /eval/status — статус запуска оценки
- GET /eval/report — отчёт по оценке
- GET /health — проверка здоровья сервиса
"""

from fastapi import BackgroundTasks, FastAPI, HTTPException

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.schemas.eval import EvalReport, EvalRunRequest, EvalRunResponse, EvalStatusResponse
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, SourceDocument
from app.services.agent import process_query
from app.services.embeddings import get_embeddings
from app.services.eval_pipeline import create_run, read_run, run_evaluation
from app.services.llm import get_llm
from app.services.vector_store import get_vector_store


logger = get_logger(__name__)

app = FastAPI(
    title="TJ-Assistant ML API",
    description="RAG-сервис с агентными возможностями для базы знаний Тинькофф Журнала",
    version="2.0.0",
)


@app.on_event("startup")
def _startup() -> None:
    """
    Инициализация компонентов при запуске сервиса.

    Загружает и кеширует: модель эмбеддингов, подключение к Qdrant, LLM GigaChat.
    """
    configure_logging()
    settings = get_settings()

    logger.info("=" * 60)
    logger.info("Инициализация TJ-Assistant ML v2.0.0")
    logger.info("=" * 60)
    logger.info("GigaChat модель: %s", settings.gigachat_model)
    logger.info("Модель эмбеддингов: %s", settings.embedding_model_name)
    logger.info("Qdrant: %s / коллекция: %s", settings.qdrant_url, settings.collection_name)
    logger.info("Агент: max_iterations=%d", settings.agent_max_iterations)

    get_embeddings()
    get_vector_store()
    get_llm()

    logger.info("Инициализация завершена.")


@app.post("/rag/query", response_model=RAGQueryResponse)
def rag_query(payload: RAGQueryRequest) -> RAGQueryResponse:
    """
    Обработка RAG-запроса с агентными возможностями.

    Принимает вопрос пользователя, выполняет поиск по базе знаний,
    при необходимости вызывает инструменты (дополнительный поиск,
    вычисления) и генерирует развёрнутый ответ.

    Args:
        payload: Тело запроса с полями question, top_k, chat_history.

    Returns:
        RAGQueryResponse: Ответ с полями answer, context, sources,
                          token_usage, agent_iterations.
    """
    # Преобразуем chat_history из Pydantic-моделей в словари
    chat_history = None
    if payload.chat_history:
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in payload.chat_history
        ]

    result = process_query(
        question=payload.question,
        top_k=payload.top_k,
        chat_history=chat_history,
    )

    sources = [
        SourceDocument(content=doc.page_content, metadata=doc.metadata or {})
        for doc in result.docs
    ]

    return RAGQueryResponse(
        answer=result.answer,
        context=result.context,
        sources=sources,
        token_usage=result.token_usage,
        agent_iterations=result.iterations,
    )


@app.post("/eval/run", response_model=EvalRunResponse)
def eval_run(
    payload: EvalRunRequest, background_tasks: BackgroundTasks
) -> EvalRunResponse:
    """
    Запуск фоновой оценки качества RAG-пайплайна.

    Создаёт новый запуск оценки и добавляет задачу в фоновую очередь.

    Args:
        payload: Тело запроса с необязательным именем запуска.
        background_tasks: Менеджер фоновых задач FastAPI.

    Returns:
        EvalRunResponse: UUID запуска и статус 'running'.
    """
    run_id = create_run(payload.run_name)
    background_tasks.add_task(run_evaluation, run_id)
    return EvalRunResponse(run_id=run_id, status="running")


@app.get("/eval/status", response_model=EvalStatusResponse)
def eval_status(run_id: str) -> EvalStatusResponse:
    """
    Получить статус запуска оценки.

    Args:
        run_id: UUID запуска.

    Returns:
        EvalStatusResponse: Текущий статус (running/completed/failed).

    Raises:
        HTTPException(404): Если запуск не найден.
    """
    try:
        run_data = read_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvalStatusResponse(
        run_id=run_data["run_id"],
        status=run_data["status"],
        started_at=run_data.get("started_at"),
        finished_at=run_data.get("finished_at"),
        error=run_data.get("error"),
    )


@app.get("/eval/report", response_model=EvalReport)
def eval_report(run_id: str) -> EvalReport:
    """
    Получить полный отчёт по запуску оценки.

    Args:
        run_id: UUID запуска.

    Returns:
        EvalReport: Метрики и детальные результаты по каждому вопросу.

    Raises:
        HTTPException(404): Если запуск не найден.
    """
    try:
        run_data = read_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvalReport(
        run_id=run_data["run_id"],
        status=run_data["status"],
        metrics=run_data.get("metrics", {}),
        items=run_data.get("items", []),
    )


@app.get("/health")
def health_check() -> dict:
    """
    Проверка здоровья сервиса.

    Используется Docker healthcheck и балансировщиками нагрузки.

    Returns:
        dict: {"status": "healthy"}.
    """
    return {"status": "healthy"}
