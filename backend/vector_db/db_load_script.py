"""
Модуль для загрузки статей в chromadb
"""

import json
import logging
from pathlib import Path
import chromadb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
current_dir = Path(__file__).parent.resolve()

INPUT_JSON_FILE = current_dir / "articles.json"
CHROMA_DB_PATH = current_dir / "chroma_db"
COLLECTION_NAME = "articles_collection"
BATCH_SIZE = 128


def main():
    """
    Загружает готовые чанки из JSON в ChromaDB, работая с плоской структурой.
    """
    if not INPUT_JSON_FILE.exists():
        logging.error(f"Файл с данными не найден: {INPUT_JSON_FILE}")
        return

    logging.info(f"Чтение данных из файла: {INPUT_JSON_FILE}")
    with open(INPUT_JSON_FILE, "r", encoding="utf-8") as f:
        all_chunks_from_json = json.load(f)

    if not all_chunks_from_json:
        logging.warning("JSON-файл пуст, нет данных для загрузки.")
        return

    logging.info(f"Загружено {len(all_chunks_from_json)} чанков из файла. Начинаем подготовку и дедупликацию.")

    ids_list = []
    documents_list = []
    metadatas_list = []

    seen_ids = set()

    for chunk in all_chunks_from_json:
        if "document" not in chunk or "metadata" not in chunk:
            continue

        metadata = chunk["metadata"]

        source_url = metadata.get("source_url", "unknown_source")
        chunk_index = metadata.get("chunk_id", "unknown_chunk")
        unique_id = f"{source_url}#chunk_{chunk_index}"

        # Пропускаем дубликаты
        if unique_id in seen_ids:
            continue

        seen_ids.add(unique_id)

        ids_list.append(unique_id)
        documents_list.append(chunk["document"])
        metadatas_list.append(metadata)

    logging.info(f"После дедупликации подготовлено {len(ids_list)} уникальных чанков для загрузки.")

    if not ids_list:
        logging.warning(
            "Нет уникальных чанков для загрузки (возможно, все они уже есть в базе или являются дубликатами).")
        return

    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        collection = client.get_or_create_collection(name=COLLECTION_NAME)

        # Итерируемся по индексам для создания пакетов (батчей)
        for i in range(0, len(ids_list), BATCH_SIZE):
            batch_ids = ids_list[i:i + BATCH_SIZE]
            batch_documents = documents_list[i:i + BATCH_SIZE]
            batch_metadatas = metadatas_list[i:i + BATCH_SIZE]

            logging.info(f"Загрузка пакета {i // BATCH_SIZE + 1} (размер: {len(batch_ids)})...")

            collection.add(
                ids=batch_ids,
                documents=batch_documents,
                metadatas=batch_metadatas
            )

        logging.info("--- Все данные успешно загружены в ChromaDB ---")
        logging.info(f"Всего документов в коллекции '{COLLECTION_NAME}': {collection.count()}")
    except chromadb.errors.DuplicateIDError:
        logging.error(
            "Ошибка дублирования ID. Это означает, что некоторые из этих чанков уже существуют в базе данных.")
        logging.info("Чтобы добавить только новые, используйте метод `collection.upsert()` вместо `collection.add()`.")
    except Exception as e:
        logging.error(f"Произошла ошибка при работе с ChromaDB: {e}", exc_info=True)


if __name__ == "__main__":
    main()