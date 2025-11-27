# tj-assistant quickstart

## запуск всего проекта

```bash
# из корня проекта
docker compose up --build
```

жди сообщения: `✅ Все сервисы готовы (Backend + ML)`

## доступные сервисы

### api endpoints
- **backend api**: http://localhost:8000/docs
- **ml api**: http://localhost:8001/health
- **postgres**: localhost:5432

### порты
```
8000 - backend (fastapi)
8001 - ml orchestrator
5003 - embedding model
5004 - vector db
5005 - llm service
5432 - postgres
```

## разработка

### только backend
```bash
docker-compose up backend postgres
```

### только ml
```bash
cd ml
docker-compose up
```

### изменения в коде
все сервисы с `--reload`, изменения применяются автоматически:
- `backend/app/*.py` → backend перезагружается
- `ml/*//*.py` → ml сервис перезагружается

## что дальше?

1. читай [DOCKER_README.md](DOCKER_README.md) для деталей
2. читай [ml/MIGRATION.md](ml/MIGRATION.md) про новую структуру
3. читай [ml/config/README.md](ml/config/README.md) про ml dockerfile

## проблемы?

### медленный старт
первый запуск скачивает модели (5-10 мин), потом кешируется.

### "unhealthy" сервисы
```bash
docker-compose logs embedding_model  # смотри логи
```

### порты заняты
проверь что ничего не слушает на 8000, 8001, 5003-5005, 5432:
```bash
lsof -i :8000
```

## остановка

```bash
docker-compose down        # остановить
docker-compose down -v     # остановить + удалить volumes (осторожно!)
```

