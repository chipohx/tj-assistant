"""
Модуль инструментов (tools) для агентного цикла.

Определяет набор инструментов, доступных агенту TJ-Assistant
для выполнения сложных задач: поиск по базе знаний, математические
вычисления, получение текущей даты и извлечение структурированных данных.

Инструменты реализованы как LangChain-совместимые функции с декоратором @tool,
что позволяет привязывать их к моделям с поддержкой function calling (GigaChat-Pro/Max).
"""

import ast
import operator
from datetime import datetime, timezone
from typing import List

from langchain_core.documents import Document
from langchain_core.tools import tool

from app.core.logging import get_logger
from app.services.vector_store import search_mmr


logger = get_logger(__name__)

# Безопасные математические операции для вычислений
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_node(node: ast.AST) -> float:
    """
    Рекурсивно вычислить значение узла AST-дерева.

    Поддерживает только базовые арифметические операции
    для безопасного вычисления математических выражений.

    Args:
        node: Узел абстрактного синтаксического дерева Python.

    Returns:
        float: Результат вычисления.

    Raises:
        ValueError: При обнаружении неподдерживаемой операции.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Неподдерживаемая операция: {op_type.__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        return _SAFE_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Неподдерживаемая операция: {op_type.__name__}")
        operand = _safe_eval_node(node.operand)
        return _SAFE_OPERATORS[op_type](operand)
    else:
        raise ValueError(f"Неподдерживаемое выражение: {ast.dump(node)}")


def _format_search_results(docs: List[Document]) -> str:
    """
    Отформатировать результаты поиска для вставки в контекст агента.

    Args:
        docs: Список документов из Qdrant.

    Returns:
        str: Отформатированная строка с содержимым и метаданными документов.
    """
    if not docs:
        return "Результатов не найдено."

    parts = []
    for i, doc in enumerate(docs, 1):
        title = doc.metadata.get("article_title", "Без названия")
        url = doc.metadata.get("source_url", "")
        parts.append(
            f"--- Результат {i}: {title} ---\n"
            f"{doc.page_content}\n"
            f"Источник: {url}"
        )
    return "\n\n".join(parts)


@tool
def search_knowledge_base(query: str) -> str:
    """Поиск статей в базе знаний Тинькофф Журнала по заданному запросу.

    Используй этот инструмент когда:
    - Нужна дополнительная информация по теме вопроса
    - Вопрос затрагивает несколько тем и нужен контекст по каждой
    - Нужно уточнить или проверить факты из имеющегося контекста
    - Пользователь задаёт вопрос о конкретной статье или теме

    Args:
        query: Поисковый запрос на русском языке. Формулируй кратко и по существу.
    """
    logger.info("Инструмент search_knowledge_base: запрос='%s'", query)
    docs = search_mmr(query, top_k=4)
    result = _format_search_results(docs)
    logger.info("Найдено документов: %d", len(docs))
    return result


@tool
def calculate(expression: str) -> str:
    """Вычислить математическое выражение и вернуть результат.

    Используй этот инструмент когда:
    - Нужно посчитать проценты, налоги, доходность
    - Нужно сложить, вычесть, умножить или разделить числа
    - Пользователь просит рассчитать что-то конкретное

    Поддерживаемые операции: +, -, *, /, //, %, **
    Примеры: "100000 * 0.13", "50000 + 50000 * 0.1", "2 ** 10"

    Args:
        expression: Математическое выражение в формате Python (например, "100000 * 0.13").
    """
    logger.info("Инструмент calculate: выражение='%s'", expression)
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval_node(tree.body)
        # Форматируем результат: убираем лишние нули для целых чисел
        if result == int(result):
            formatted = f"{int(result):,}".replace(",", " ")
        else:
            formatted = f"{result:,.2f}".replace(",", " ")
        logger.info("Результат вычисления: %s = %s", expression, formatted)
        return f"Результат: {expression} = {formatted}"
    except (ValueError, SyntaxError, ZeroDivisionError) as exc:
        error_msg = f"Ошибка вычисления '{expression}': {exc}"
        logger.warning(error_msg)
        return error_msg


@tool
def get_current_date() -> str:
    """Получить текущую дату и время.

    Используй этот инструмент когда:
    - Нужно знать текущую дату для расчёта сроков
    - Пользователь спрашивает о дедлайнах или сроках относительно сегодня
    - Нужно определить актуальность информации
    """
    now = datetime.now(timezone.utc)
    return (
        f"Текущая дата и время (UTC): {now.strftime('%d.%m.%Y %H:%M')}. "
        f"День недели: {now.strftime('%A')}."
    )


def get_all_tools() -> list:
    """
    Получить список всех доступных инструментов агента.

    Returns:
        list: Список LangChain-инструментов [search_knowledge_base, calculate, get_current_date].
    """
    return [search_knowledge_base, calculate, get_current_date]
