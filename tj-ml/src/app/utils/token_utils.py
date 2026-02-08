"""Утилиты для подсчёта токенов в тексте."""
from typing import Optional


def estimate_tokens(text: str, method: str = "approximate") -> int:
    """
    Приблизительный подсчёт токенов в тексте.
    
    Args:
        text: Текст для подсчёта
        method: Метод подсчёта ("approximate" или "words")
        
    Returns:
        Приблизительное количество токенов
        
    Note:
        Для точного подсчёта нужен токенайзер конкретной модели.
        Используем приблизительные методы:
        - approximate: ~1 токен на 4 символа (усреднённо для английского и русского)
        - words: количество слов (консервативная оценка)
    """
    if not text:
        return 0
    
    if method == "words":
        # Подсчёт слов (обычно 1 слово = 1-2 токена)
        return len(text.split())
    
    # Метод approximate: среднее между символами и словами
    # Для русского текста: ~1 токен на 3-4 символа
    # Для английского: ~1 токен на 4 символа
    char_estimate = len(text) // 4
    word_estimate = len(text.split())
    
    # Берём среднее между двумя оценками
    return (char_estimate + word_estimate) // 2


def estimate_tokens_safe(text: Optional[str]) -> int:
    """Безопасный подсчёт токенов с обработкой None."""
    if text is None:
        return 0
    return estimate_tokens(text)
