import logging
import json
from pathlib import Path
import time

from article_parser import get_category_file_names
from ml.parser.article_parser import prepare_chunks_from_category

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
current_dir = Path(__file__).parent.resolve()
categories_path = current_dir / "categories"

# --- Параметры ---
ARTICLES_PER_CATEGORY = 2
# Имя файла для сохранения результата
OUTPUT_JSON_FILE = current_dir / "articles.json"

def main():
    """
    Главная функция для последовательного парсинга всех статей из всех категорий.
    """
    start_time = time.time()
    all_parsed_articles = []

    category_files = get_category_file_names()
    if not category_files:
        logging.info("Файлы категорий не найдены. Завершение работы.")
        return

    logging.info(f"Найдено {len(category_files)} категорий. Начинаем последовательный парсинг.")

    for category_index, category_file in enumerate(category_files):
        category_name = Path(category_file).stem.removeprefix('sitemap-flow-').removeprefix('sitemap-')
        category_articles = prepare_chunks_from_category(category_file, ARTICLES_PER_CATEGORY)
        logging.info(f"--- Категория '{category_name}' завершена. ---")
        all_parsed_articles.append(category_articles)

    if all_parsed_articles:
        logging.info(f"\nПарсинг завершен. Всего спарсено {len(all_parsed_articles)} статей.")
        with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
            for category_articles in all_parsed_articles:
                json.dump(category_articles, f, ensure_ascii=False, indent=2)
        logging.info(f"Все данные сохранены в файл: {OUTPUT_JSON_FILE}")
    else:
        logging.warning("Не удалось спарсить ни одной статьи.")

    end_time = time.time()
    logging.info(f"\n--- Вся работа завершена за {end_time - start_time:.2f} секунд ---")


if __name__ == "__main__":
    main()