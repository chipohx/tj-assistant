"""
Docstring
"""

from typing import List, Dict, Optional, Any
import chromadb


class ChromaStore:
    def __init__(
        self,
        collection_name: str,
        embedder,
        persist_directory: Optional[str] = None,
        embedding_dim: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.collection_name = collection_name
        self.embedder = embedder
        self.embedding_dim = embedding_dim

        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.EphemeralClient()

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata=metadata,
        )

    def add(
            self,
            ids: List[str],
            vectors: Optional[List[List[float]]] = None,
            documents: Optional[List[str]] = None,
            metadatas: Optional[List[Dict]] = None,
    ):
        """
        Добавляет записи в коллекцию. Можно передать готовые векторы или тексты (для которых будут вычислены эмбеддинги).
        :param ids: list of ids (strings)
        :param vectors: optional precomputed list of vectors
        :param documents: optional list of document texts
        :param metadatas: optional list of metadata dicts
        """
        if vectors is None:
            if documents is None:
                raise ValueError("Нужно передать либо vectors, либо documents.")
            # вычисляем эмбеддинги у embedder'а
            vectors = self.embedder.embed(documents)
        else:
            if self.embedding_dim:
                assert all(len(v) == self.embedding_dim for v in vectors), (
                    "Неверный размер векторов"
                )

        add_kwargs = {
            "ids": ids,
            "documents": documents if documents is not None else [None] * len(ids),
            "metadatas": metadatas if metadatas is not None else [{}] * len(ids),
            "embeddings": vectors,
        }
        self.collection.add(**add_kwargs)

    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Поиск похожих документов по текстовому запросу.
        Возвращает список dict: {'id','score','metadata','document'}
        """
        # получаем эмбеддинг для запроса
        qvecs = self.embedder.embed([query])
        qvec = qvecs[0]

        results = self.collection.query(
            query_embeddings=[qvec],
            n_results=k,
            include=["distances", "metadatas", "documents"],
        )

        hits = []
        # Формат results: dict с полями 'ids', 'distances', 'metadatas', 'documents' — каждый элемент список списков (по батчам)
        # Берём первый батч
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]

        # Чем меньше distance — тем ближе
        for idx, did in enumerate(ids):
            hits.append({
                "id": did,
                "score": distances[idx] if idx < len(distances) else None,
                "metadata": metadatas[idx] if idx < len(metadatas) else None,
                "document": documents[idx] if idx < len(documents) else None,
            })
        return hits

    def delete(self, ids: List[str]):
        """Удаляет документы по id"""
        self.collection.delete(ids=ids)

    def get(self, id: str) -> Optional[Dict]:
        """Возвращает документ по id"""
        res = self.collection.get(
            ids=[id], include=["documents", "metadatas", "embeddings"]
        )
        ids = res.get("ids", [[]])[0]
        if not ids:
            return None
        return {
            "id": ids[0],
            "document": res.get("documents", [[]])[0][0],
            "metadata": res.get("metadatas", [[]])[0][0],
            "embedding": res.get("embeddings", [[]])[0][0],
        }

    def persist(self):
        """
        Если Chroma настроен на персистентность, можно явно вызвать persist
        """
        try:
            self.client.persist()
        except Exception:
            pass

    def reset_collection(self):
        """
        Удаляет текущую коллекцию и создаёт занов
        """
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(name=self.collection_name)
