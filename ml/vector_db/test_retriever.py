"""
Только для теста
"""

import logging
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
from transformers import pipeline, set_seed

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

current_dir = Path(__file__).parent.resolve()
# позже вынести в consts.py

CHROMA_DB_PATH = current_dir / "chroma_db"
COLLECTION_NAME = "articles_collection"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
LLM_MODEL_NAME = "distilgpt2"
TOP_K_RESULTS = 5


def initialize_retriever():
    """Инициализирует клиент ChromaDB и модель для создания встраиваний."""
    logging.info("Инициализация компонентов Retriever...")
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        collection = client.get_collection(name=COLLECTION_NAME)
        logging.info(f"Успешно подключено к коллекции '{COLLECTION_NAME}' с {collection.count()} документами.")

        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cpu')
        logging.info(f"Модель для встраиваний '{EMBEDDING_MODEL_NAME}' успешно загружена.")

        return collection, embedding_model
    except Exception as e:
        logging.error(f"Ошибка при инициализации Retriever: {e}", exc_info=True)
        return None, None


def initialize_llm():
    """Инициализирует небольшую языковую модель для генерации ответа."""
    logging.info(f"Загрузка языковой модели: {LLM_MODEL_NAME}...")
    try:
        # Использование pipeline для упрощения генерации текста
        qa_pipeline = pipeline('text-generation', model=LLM_MODEL_NAME, device='cpu')
        set_seed(42)  # Для воспроизводимости результатов
        logging.info("Языковая модель успешно загружена.")
        return qa_pipeline
    except Exception as e:
        logging.error(f"Не удалось загрузить языковую модель: {e}", exc_info=True)
        return None


def answer_question(question: str, collection: chromadb.Collection, embedding_model: SentenceTransformer, llm_pipeline):
    """
    Находит релевантную информацию в ChromaDB и генерирует ответ с помощью ЯМ.
    """
    if not all([collection, embedding_model, llm_pipeline]):
        logging.error("Один из компонентов (ChromaDB, модель встраиваний, ЯМ) не был инициализирован.")
        return "Не удалось обработать запрос из-за внутренней ошибки."

    logging.info(f"Получен вопрос: \"{question}\"")

    # Создание встраивания для вопроса
    logging.info("Создание встраивания для вопроса...")
    query_embedding = embedding_model.encode(question).tolist()

    # Поиск релевантных документов в ChromaDB
    logging.info(f"Поиск {TOP_K_RESULTS} наиболее релевантных документов...")
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K_RESULTS
        )
        retrieved_documents = results['documents'][0]
        if not retrieved_documents:
            logging.warning("Не найдено релевантных документов в базе знаний.")
            return "К сожалению, я не нашел информации по вашему вопросу в базе знаний."

    except Exception as e:
        logging.error(f"Ошибка при запросе к ChromaDB: {e}")
        return "Произошла ошибка при поиске информации."

    context = "\n\n".join(retrieved_documents)
    logging.info(f"Извлеченный контекст:\n---\n{context}\n---")

    # Формирование промпта и генерация ответа
    prompt = f"""
Контекст:
{context}

Вопрос: {question}

Ответь на вопрос, основываясь только на предоставленном выше контексте.
Ответ:
"""
    logging.info("Генерация ответа с помощью языковой модели...")

    try:
        # max_length определяет общую длину промпта + сгенерированного ответа
        generated_text = llm_pipeline(prompt, max_length=512, num_return_sequences=1, truncation=True)
        answer = generated_text[0]['generated_text'].split("Ответ:")[1].strip()

        logging.info(f"Сгенерированный ответ: \"{answer}\"")
        return answer
    except Exception as e:
        logging.error(f"Ошибка при генерации ответа: {e}")
        return "Не удалось сгенерировать ответ."


def main():
    """
    Основная функция для демонстрации работы Retriever.
    """
    collection, embedding_model = initialize_retriever()
    llm_pipeline = initialize_llm()

    if not all([collection, embedding_model, llm_pipeline]):
        logging.error("Не удалось запустить приложение из-за ошибок инициализации.")
        return

    # --- Пример вопроса ---
    example_question = "как приготовить свиную корейку?"

    answer = answer_question(example_question, collection, embedding_model, llm_pipeline)

    print("\n" + "=" * 50)
    print(f"Вопрос: {example_question}")
    print(f"Ответ: {answer}")
    print("=" * 50)


if __name__ == "__main__":
    main()