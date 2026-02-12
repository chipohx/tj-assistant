"""
Модуль отслеживания использования токенов при вызовах LLM.

Содержит callback-обработчик TokenUsageCallback, который подключается
к LangChain chain/agent и собирает статистику по токенам:
- Токены из запроса пользователя
- Токены из RAG-контекста (документы из векторной БД)
- Входные и выходные токены LLM (от API)
- Общее количество успешных запросов

Поддерживает агрегацию по нескольким вызовам LLM
(как в агентном цикле с инструментами).
"""

from typing import Any, Dict, List

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from app.core.logging import get_logger


logger = get_logger(__name__)


class TokenUsageCallback(BaseCallbackHandler):
    """
    Callback-обработчик для сбора статистики использования токенов.

    Подключается к LangChain вызовам через параметр config.callbacks.
    Агрегирует данные по всем вызовам LLM в рамках одного запроса
    (поддерживает многошаговые агентные сценарии).

    Attributes:
        total_tokens: Общее количество использованных токенов (от API).
        prompt_tokens: Общее количество входных токенов (от API).
        completion_tokens: Общее количество выходных токенов (от API).
        successful_requests: Число успешных запросов к LLM.
        query_tokens: Оценка количества токенов в запросе пользователя.
        context_tokens: Оценка количества токенов в RAG-контексте.
    """

    def __init__(self, query_tokens: int = 0, context_tokens: int = 0) -> None:
        """
        Инициализация callback-обработчика.

        Args:
            query_tokens: Оценённое количество токенов в запросе пользователя.
            context_tokens: Оценённое количество токенов в контексте из векторной БД.
        """
        self.total_tokens: int = 0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.successful_requests: int = 0
        self.query_tokens: int = query_tokens
        self.context_tokens: int = context_tokens

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Вызывается перед каждым запросом к LLM. Не выполняет действий."""
        pass

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """
        Вызывается после завершения запроса к LLM.

        Извлекает данные о токенах из ответа и агрегирует их.
        Поддерживает как стандартный формат token_usage от OpenAI/GigaChat,
        так и вычисление total_tokens при его отсутствии.

        Args:
            response: Результат вызова LLM с метаданными.
        """
        if response.llm_output is None:
            return

        token_usage = response.llm_output.get("token_usage", {})

        if token_usage:
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)
            total_tokens = token_usage.get("total_tokens", 0)

            if not total_tokens and (prompt_tokens or completion_tokens):
                total_tokens = prompt_tokens + completion_tokens

            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens
            self.total_tokens += total_tokens
            self.successful_requests += 1

            logger.info(
                "Использование токенов — "
                "Query: %d, Context: %d, Input: %d, Output: %d, Total: %d, "
                "Запрос #%d",
                self.query_tokens,
                self.context_tokens,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                self.successful_requests,
            )

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """
        Вызывается при ошибке LLM.

        Args:
            error: Исключение, произошедшее при вызове LLM.
        """
        logger.error("Ошибка LLM: %s", error)

    def get_usage_stats(self) -> Dict[str, int]:
        """
        Получить агрегированную статистику использования токенов.

        Returns:
            Dict[str, int]: Словарь со статистикой:
                - query_tokens: токены из запроса пользователя
                - context_tokens: токены из RAG-контекста
                - prompt_tokens: общие входные токены (от API)
                - completion_tokens: общие выходные токены (от API)
                - total_tokens: общее количество токенов
                - successful_requests: число успешных запросов к LLM
        """
        return {
            "query_tokens": self.query_tokens,
            "context_tokens": self.context_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "successful_requests": self.successful_requests,
        }

    def reset(self) -> None:
        """Сбросить все счётчики до нулевых значений."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.successful_requests = 0
