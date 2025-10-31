"""
Пример добавления статьи в векторную бд
"""

from backend.app.utils.embeddings import SentenceTransformerEmbedder
from chroma_store import ChromaStore

embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2", normalize=True, device='cpu')
store = ChromaStore(
    collection_name="test_col", embedder=embedder, persist_directory="./chroma_db"
)

store.add(
    ids=["1", "2"],
    documents=["Это первый документ", "Второй документ про python"],
    metadatas=[{"title": "doc1"}, {"title": "doc2"}],
)

print("Search results:", store.search("python", k=2))
store.persist()
