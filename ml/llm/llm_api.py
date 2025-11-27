"""
Модуль генерации вопросов и ответов
"""
import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse, Response
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from config import SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = FastAPI(title="LLM Service with Gemini")


# вынести в schemas
class GenerationRequest(BaseModel):
    context: str
    user_message: str


# Конфигурация Gemini API
# в.env файле GOOGLE_API_KEY="ВАШ_API_КЛЮЧ"
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite", system_instruction=SYSTEM_PROMPT,
)

    is_ready = True
    logging.info("Gemini model initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Gemini model: {e}")
    is_ready = False


@app.get("/health")
async def health_check():
    """Проверка доступности сервиса."""
    logging.info("[health_check] health check requested")
    if is_ready:
        return JSONResponse(status_code=200, content={"status": "ok"})
    # 503 — сервис ещё не готов (например, если не удалось инициализировать модель)
    return JSONResponse(status_code=503, content={"status": "loading"})


@app.post("/generate-question")
async def generate_question(request_data: GenerationRequest) -> Response:
    """
    Генерирует ответ, исходя из вопроса пользователя
    и контекста из векторной БД.
    """
    logging.info("[generate_question] starting question generation")

    # Формируем контент для пользователя, объединяя контекст и его вопрос
    user_content = f"""Контекст из статей:
{request_data.context}
---
Вопрос пользователя: {request_data.user_message}

Ответь на вопрос пользователя, используя информацию из
предоставленного контекста. Если информации недостаточно, укажи это.
В конце ответа обязательно перечисли все использованные источники."""

    # Настройки для генерации ответа
    generation_config = GenerationConfig(
        max_output_tokens=2048,
        temperature=0.7
    )

    try:
        response = model.generate_content(
            contents=[user_content],
            generation_config=generation_config
        )

        # Извлекаем сгенерированный текст из ответа
        generated_text = response.text
        logging.info("[generate_question] successfully generated response")
        return JSONResponse(content={"generated_text": generated_text})

    except Exception as e:
        logging.exception("[generate_question] generation failed: %s", e)
        return JSONResponse(status_code=500, content={"error": f"An error occurred during generation: {str(e)}"})

# uvicorn llm:app --host 0.0.0.0 --port 5005 --reload