# Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Установка build-зависимостей для компиляции torch и других пакетов
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime - минимальный образ
FROM python:3.12-slim

WORKDIR /app

# Копирование установленных пакетов из builder
COPY --from=builder /root/.local /root/.local

# Создание структуры пакета и копирование кода
RUN mkdir -p embedding_model
COPY embedding_model.py config.py __init__.py embedding_model/

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH

# Порт сервиса
EXPOSE 5003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5003/health', timeout=5)" || exit 1

# Запуск приложения
CMD ["uvicorn", "embedding_model:app", "--host", "0.0.0.0", "--port", "5003"]
