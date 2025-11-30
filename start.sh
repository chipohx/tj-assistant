#!/bin/bash
if ! docker images | grep -q "tj-assistant.*embedding_model"; then
    echo "building embedding_model and vector_db..."
    docker compose build embedding_model vector_db
fi

# запускаем в фоне
docker compose up -d embedding_model vector_db

# ждем пока они станут healthy
echo "ждём embedding_model и vector_db..."
timeout 180 bash -c 'until docker-compose ps | grep -q "embedding_model.*healthy"; do sleep 2; done'

# пересобираем и запускаем остальное
docker compose build main # сюда добавить контейнер, который хотим пересобрать
docker compose up llm main postgres backend