"""
Утилиты для приблизительной оценки количества токенов в тексте.

Так как точный подсчёт требует токенизатора конкретной модели,
используются эвристические методы оценки.

Для русского текста характерно ~1 токен на 3-4 символа.
Для английского — ~1 токен на 4 символа.
"""

from typing import Optional


def estimate_tokens(text: str, method: str = "approximate") -> int:
    """
    Приблизительно оценить количество токенов в тексте.

    Args:
        text: Текст для оценки.
        method: Метод оценки:
            - 'approximate' (по умолчанию) — среднее между оценкой
              по символам и по словам. Хорошо работает для смешанных текстов.
            - 'words' — количество слов (консервативная оценка).

    Returns:
        int: Приблизительное количество токенов (>= 0).

    Note:
        Для точного подсчёта необходим токенизатор конкретной модели.
        Данные эвристики дают погрешность ~15-25%.
    """
    if not text:
        return 0

    if method == "words":
        return len(text.split())

    # Для русского текста: ~1 токен на 3-4 символа
    # Для английского: ~1 токен на 4 символа
    char_estimate = len(text) // 4
    word_estimate = len(text.split())

    return (char_estimate + word_estimate) // 2


def estimate_tokens_safe(text: Optional[str]) -> int:
    """
    Безопасная оценка количества токенов с обработкой None.

    Args:
        text: Текст для оценки или None.

    Returns:
        int: Количество токенов (0 если text is None).
    """
    if text is None:
        return 0
    return estimate_tokens(text)
