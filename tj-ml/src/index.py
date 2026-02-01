import json
import os
import time
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse


# Загружаем переменные окружения из .env файла
load_dotenv()

# URL для подключения к Qdrant (по умолчанию локальный)
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
COLLECTION_NAME = os.getenv('QDRANT_COLLECTION', 'tj')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')


def load_articles_from_json(file_path):
    """
    Загружает статьи из JSON файла и преобразует их в список объектов Document.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = []
    for item in data:
        # Извлекаем текст и метаданные
        doc = Document(
            page_content=item.get('document', ''),
            metadata=item.get('metadata', {})
        )
        documents.append(doc)
    return documents


def wait_for_qdrant(url: str, max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for Qdrant to be ready."""
    client = QdrantClient(url=url)
    for i in range(max_retries):
        try:
            client.get_collections()
            print(f"Qdrant доступен на {url}")
            return True
        except Exception as e:
            print(f"Ожидание Qdrant ({i+1}/{max_retries})... {e}")
            time.sleep(delay)
    return False


def check_collection_exists(url: str, collection_name: str) -> bool:
    """Check if collection already exists and has data."""
    try:
        client = QdrantClient(url=url)
        collection_info = client.get_collection(collection_name)
        if collection_info.points_count > 0:
            print(f"Коллекция '{collection_name}' уже существует с {collection_info.points_count} документами")
            return True
    except UnexpectedResponse:
        pass
    except Exception as e:
        print(f"Ошибка при проверке коллекции: {e}")
    return False


def main():
    print(f"Загрузка модели эмбеддингов {EMBEDDING_MODEL}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    articles_path = os.path.join(current_dir, 'data', 'articles.json')

    print(f"Читаем данные из: {articles_path}")

    # Wait for Qdrant to be ready
    if not wait_for_qdrant(QDRANT_URL):
        print("Ошибка: Qdrant не доступен")
        return

    # Check if already indexed
    if check_collection_exists(QDRANT_URL, COLLECTION_NAME):
        print("Индексация пропущена - данные уже загружены")
        return

    try:
        documents = load_articles_from_json(articles_path)
        print(f"Загружено фрагментов: {len(documents)}")

        print(f"Подключение к Qdrant ({QDRANT_URL}) и загрузка векторов...")

        QdrantVectorStore.from_documents(
            documents=documents,
            embedding=embeddings,
            url=QDRANT_URL,
            collection_name=COLLECTION_NAME,
            force_recreate=True
        )

        print(f"Успех! Данные загружены в коллекцию '{COLLECTION_NAME}'.")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        raise


if __name__ == "__main__":
    main()
