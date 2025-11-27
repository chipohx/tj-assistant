# tj-assistant docker setup

единый docker-compose для всего проекта: backend + ml микросервисы.

## структура сервисов

### backend services (порты 8000, 5432)
- **postgres** - postgresql база данных
- **backend** - fastapi backend с auth/chat api (порт 8000)

### ml services (порты 5003-5005, 8001)
- **embedding_model** - sentence-transformers для векторизации (порт 5003)
- **vector_db** - chromadb для семантического поиска (порт 5004)
- **llm** - gemini api для генерации ответов (порт 5005)
- **main** - orchestrator для ml pipeline (порт 8001)

## быстрый старт

```bash
# собрать и запустить все сервисы
docker-compose up --build

# запустить только backend + postgres
docker-compose up backend postgres

# запустить только ml сервисы
docker-compose up embedding_model vector_db llm main

# остановить все
docker-compose down

# остановить и удалить volumes
docker-compose down -v
```

## endpoints

### backend api
- `http://localhost:8000/api/chat` - chat endpoint
- `http://localhost:8000/api/auth` - auth endpoint
- `http://localhost:8000/docs` - swagger ui

### ml api
- `http://localhost:5003/health` - embedding model status
- `http://localhost:5004/health` - vector db status  
- `http://localhost:5005/health` - llm status
- `http://localhost:8001/health` - main service status
- `http://localhost:8001/llm_response` - основной ml endpoint

### database
- `postgresql://user:pass@localhost:5432/maindb`

## архитектура

```
frontend (port 3000)
    ↓
backend (port 8000) ←→ postgres (port 5432)
    ↓
main ml service (port 8001)
    ↓
    ├── embedding_model (port 5003)
    ├── vector_db (port 5004)
    └── llm (port 5005)
```

## volumes

- `postgres_data` - персистентные данные postgresql
- `hf_cache` - кеш моделей huggingface (shared между ml сервисами)

## development mode

все сервисы запущены с `--reload`, изменения в коде применяются автоматически:

```bash
# изменить backend код
vim backend/app/main.py  # автоперезагрузка

# изменить ml код
vim ml/llm/llm_api.py  # автоперезагрузка
```

## production готовность

для продакшна нужно:

1. убрать `--reload` флаги из command
2. добавить .env файлы с секретами
3. настроить nginx reverse proxy
4. использовать managed postgres (не docker)
5. добавить monitoring/logging
6. настроить ssl/https

## troubleshooting

### "service unhealthy"
```bash
# проверить логи
docker-compose logs embedding_model

# зайти в контейнер
docker exec -it embedding_model_service bash
curl http://localhost:5003/health
```

### "connection refused" между сервисами
убедитесь что используете docker service names:
- ✅ `http://embedding_model:5003`
- ❌ `http://localhost:5003`

### медленный startup ml сервисов
первый запуск скачивает модели, может занять 5-10 минут. hf_cache volume сохраняет их для последующих запусков.

### postgres data migration
```bash
# backup
docker exec tj_postgres pg_dump -U user maindb > backup.sql

# restore
docker exec -i tj_postgres psql -U user maindb < backup.sql
```

## мониторинг

```bash
# статус всех контейнеров
docker-compose ps

# логи в реальном времени
docker-compose logs -f

# ресурсы
docker stats

# проверка healthchecks
docker inspect embedding_model_service | grep -A 10 Health
```

## полезные команды

```bash
# rebuild конкретного сервиса
docker-compose build backend
docker-compose up -d backend

# restart сервиса без rebuild
docker-compose restart llm

# exec команды в контейнере
docker-compose exec backend python -m pytest
docker-compose exec postgres psql -U user maindb

# очистка всего
docker-compose down -v --rmi all
docker system prune -a
```

