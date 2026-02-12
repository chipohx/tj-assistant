"""
Модуль конфигурации сервиса.

Содержит датакласс Settings с настройками приложения
и фабричную функцию get_settings() для получения экземпляра конфигурации.
Все параметры читаются из переменных окружения с разумными значениями по умолчанию.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """
    Неизменяемый датакласс с настройками сервиса.

    Attributes:
        gigachat_auth_key: Ключ авторизации GigaChat API (base64-encoded credentials).
        gigachat_model: Название модели GigaChat (GigaChat, GigaChat-Pro, GigaChat-Max).
        gigachat_temperature: Температура генерации (0.0 — детерминированно, 1.0 — максимально творчески).
        gigachat_max_tokens: Максимальное количество токенов в ответе модели.
        qdrant_url: URL для подключения к серверу Qdrant.
        collection_name: Имя коллекции в Qdrant.
        embedding_model_name: Название модели эмбеддингов из HuggingFace.
        eval_golden_path: Путь к файлу с эталонным набором данных для оценки.
        eval_runs_dir: Директория для хранения результатов запусков оценки.
        agent_max_iterations: Максимальное число итераций агентного цикла.
        retrieval_top_k: Количество документов, возвращаемых при поиске по умолчанию.
        retrieval_fetch_k_multiplier: Множитель для fetch_k в MMR-поиске (fetch_k = top_k * multiplier).
    """

    # GigaChat
    gigachat_auth_key: str
    gigachat_model: str
    gigachat_temperature: float
    gigachat_max_tokens: int

    # Qdrant
    qdrant_url: str
    collection_name: str

    # Embeddings
    embedding_model_name: str

    # Evaluation
    eval_golden_path: str
    eval_runs_dir: str

    # Agent
    agent_max_iterations: int
    retrieval_top_k: int
    retrieval_fetch_k_multiplier: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Фабричная функция для получения настроек сервиса.

    Читает переменные окружения и возвращает заполненный объект Settings.
    Результат кешируется — повторные вызовы возвращают тот же объект.

    Returns:
        Settings: Объект с настройками сервиса.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    storage_dir = os.path.join(base_dir, "storage", "eval_runs")

    return Settings(
        # GigaChat
        gigachat_auth_key=os.getenv("GIGACHAT_AUTH_KEY", ""),
        gigachat_model=os.getenv("GIGACHAT_MODEL", "GigaChat-Pro"),
        gigachat_temperature=float(os.getenv("GIGACHAT_TEMPERATURE", "0.3")),
        gigachat_max_tokens=int(os.getenv("GIGACHAT_MAX_TOKENS", "2048")),
        # Qdrant
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        collection_name=os.getenv("QDRANT_COLLECTION", "tj"),
        # Embeddings
        embedding_model_name=os.getenv(
            "EMBEDDING_MODEL_NAME",
            "intfloat/multilingual-e5-large",
        ),
        # Evaluation
        eval_golden_path=os.getenv(
            "EVAL_GOLDEN_PATH",
            os.path.join(data_dir, "eval_golden.json"),
        ),
        eval_runs_dir=os.getenv(
            "EVAL_RUNS_DIR",
            storage_dir,
        ),
        # Agent
        agent_max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "4")),
        retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5")),
        retrieval_fetch_k_multiplier=int(os.getenv("RETRIEVAL_FETCH_K_MULTIPLIER", "3")),
    )
