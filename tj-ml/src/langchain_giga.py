import os
from dotenv import load_dotenv
from langchain_gigachat.chat_models import GigaChat
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Загружаем переменные окружения
load_dotenv()

GIGACHAT_AUTH_KEY = os.getenv('GIGACHAT_AUTH_KEY')
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
COLLECTION_NAME = "tj"


def main():
    # 1. Инициализация локальной модели эмбеддингов
    print("Загрузка модели эмбеддингов...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # 2. Подключение к существующей базе Qdrant
    print(f"Подключение к Qdrant ({COLLECTION_NAME})...")
    vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
    )

    # 3. Инициализация GigaChat
    llm = GigaChat(
        credentials=GIGACHAT_AUTH_KEY,
        model="GigaChat",
        verify_ssl_certs=False
    )

    # 4. Создание RAG цепочки
    template = """Используй только предоставленный контекст, чтобы ответить. 
    Если в контексте нет ответа, скажи, что ты не знаешь.
    Отвечай кратко и по делу.

    Контекст:
    {context}

    Вопрос: {question}

    Ответ:"""

    prompt = ChatPromptTemplate.from_template(template)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # LCEL цепочка
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # 5. Тестовый запрос
    query = "Куда можно сходить в Питере?"
    print(f"\nВопрос: {query}")
    print("-" * 30)

    try:
        response = rag_chain.invoke(query)
        print(f"Ответ RAG:\n{response}")
    except Exception as e:
        print(f"Ошибка при выполнении запроса: {e}")


if __name__ == "__main__":
    main()
