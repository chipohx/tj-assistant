"""
Модуль агента TJ-Assistant.

Реализует агентный цикл с поддержкой инструментов (tool calling):
1. Начальный поиск по базе знаний (RAG).
2. Передача контекста + вопроса в GigaChat с привязанными инструментами.
3. Если модель решает использовать инструмент — выполнение и возврат результата.
4. Цикл продолжается до получения финального текстового ответа
   или достижения лимита итераций.

Агент прозрачен для бэкенда: принимает вопрос, возвращает ответ
в том же формате, что и обычный RAG-пайплайн.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.llm import get_llm, get_llm_with_tools
from app.services.rag_chain import format_docs, _ensure_sources_in_answer
from app.services.token_tracker import TokenUsageCallback
from app.services.tools import get_all_tools
from app.services.vector_store import search_mmr
from app.utils.token_utils import estimate_tokens


logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────────
# Системный промпт для агента
# ────────────────────────────────────────────────────────────────────
AGENT_SYSTEM_PROMPT = """Ты — TJ-Assistant, экспертный AI-ассистент по материалам Тинькофф Журнала (Т⁠-⁠Ж).
Ты глубоко разбираешься в финансах, праве, налогах, инвестициях, недвижимости, путешествиях и других темах Т⁠-⁠Ж.

## Твои возможности

У тебя есть **инструменты**, которые ты можешь вызывать:
- **search_knowledge_base** — поиск статей в базе знаний Т⁠-⁠Ж по запросу.
- **calculate** — вычисление математических выражений (проценты, налоги, суммы).
- **get_current_date** — получение текущей даты и времени.

## Стратегия работы

1. Тебе уже предоставлен начальный контекст из базы знаний. Проанализируй его.
2. Если контекста **достаточно** — сразу дай подробный ответ.
3. Если контекста **недостаточно** или вопрос сложный:
   - Используй `search_knowledge_base` с переформулированным запросом.
   - Если нужны вычисления — используй `calculate`.
4. Для вопросов, требующих сравнения — поищи информацию по каждой теме отдельно.

## Правила ответа

1. **Основа** — информация из базы знаний. Не придумывай факты.
2. Если ответа **нет в базе**, скажи: «К сожалению, я не нашёл информации по вашему вопросу в базе статей Т⁠-⁠Ж.»
3. **Структурируй** ответ в Markdown: заголовки (##), списки, таблицы, жирный текст.
4. Будь **конкретным**: цифры, ставки, сроки, суммы из статей.
5. Отвечай **подробно и экспертно**, но понятным языком.
6. В конце добавь раздел «**Источники:**» со ссылками: `- [Название](URL)`.
7. Отвечай **только на русском**.
8. При неоднозначном вопросе — рассмотри варианты и объясни нюансы."""


@dataclass
class AgentResult:
    """
    Результат работы агента.

    Attributes:
        answer: Финальный текстовый ответ.
        context: Отформатированный начальный контекст из базы знаний.
        docs: Список документов, использованных для начального контекста.
        token_usage: Агрегированная статистика токенов по всем вызовам LLM.
        iterations: Количество итераций агентного цикла (0 = ответ без инструментов).
    """

    answer: str
    context: str
    docs: List[Document] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)
    iterations: int = 0


def _execute_tool_call(tool_call: dict, tools_map: dict) -> str:
    """
    Выполнить вызов инструмента по данным из ответа модели.

    Args:
        tool_call: Словарь с информацией о вызове:
                   {"name": str, "args": dict, "id": str}.
        tools_map: Словарь {имя_инструмента: экземпляр_инструмента}.

    Returns:
        str: Текстовый результат выполнения инструмента
             или сообщение об ошибке.
    """
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})

    logger.info("Вызов инструмента: %s(%s)", tool_name, tool_args)

    tool_func = tools_map.get(tool_name)
    if tool_func is None:
        error = f"Инструмент '{tool_name}' не найден."
        logger.warning(error)
        return error

    try:
        result = tool_func.invoke(tool_args)
        logger.info(
            "Результат инструмента %s: %d символов",
            tool_name,
            len(str(result)),
        )
        return str(result)
    except Exception as exc:
        error = f"Ошибка выполнения инструмента '{tool_name}': {exc}"
        logger.error(error)
        return error


def process_query(
    question: str,
    top_k: int = 5,
    chat_history: Optional[List[dict]] = None,
) -> AgentResult:
    """
    Обработать запрос пользователя через агентный цикл.

    Пайплайн:
    1. MMR-поиск начального контекста в Qdrant.
    2. Формирование сообщений: системный промпт + история + контекст + вопрос.
    3. Вызов GigaChat с привязанными инструментами.
    4. Если модель запрашивает инструменты — выполнение и возврат в модель.
    5. Повторение шагов 3-4 до финального ответа или лимита итераций.
    6. Гарантированное добавление источников к ответу.

    При ошибке в агентном цикле происходит fallback на прямой RAG-пайплайн.

    Args:
        question: Вопрос пользователя.
        top_k: Количество документов для начального контекста.
        chat_history: Необязательная история чата в формате
                      [{"role": "user"|"assistant", "content": "..."}].

    Returns:
        AgentResult: Объект с ответом, контекстом, источниками и статистикой.
    """
    settings = get_settings()
    max_iterations = settings.agent_max_iterations

    logger.info(
        "Агент: запрос='%s', top_k=%d, max_iterations=%d",
        question[:80],
        top_k,
        max_iterations,
    )

    # 1. Начальный поиск документов
    docs = search_mmr(question, top_k=top_k)
    context = format_docs(docs)

    # Оценка токенов
    query_tokens = estimate_tokens(question)
    context_tokens = estimate_tokens(context)
    token_callback = TokenUsageCallback(
        query_tokens=query_tokens,
        context_tokens=context_tokens,
    )
    callback_config = {"callbacks": [token_callback]}

    # 2. Формирование сообщений
    messages: List[BaseMessage] = [SystemMessage(content=AGENT_SYSTEM_PROMPT)]

    if chat_history:
        for msg in chat_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    user_content = (
        f"Начальный контекст из базы знаний:\n\n{context}\n\n"
        f"---\n\n"
        f"Вопрос пользователя: {question}"
    )
    messages.append(HumanMessage(content=user_content))

    # 3. Попытка агентного цикла с инструментами
    try:
        return _run_agent_loop(
            messages=messages,
            docs=docs,
            context=context,
            token_callback=token_callback,
            callback_config=callback_config,
            max_iterations=max_iterations,
        )
    except Exception as exc:
        logger.warning(
            "Агентный цикл завершился с ошибкой: %s. Fallback на прямой RAG.",
            exc,
        )
        return _fallback_direct_rag(
            messages=messages,
            docs=docs,
            context=context,
            token_callback=token_callback,
            callback_config=callback_config,
        )


def _run_agent_loop(
    messages: List[BaseMessage],
    docs: List[Document],
    context: str,
    token_callback: TokenUsageCallback,
    callback_config: dict,
    max_iterations: int,
) -> AgentResult:
    """
    Запустить агентный цикл с инструментами.

    Привязывает инструменты к модели и итеративно обрабатывает
    вызовы инструментов до получения финального ответа.

    Args:
        messages: Список сообщений для модели.
        docs: Начальные документы из RAG.
        context: Отформатированный контекст.
        token_callback: Callback для отслеживания токенов.
        callback_config: Конфигурация для LangChain invoke.
        max_iterations: Максимальное число итераций.

    Returns:
        AgentResult: Результат работы агента.
    """
    tools = get_all_tools()
    tools_map = {t.name: t for t in tools}
    llm_with_tools = get_llm_with_tools(tools)

    iterations = 0

    for iteration in range(max_iterations):
        response = llm_with_tools.invoke(messages, config=callback_config)

        # Если нет вызовов инструментов — это финальный ответ
        if not response.tool_calls:
            answer = _ensure_sources_in_answer(response.content, docs)
            logger.info(
                "Агент завершил работу за %d итераций (без инструментов на последней)",
                iterations,
            )
            return AgentResult(
                answer=answer,
                context=context,
                docs=docs,
                token_usage=token_callback.get_usage_stats(),
                iterations=iterations,
            )

        # Обрабатываем вызовы инструментов
        messages.append(response)
        iterations += 1

        for tool_call in response.tool_calls:
            result = _execute_tool_call(tool_call, tools_map)
            messages.append(
                ToolMessage(
                    content=result,
                    tool_call_id=tool_call.get("id", f"call_{iteration}"),
                )
            )

        logger.info("Агент: итерация %d/%d завершена", iterations, max_iterations)

    # Лимит итераций достигнут — запрашиваем финальный ответ без инструментов
    logger.warning(
        "Агент: достигнут лимит итераций (%d). Запрашиваю финальный ответ.",
        max_iterations,
    )
    messages.append(
        HumanMessage(
            content="Пожалуйста, дай финальный ответ на основе всей собранной информации."
        )
    )

    llm = get_llm()
    final_response = llm.invoke(messages, config=callback_config)
    answer = _ensure_sources_in_answer(final_response.content, docs)

    return AgentResult(
        answer=answer,
        context=context,
        docs=docs,
        token_usage=token_callback.get_usage_stats(),
        iterations=iterations,
    )


def _fallback_direct_rag(
    messages: List[BaseMessage],
    docs: List[Document],
    context: str,
    token_callback: TokenUsageCallback,
    callback_config: dict,
) -> AgentResult:
    """
    Запасной вариант: прямой RAG без инструментов.

    Используется когда агентный цикл завершился с ошибкой
    (например, модель не поддерживает function calling).

    Args:
        messages: Список сообщений для модели.
        docs: Документы из RAG.
        context: Отформатированный контекст.
        token_callback: Callback для отслеживания токенов.
        callback_config: Конфигурация для LangChain invoke.

    Returns:
        AgentResult: Результат прямого RAG-запроса.
    """
    llm = get_llm()
    response = llm.invoke(messages, config=callback_config)
    answer = _ensure_sources_in_answer(response.content, docs)

    return AgentResult(
        answer=answer,
        context=context,
        docs=docs,
        token_usage=token_callback.get_usage_stats(),
        iterations=0,
    )
