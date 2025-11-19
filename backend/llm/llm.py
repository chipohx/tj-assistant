"""
Модуль генерации вопросов и ответов
"""
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse, Response
from llama_cpp import Llama
import os
import logging
from dotenv import load_dotenv
import time
from config import (
    REPO_ID,
    MODEL_FILENAME,
    N_GPU_LAYERS,
)

logging.basicConfig(level=logging.INFO)
load_dotenv()
app = FastAPI(title="ллм")

# Флаг готовности модели: False, пока загрузка не завершилась
is_ready = False


class GenerationRequest(BaseModel):
    context: str
    user_message: str


def _load_model() -> None:
    """
    Загружает модель
    """
    global llm, is_ready
    logging.info("[question_model] loading model")
    try:
        start_time = time.time()
        llm = Llama.from_pretrained(
            repo_id=REPO_ID,
            filename=MODEL_FILENAME,
            set_prefix_caching=True,
            n_threads=4,
            # n_gpu_layers=N_GPU_LAYERS,
            n_ctx=2048,
            verbose=True,
            token=os.getenv("HF_TOKEN")
        )

        is_ready = True
        load_time = time.time() - start_time
        logging.info(
            f"[question_model] model loaded in {load_time:.1f} seconds"
        )
    except Exception as e:
        logging.exception("[question_model] failed to load model: %s", e)


# Запускаем загрузку в фоне при старте приложения
_load_model()
logging.info("[question_model] model loaded")


@app.get("/health")
async def health_check():
    logging.info("[question_model] health check")
    if is_ready:
        return JSONResponse(status_code=200, content={"status": "ok"})
    # 503 — сервис ещё не готов
    return JSONResponse(status_code=503, content={"status": "loading"})


@app.post("/generate-question")
async def generate_question(request_data: GenerationRequest) -> Response:
    """
    Генерирует ответ(вопрос), исходя из вопроса юзера
    и контекста из векторной БД
    """
    logging.info("[question_model] generate question")

    SYSTEM_PROMPT = """Ты — полезный ассистент Тинькофф Журнала (Т-Ж).
Твоя задача — давать точные, полезные и структурированные ответы на
вопросы пользователей, основываясь исключительно на предоставленном
контексте из статей.

Правила работы:
1. Используй только информацию из предоставленного контекста.
   Не придумывай факты.
2. Если в контексте нет информации для ответа, честно скажи об этом.
3. Структурируй ответ: используй абзацы, списки и выделения для
   лучшей читаемости.
4. Будь точным и конкретным. Избегай общих фраз.
5. В конце ответа обязательно укажи все источники (source_url),
   которые ты использовал.

Формат указания источников:
Источники:
- [название статьи или URL]
- [название статьи или URL]"""

    def build_messages() -> list[dict]:
        """
        Формирует сообщения для LLM с системным промптом
        и пользовательским запросом
        """
        user_content = f"""Контекст из статей:

{request_data.context}

---

Вопрос пользователя: {request_data.user_message}

Ответь на вопрос пользователя, используя информацию из
предоставленного контекста. Если информации недостаточно, укажи это.
В конце ответа обязательно перечисли все использованные источники."""

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    messages = build_messages()

    max_tokens = 512
    temperature = 0.7

    try:
        output = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
        )
    except ValueError as e:
        logging.exception("[question_model] generation failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

    logging.info(f" sending question: {output}")
    return JSONResponse(content=output)

# uvicorn llm.llm:app --host 0.0.0.0 --port 5005 --reload
