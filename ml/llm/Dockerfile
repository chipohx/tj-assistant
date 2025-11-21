# Builder - установка зависимостей и компиляция
FROM python:3.12-slim AS builder

WORKDIR /app
# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime - минимальный образ
FROM python:3.12-slim

WORKDIR /app

# Копирование установленных пакетов из builder
COPY --from=builder /root/.local /root/.local

# Создание структуры пакета и копирование кода
RUN mkdir -p llm
COPY llm.py config.py __init__.py llm/

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH

# Порт сервиса
EXPOSE 5005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5005/health', timeout=5)" || exit 1

# Запуск приложения
CMD ["uvicorn", "llm:app", "--host", "0.0.0.0", "--port", "5005"]
