import requests
import json
import time
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TJ Assistant Main Service")

# URL сервисов из переменных окружения или значения по умолчанию
EMBEDDING_MODEL_BASE_URL = os.getenv("EMBEDDING_MODEL_URL", "http://localhost:5003")
VECTOR_DB_BASE_URL = os.getenv("VECTOR_DB_URL", "http://localhost:5004")
LLM_BASE_URL = os.getenv("LLM_URL", "http://localhost:5005")

EMBEDDING_MODEL_URL = f"{EMBEDDING_MODEL_BASE_URL}/get"
VECTOR_DB_URL = f"{VECTOR_DB_BASE_URL}/get_context"
LLM_URL = f"{LLM_BASE_URL}/generate-question"

EMBEDDING_MODEL_HEALTH_URL = f"{EMBEDDING_MODEL_BASE_URL}/health"
VECTOR_DB_HEALTH_URL = f"{VECTOR_DB_BASE_URL}/health"
LLM_HEALTH_URL = f"{LLM_BASE_URL}/health"


class QueryRequest(BaseModel):
    query: str


def check_service_health(service_name: str, health_url: str, timeout: int = 5) -> bool:
    """
    Проверяет готовность сервиса через health-check endpoint
    
    Args:
        service_name: Название сервиса для логирования
        health_url: URL health-check endpoint
        timeout: Таймаут запроса в секундах
    
    Returns:
        True если сервис готов, False иначе
    """
    try:
        response = requests.get(health_url, timeout=timeout)
        if response.status_code == 200:
            logger.info(f"✓ {service_name} is healthy")
            return True
        else:
            logger.warning(f"✗ {service_name} health check returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ {service_name} health check failed: {e}")
        return False


def check_all_services() -> dict:
    """
    Проверяет готовность всех зависимых сервисов
    
    Returns:
        Словарь с результатами проверки каждого сервиса
    """
    results = {
        "embedding_model": check_service_health("Embedding Model", EMBEDDING_MODEL_HEALTH_URL),
        "vector_db": check_service_health("Vector DB", VECTOR_DB_HEALTH_URL),
        "llm": check_service_health("LLM", LLM_HEALTH_URL),
    }
    return results


@app.get("/health")
async def health_check():
    """
    Health check endpoint для main сервиса.
    Проверяет готовность всех зависимых сервисов.
    """
    services_status = check_all_services()
    all_healthy = all(services_status.values())
    
    if all_healthy:
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "services": services_status}
        )
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "services": services_status}
        )


@app.post("/llm_response")
async def get_response_from_llm(request: QueryRequest):
    """
    Получает ответ от LLM на основе запроса пользователя.
    Перед обработкой проверяет готовность всех сервисов.
    """
    query = request.query
    
    # Проверка готовности всех сервисов перед обработкой
    services_status = check_all_services()
    if not all(services_status.values()):
        unavailable_services = [name for name, status in services_status.items() if not status]
        raise HTTPException(
            status_code=503,
            detail=f"Сервисы недоступны: {', '.join(unavailable_services)}"
        )
    
    try:
        # Шаг 1: Получение эмбеддинга запроса
        e5_start = time.time()
        embedding_response = requests.post(
            EMBEDDING_MODEL_URL,
            params={'message': query},
            timeout=30
        )
        embedding_response.raise_for_status()
        vectorized_query = embedding_response.json()
        e5_end = time.time() - e5_start
        logger.info(f"Embedding generation time: {e5_end:.2f}s")

        # Шаг 2: Поиск релевантного контекста в векторной БД
        chroma_start = time.time()
        context_response = requests.get(
            VECTOR_DB_URL,
            params={'message_embedding': json.dumps(vectorized_query), 'top_k': 3},
            timeout=30
        )
        context_response.raise_for_status()
        retrieved_data = context_response.json()
        chroma_end = time.time() - chroma_start
        logger.info(f"Vector DB search time: {chroma_end:.2f}s")

        # Шаг 3: Форматирование контекста
        if not retrieved_data:
            raise HTTPException(
                status_code=404,
                detail="Не найдено релевантного контекста для запроса"
            )

        formatted_context = ""
        for item in retrieved_data:
            formatted_context += f"Текст статьи:\n{item['document']}\n"
            formatted_context += f"Источник: {item['source_url']}\n\n"

        # Шаг 4: Генерация ответа через LLM
        llm_payload = {
            'context': formatted_context.strip(),
            'user_message': query
        }

        llm_start = time.time()
        llm_response = requests.post(
            LLM_URL,
            json=llm_payload,
            timeout=300
        )
        llm_response.raise_for_status()
        llm_output = llm_response.json()
        llm_end = time.time() - llm_start
        logger.info(f"LLM generation time: {llm_end:.2f}s")

        # Шаг 5: Обработка ответа от LLM
        if "generated_text" in llm_output:
            response_content = llm_output["generated_text"]
            return JSONResponse(
                status_code=200,
                content={
                    "response": response_content,
                    "timings": {
                        "embedding": round(e5_end, 2),
                        "vector_db": round(chroma_end, 2),
                        "llm": round(llm_end, 2),
                        "total": round(e5_end + chroma_end + llm_end, 2)
                    }
                }
            )
        else:
            logger.error(f"LLM response format error: {llm_output}")
            raise HTTPException(
                status_code=500,
                detail="Некорректный формат ответа от LLM: отсутствует ключ 'generated_text'"
            )

    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout: {e}")
        raise HTTPException(status_code=504, detail="Таймаут при обращении к сервису")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Ошибка при обращении к сервису: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

