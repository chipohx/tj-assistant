# ML Services Configuration

эта директория содержит общую конфигурацию для всех ml микросервисов tj-assistant.

## структура

```
config/
├── .dockerfile          # единый multi-stage dockerfile для всех сервисов
├── requirements/        # requirements для каждого сервиса
│   ├── embedding_model.txt
│   ├── llm.txt
│   ├── vector_db.txt
│   └── main.txt
└── README.md
```

## как работает

все сервисы собираются из одного dockerfile с разными target stages:
- `embedding_model` - sentence-transformers с quantization
- `llm` - gemini api для генерации ответов
- `vector_db` - chromadb для векторного поиска
- `main` - orchestrator сервис

## использование

из директории `ml/`:

```bash
# собрать и запустить все сервисы
docker-compose up --build

# собрать конкретный сервис
docker-compose build embedding_model

# запустить конкретный сервис
docker-compose up embedding_model
```

## преимущества новой структуры

1. **DRY**: общие слои docker кешируются между сервисами
2. **anchors**: yaml anchors убирают дублирование конфигурации
3. **быстрый startup**: оптимизированные healthchecks с file-based caching
4. **кеш моделей**: hf_cache volume персистит загруженные модели
5. **multi-stage builds**: минимальные финальные образы (только runtime deps)

## изменения с оригинала

- убрал отдельные Dockerfile в каждом сервисе (теперь один .dockerfile)
- добавил hf_cache volume для кеширования моделей huggingface
- оптимизировал healthcheck (2s interval вместо 30s, file-based caching)
- исправил start_period для embedding (было 600000s lol, стало 120s)
- централизовал requirements в config/requirements/

