from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

client = QdrantClient(url="http://localhost:6333")

# Создаём коллекцию, если её нет (384 = длина эмбеддинга all-MiniLM-L6-v2)
client.recreate_collection(
    collection_name="articles"
)
