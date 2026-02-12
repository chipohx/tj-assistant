"""
Модуль настройки логирования для сервиса TJ-Assistant ML.

Предоставляет функции для конфигурации и получения логгеров
с единым форматом вывода и уровнем логирования.
"""

import logging
import sys


def configure_logging() -> None:
    """
    Настраивает глобальное логирование приложения.

    Устанавливает формат сообщений с временной меткой, уровнем,
    именем логгера и текстом сообщения. Вывод направляется в stdout.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    """
    Получить именованный логгер.

    Args:
        name: Имя логгера (обычно __name__ вызывающего модуля).

    Returns:
        logging.Logger: Сконфигурированный экземпляр логгера.
    """
    return logging.getLogger(name)
