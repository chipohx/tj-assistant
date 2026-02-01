from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    settings = get_settings()
    return HuggingFaceEmbeddings(model_name=settings.embedding_model_name)
