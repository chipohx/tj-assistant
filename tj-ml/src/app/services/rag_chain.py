from typing import Dict, List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from app.services.vector_store import get_vector_store
from app.services.llm import get_llm
from app.services.token_tracker import TokenUsageCallback
from app.utils.token_utils import estimate_tokens


PROMPT_TEMPLATE = """Ты - ассистент по статьям Т⁠-⁠Ж (Тинькофф Журнал). Отвечай только на основе предоставленного контекста.

Правила:
1. Если в контексте нет ответа, ответь: "К сожалению, я не нашёл информации по вашему вопросу в базе статей Т⁠-⁠Ж."
2. ТОЛЬКО ЕСЛИ ответ найден, то в конце ответа ОДИН РАЗ добавь раздел "Источники:" со ссылками в формате:
   - [Название статьи](URL)
3. Отвечай кратко и по делу на русском языке.
4. ОБЯЗАТЕЛЬНО отвечай в MD формате для отделения заголовков нумеровнанных/bullet списков и таблиц

Контекст с источниками:
{context}

Вопрос: {question}

Ответ (не забудь про раздел "Источники:" в конце):"""


def _format_docs(docs: List[Document]) -> str:
    """Format documents with content and metadata including source URLs."""
    formatted = []
    for i, doc in enumerate(docs, 1):
        content = doc.page_content
        metadata = doc.metadata
        
        # Extract source URL and title from metadata
        source_url = metadata.get('source_url', 'N/A')
        article_title = metadata.get('article_title', 'Неизвестная статья')
        
        formatted.append(
            f"Фрагмент {i}:\n{content}\n"
            f"Источник: {article_title}\nURL: {source_url}"
        )
    
    return "\n\n".join(formatted)


def query_rag(question: str, top_k: int = 3) -> Tuple[str, str, List[Document], Dict[str, int]]:
    """
    Выполняет RAG запрос с детальным отслеживанием использования токенов.
    
    Args:
        question: Вопрос пользователя
        top_k: Количество документов для контекста
        
    Returns:
        Tuple содержащий:
        - answer: Ответ модели
        - context: Контекст из векторной БД
        - docs: Список документов-источников
        - token_usage: Детальная статистика токенов (query, context, prompt, completion, total)
    """
    vector_store = get_vector_store()
    llm = get_llm()

    # Получаем документы из векторной БД
    docs = vector_store.similarity_search(question, k=top_k)
    context = _format_docs(docs)
    
    # Подсчитываем токены запроса и контекста
    query_tokens = estimate_tokens(question)
    context_tokens = estimate_tokens(context)

    # Создаём callback для отслеживания токенов с детализацией
    token_callback = TokenUsageCallback(
        query_tokens=query_tokens,
        context_tokens=context_tokens
    )

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()

    # Вызываем chain с callback для отслеживания токенов
    answer = chain.invoke(
        {"context": context, "question": question},
        config={"callbacks": [token_callback]}
    )
    
    # Add sources to answer if not already present
    if "источник" not in answer.lower() and "source" not in answer.lower():
        sources_text = "\n\n**Источники:**\n"
        unique_sources = {}
        for doc in docs:
            url = doc.metadata.get('source_url', '')
            title = doc.metadata.get('article_title', 'Статья Т⁠-⁠Ж')
            if url and url not in unique_sources:
                unique_sources[url] = title
        
        for url, title in unique_sources.items():
            sources_text += f"- [{title}]({url})\n"
        
        answer = answer + sources_text
    
    # Получаем детальную статистику использования токенов
    token_usage = token_callback.get_usage_stats()
    
    return answer, context, docs, token_usage
