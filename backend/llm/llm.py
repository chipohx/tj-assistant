from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse, Response
from llama_cpp import Llama
import os
import logging
from dotenv import load_dotenv
import time
from .config import (
    REPO_ID,
    MODEL_FILENAME,
)

logging.basicConfig(level=logging.INFO)
load_dotenv()
app = FastAPI(title="ллм")

# Флаг готовности модели: False, пока загрузка не завершилась
is_ready = False

class GenerationRequest(BaseModel):
    context: str
    user_message: str

def _load_model():
    global llm, is_ready
    logging.info("[question_model] loading model")
    try:
        start_time = time.time()
        llm = Llama.from_pretrained(
            repo_id=REPO_ID,
            filename=MODEL_FILENAME,
            set_prefix_caching=True,
            n_threads=1,
            n_ctx=1024,
            verbose=False,
            token=os.getenv("HF_TOKEN")
        )

        is_ready = True
        logging.info(f"[question_model] model loaded in {time.time() - start_time:.1f} seconds")
    except Exception as e:
        logging.exception("[question_model] failed to load model: %s", e)


# Запускаем загрузку в фоне при старте приложения
_load_model()
logging.info(f"[question_model] model loaded")


@app.get("/health")
async def health_check():
    logging.info(f"[question_model] health check")
    if is_ready:
        return {"status": "ok"}
    # 503 — сервис ещё не готов
    return JSONResponse(status_code=503, content={"status": "loading"})


@app.post("/generate-question")
async def generate_question(request_data: GenerationRequest):
    logging.info(f"[question_model] generate question")

    SYSTEM_PROMPT = """Ты — полезный ассистент Т-Ж. Твоя задача — ответить на вопрос пользователя,
    основываясь на предоставленном контексте. После ответа обязательно укажи источники (source_url), которые ты использовал, в формате:
    Источники:
    - [ссылка1]
    - [ссылка2]"""

    def build_messages() -> list[dict]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Контекст из статей:\n{request_data.context}\n\nСообщение пользователя: {request_data.user_message}\n\nОтветь на вопрос и укажи источники.",
            },
        ]

    messages = build_messages()

    max_tokens = 256
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
