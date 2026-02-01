from functools import lru_cache
from langchain_qdrant import QdrantVectorStore
from app.core.config import get_settings
from app.services.embeddings import get_embeddings


@lru_cache(maxsize=1)
def get_vector_store() -> QdrantVectorStore:
    settings = get_settings()
    embeddings = get_embeddings()
    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url=settings.qdrant_url,
        collection_name=settings.collection_name,
    )
