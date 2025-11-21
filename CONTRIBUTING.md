### Как запускать контейнеры

1) установить переменную GEMINI_API_KEY в окружение (ключ можно взять в https://aistudio.google.com/api-keys)
2) запустить [db_load_script.py](ml/vector_db/db_load_script.py), так вы наполните БД статьями
3) ```docker compose up -d```
4) первый запуск будет долгим, так как грузится e5