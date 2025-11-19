"""
Веткторизующая модель
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer
import logging
from config import (
    EMBEDDING_MODEL_NAME,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title='эмбеддинг модель для запросов')

embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cpu')
logging.info(f"Модель для встраиваний '{EMBEDDING_MODEL_NAME}' успешно загружена.")


@app.get("/health")
async def health_check():
    """
    Health check endpoint для проверки готовности сервиса
    """
    try:
        # Проверяем, что модель может выполнить простой encode
        test_embedding = embedding_model.encode("test", normalize_embeddings=True)
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "model_name": EMBEDDING_MODEL_NAME}
        )
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": str(e)}
        )


@app.post("/get")
async def encode(message: str):
    """
    Преобразует сообщение юзера в вектор
    """
    message_embedding = embedding_model.encode(message).tolist()
    return message_embedding

# uvicorn embedding_model.embedding_model:app --host 0.0.0.0 --port 5003 --reload
