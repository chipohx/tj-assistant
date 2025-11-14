"""
Векторная база данных
"""
import logging
from pathlib import Path
import chromadb
from fastapi import FastAPI, Response
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="запросы на поиск в векторной бд")

current_dir = Path(__file__).parent.resolve()

CHROMA_DB_PATH = str(current_dir / "chroma_db")
COLLECTION_NAME = "articles_collection"

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)


@app.get("/get_context")
async def get_context(message_embedding: str, top_k: int = 3) -> Response:
    """
    Ищет наиболее релевантные документы для вопроса
    и формирует контекст
    :param message_embedding: вектор вопроса юзера,
    :param top_k: количество возвращаемых документов

    returns: json response: {
                            document: document,
                            source_url: source_url,
                            }
    """
    logging.info(f"Получен запрос на поиск контекста. Запрашиваемое количество документов (top_k): {top_k}")
    try:
        embedding_list = json.loads(message_embedding)

        results = collection.query(
            query_embeddings=[embedding_list],
            n_results=top_k,
            include=["metadatas", "documents"]
        )

        if not results or not results["metadatas"][0]:
            logging.warning("Поиск в ChromaDB не дал результатов для данного запроса.")
            return Response(content=json.dumps([]), media_type="application/json")

        context_data = []
        log_summary = ["Найденный контекст для передачи в LLM:"]

        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            context_data.append({
                "document": doc,
                "source_url": meta.get("source_url", "Источник не найден")
            })

            title = meta.get('article_title', 'Без заголовка')
            source = meta.get('source_url', 'URL отсутствует')
            log_summary.append(f"  - Заголовок: '{title}', Источник: {source}")

        logging.info("\n".join(log_summary))

    except Exception as e:
        logging.error(f"Ошибка при обработке запроса к ChromaDB: {e}", exc_info=True)
        return Response(content="Произошла ошибка при поиске информации.", status_code=500)

    return Response(content=json.dumps(context_data, ensure_ascii=False), media_type="application/json")

# uvicorn vector_db.chroma_db:app --host 0.0.0.0 --port 5004 --reload