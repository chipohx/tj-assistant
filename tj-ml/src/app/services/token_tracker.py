"""Token usage tracking for LLM API calls."""
from typing import Any, Dict, List
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from app.core.logging import get_logger


logger = get_logger(__name__)


class TokenUsageCallback(BaseCallbackHandler):
    """
    Callback handler для отслеживания использования токенов с детализацией.
    
    Отслеживает:
    - Токены из запроса пользователя
    - Токены из контекста RAG (векторная БД)
    - Токены ответа модели
    """
    
    def __init__(self, query_tokens: int = 0, context_tokens: int = 0):
        """
        Инициализация callback.
        
        Args:
            query_tokens: Количество токенов в запросе пользователя
            context_tokens: Количество токенов в контексте из векторной БД
        """
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.successful_requests = 0
        self.query_tokens = query_tokens
        self.context_tokens = context_tokens
        
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Вызывается в начале LLM запроса."""
        pass
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Вызывается в конце LLM запроса для подсчёта токенов."""
        if response.llm_output is None:
            return
            
        token_usage = response.llm_output.get("token_usage", {})
        
        if token_usage:
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)
            total_tokens = token_usage.get("total_tokens", 0)
            
            # Если total_tokens не предоставлен, вычисляем
            if not total_tokens and (prompt_tokens or completion_tokens):
                total_tokens = prompt_tokens + completion_tokens
            
            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens
            self.total_tokens += total_tokens
            self.successful_requests += 1
            
            logger.info(
                f"📊 Token Usage - "
                f"Query: {self.query_tokens}, "
                f"Context: {self.context_tokens}, "
                f"Total Input: {prompt_tokens}, "
                f"Output: {completion_tokens}, "
                f"Total: {total_tokens}"
            )
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Вызывается при ошибке LLM."""
        logger.error(f"❌ LLM Error: {error}")
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Получить детальную статистику использования токенов."""
        return {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "successful_requests": self.successful_requests,
            "query_tokens": self.query_tokens,
            "context_tokens": self.context_tokens,
        }
    
    def reset(self) -> None:
        """Сбросить счётчики."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.successful_requests = 0
