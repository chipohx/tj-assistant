"""
Модуль генерации вопросов и ответов
"""

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse, Response
import logging
import time

# import tqdm
from dotenv import load_dotenv
from llama_cpp import Llama
from config import SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = FastAPI(title="LLM Service with Gemini")

is_ready = False

llm = Llama.from_pretrained(
    repo_id="unsloth/Qwen3-4B-Instruct-2507-GGUF",
    filename="Qwen3-4B-Instruct-2507-IQ4_XS.gguf",
    # repo_id="Qwen/Qwen3-0.6B-GGUF",
    # filename="Qwen3-0.6B-Q8_0.gguf",
    set_prefix_caching=True,
    n_gpu_layers=22,
    n_threads=4,
    n_ctx=1024,
    n_batch=512,
)

is_ready = True


# вынести в schemas
class GenerationRequest(BaseModel):
    context: str
    user_message: str


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
    logging.info("[generate_question] starting question generation")
    logging.info(
        f"[generate_question] user message: {request_data.user_message[:100]}..."
    )

    user_content = f"""Контекст: {request_data.context}

Вопрос: {request_data.user_message}

Ответь на вопрос, используя только предоставленный контекст"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    try:
        start_time = time.time()
        logging.info(
            "[generate_question] sending to local llm model (CPU inference, may take 1-2 minutes)..."
        )
        response = llm.create_chat_completion(
            messages=messages,
            stream=False,
            max_tokens=128,
            temperature=0.5,
        )
        generation_time = time.time() - start_time

        # generated_text = ""
        # for chunk in tqdm(response, desc="Generating"):
        #     if 'content' in chunk['choices'][0]['delta']:
        #         generated_text += chunk['choices'][0]['delta']['content']

        # Извлекаем сгенерированный текст из ответа
        generated_text = response["choices"][0]["message"]["content"]
        logging.info(
            f"[generate_question] successfully generated response in {generation_time:.2f}s"
        )
        logging.info(
            f"[generate_question] response length: {len(generated_text)} chars"
        )
        return JSONResponse(content={"generated_text": generated_text})

    except Exception as e:
        logging.exception("[generate_question] generation failed: %s", e)
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred during generation: {str(e)}"},
        )


# uvicorn llm:app --host 0.0.0.0 --port 5005 --reload
