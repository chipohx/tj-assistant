"""
Веткторизующая модель
"""
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import logging
from .config import (
    EMBEDDING_MODEL_NAME,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title='эмбеддинг модель для запросов')

embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cpu')
logging.info(f"Модель для встраиваний '{EMBEDDING_MODEL_NAME}' успешно загружена.")


@app.post("/get")
async def encode(message: str):
    """
    Преобразует сообщение юзера в вектор
    """
    message_embedding = embedding_model.encode(message).tolist()
    return message_embedding

# uvicorn embedding_model.embedding_model:app --host 0.0.0.0 --port 5003 --reload
