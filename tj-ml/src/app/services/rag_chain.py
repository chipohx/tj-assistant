"""
Модуль RAG-цепочки (Retrieval-Augmented Generation).

Реализует улучшенный RAG-пайплайн с:
- MMR-поиском для разнообразного контекста
- Детальным системным промптом с инструкциями для модели
- Поддержкой истории чата (многоходовые диалоги)
- Отслеживанием использования токенов

Используется как основная RAG-функция для прямых запросов
и как вспомогательная функция в агентном цикле.
"""

from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.logging import get_logger
from app.services.llm import get_llm
from app.services.token_tracker import TokenUsageCallback
from app.services.vector_store import search_mmr
from app.utils.token_utils import estimate_tokens


logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────────
# Системный промпт для прямого RAG (без агента)
# ────────────────────────────────────────────────────────────────────
RAG_SYSTEM_PROMPT = """Ты — TJ-Assistant, экспертный AI-ассистент по материалам Тинькофф Журнала (Т⁠-⁠Ж).
Ты глубоко разбираешься в финансах, праве, налогах, инвестициях, недвижимости и других темах, освещённых в Т⁠-⁠Ж.

## Правила ответа

1. **Основа ответа** — предоставленный контекст из базы знаний. Не выдумывай факты.
2. Если в контексте **нет ответа**, честно скажи: «К сожалению, я не нашёл информации по вашему вопросу в базе статей Т⁠-⁠Ж.»
3. **Структурируй ответ** в Markdown: используй заголовки (##), списки (- или 1.), таблицы, жирный текст.
4. Будь **конкретным**: приводи цифры, даты, ставки, суммы из статей.
5. Отвечай **подробно и экспертно**, но понятным языком — как опытный финансовый консультант.
6. В конце ответа **обязательно** добавь раздел «Источники:» со ссылками в формате:
   - [Название статьи](URL)
7. Отвечай **только на русском языке**.
8. Если вопрос неоднозначный — рассмотри разные варианты и объясни нюансы."""


RAG_USER_TEMPLATE = """Контекст из базы знаний Т⁠-⁠Ж:
{context}

Вопрос пользователя: {question}"""


def format_docs(docs: List[Document]) -> str:
    """
    Отформатировать список документов в структурированный текстовый контекст.

    Каждый документ оборачивается блоком с номером, содержимым,
    названием статьи и URL-источника.

    Args:
        docs: Список документов из векторного хранилища.

    Returns:
        str: Отформатированная строка контекста для промпта.
    """
    if not docs:
        return "Контекст не найден."

    parts = []
    for i, doc in enumerate(docs, 1):
        title = doc.metadata.get("article_title", "Без названия")
        url = doc.metadata.get("source_url", "")

        parts.append(
            f"### Фрагмент {i}: {title}\n"
            f"{doc.page_content}\n"
            f"Источник: [{title}]({url})"
        )
    return "\n\n---\n\n".join(parts)


def _ensure_sources_in_answer(answer: str, docs: List[Document]) -> str:
    """
    Гарантировать наличие раздела «Источники» в ответе.

    Если модель не добавила источники самостоятельно,
    формирует раздел с уникальными ссылками из использованных документов.

    Args:
        answer: Текст ответа модели.
        docs: Список документов-источников.

    Returns:
        str: Ответ с гарантированным разделом «Источники».
    """
    if "источник" in answer.lower() or "source" in answer.lower():
        return answer

    unique_sources: dict[str, str] = {}
    for doc in docs:
        url = doc.metadata.get("source_url", "")
        title = doc.metadata.get("article_title", "Статья Т⁠-⁠Ж")
        if url and url not in unique_sources:
            unique_sources[url] = title

    if not unique_sources:
        return answer

    sources_text = "\n\n**Источники:**\n"
    for url, title in unique_sources.items():
        sources_text += f"- [{title}]({url})\n"

    return answer + sources_text


def query_rag(
    question: str,
    top_k: int = 5,
    chat_history: Optional[List[dict]] = None,
) -> Tuple[str, str, List[Document], Dict[str, int]]:
    """
    Выполнить RAG-запрос: поиск контекста + генерация ответа.

    Пайплайн:
    1. MMR-поиск релевантных документов в Qdrant.
    2. Форматирование контекста.
    3. Построение промпта с системным сообщением, историей чата и контекстом.
    4. Генерация ответа через GigaChat.
    5. Добавление источников (если модель не добавила).

    Args:
        question: Вопрос пользователя.
        top_k: Количество документов для контекста.
        chat_history: Необязательная история чата в формате
                      [{"role": "user"|"assistant", "content": "..."}].

    Returns:
        Tuple из четырёх элементов:
        - answer (str): Сгенерированный ответ.
        - context (str): Отформатированный контекст из базы знаний.
        - docs (List[Document]): Список документов-источников.
        - token_usage (Dict[str, int]): Статистика использования токенов.
    """
    logger.info("RAG-запрос: question='%s', top_k=%d", question[:80], top_k)

    # 1. Поиск документов (MMR для разнообразия)
    docs = search_mmr(question, top_k=top_k)
    context = format_docs(docs)
    logger.info("Найдено документов: %d, длина контекста: %d символов", len(docs), len(context))

    # 2. Оценка токенов для отслеживания
    query_tokens = estimate_tokens(question)
    context_tokens = estimate_tokens(context)
    token_callback = TokenUsageCallback(
        query_tokens=query_tokens,
        context_tokens=context_tokens,
    )

    # 3. Построение сообщений
    messages = [SystemMessage(content=RAG_SYSTEM_PROMPT)]

    # Добавляем историю чата (если есть)
    if chat_history:
        for msg in chat_history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    # Добавляем текущий запрос с контекстом
    user_message = RAG_USER_TEMPLATE.format(context=context, question=question)
    messages.append(HumanMessage(content=user_message))

    # 4. Генерация ответа
    llm = get_llm()
    response = llm.invoke(messages, config={"callbacks": [token_callback]})
    answer = response.content

    # 5. Гарантируем наличие источников
    answer = _ensure_sources_in_answer(answer, docs)

    token_usage = token_callback.get_usage_stats()
    logger.info(
        "RAG-ответ сгенерирован: %d токенов, %d символов",
        token_usage.get("total_tokens", 0),
        len(answer),
    )

    return answer, context, docs, token_usage
