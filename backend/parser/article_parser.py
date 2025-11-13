import os
import logging
from pathlib import Path
from bs4 import BeautifulSoup
import time
import selenium_loader
import random

current_dir = Path(__file__).parent
categories_path = current_dir / "categories"

def parse_article(url: str, last_mod: str, category: str) -> dict | None:
    """Эта функция парсит одну статью

    На вход принимает url статьи
    В случае прямого вызова открывает
    и закрывает driver заново
    """
    driver = None
    try:
        # Для каждого вызова создаем свой драйвер, чтобы избежать проблем при многопоточности
        driver = selenium_loader.create_driver()
        html_content = selenium_loader.get_page_source(url, driver)

        if not html_content:
            logging.warning(f"Не удалось получить HTML для {url}")
            return None

        soup = BeautifulSoup(html_content, "html.parser")

        # --- Извлечение метаданных из <head> ---

        # Заголовок
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Заголовок не найден"
        title = title.replace('\xa0', ' ')
        title = title.replace('\xad', '')

        # --- Извлечение данных из <body> ---

        # Авторы (URL)
        authors = []
        author_links = soup.select("a[href^='/user']")

        for link in author_links:
            name_tag = link.select_one("div[class*='_name_']")  # Ищем div, класс которого содержит '_name_'

            if name_tag:
                author_name = name_tag.get_text(strip=True)
                author_url = link.get("href", "")

                authors.append({
                    "name": author_name,
                    "url": f"https://journal.tinkoff.ru{author_url}"
                })

        # --- Парсинг основного текста статьи ---
        main_content = soup.find("div", {"class": "_articleView_davr3_1"})
        if not main_content:
            logging.warning(f"Текст статьи не найден для {url}")
            return None

        found_elements = main_content.find_all("div", {"class": "_container_1k5mq_5"})
        text_chunks = []
        current_chunk_parts = []
        for element in found_elements:
            # Пропускаем блоки с информацией об авторе в самом тексте
            if element.select_one("._author_ab553_6"):
                continue

            if element.find("h2"):
                if current_chunk_parts:
                    text_chunks.append(" ".join(current_chunk_parts).strip())
                current_chunk_parts = []

            element_text = element.get_text(separator=" ", strip=True).replace("\xad", "").replace("\xa0", " ")
            if element_text:
                current_chunk_parts.append(element_text)

        if current_chunk_parts:
            text_chunks.append(" ".join(current_chunk_parts).strip())

        if not text_chunks:
            logging.warning(f"Не удалось извлечь текстовые чанки из {url}")
            return None

        return {
            "source_url": url,
            "title": title,
            "text": text_chunks,
            "last_mod": last_mod,
            "category": category,
        }

    except Exception as e:
        logging.error(f"Критическая ошибка при парсинге {url}: {e}", exc_info=True)
        return None
    finally:
        if driver:
            driver.quit()
        time.sleep(random.uniform(1, 3))


def get_category_urls_with_lastmod(category_filename: str) -> list[dict]:
    """
    Эта функция возвращает список словарей для каждой статьи из XML-файла.
    Каждый словарь содержит URL ('url') и дату последнего обновления ('last_mod').
    """

    file_path = categories_path / category_filename

    with open(file_path, "r", encoding="utf-8") as file:
        articles_data = []
        content = file.read()
        soup = BeautifulSoup(content, "xml")

        # Ищем родительские теги <url>, чтобы связать loc и lastmod
        for url_entry in soup.find_all("url"):
            loc_tag = url_entry.find("loc")
            lastmod_tag = url_entry.find("lastmod")

            # Проверяем, что оба тега существуют
            if loc_tag and lastmod_tag:
                # Извлекаем только дату (YYYY-MM-DD) из полной временной метки
                last_mod_date = lastmod_tag.text.split('T')[0]

                article_info = {
                    "url": loc_tag.text,
                    "last_mod": last_mod_date
                }
                articles_data.append(article_info)

        return articles_data


def parse_category(category_filename: str, articles_to_parse: int) -> list:
    """Эта функция парсит статьи из категории

    category_filename - содержит имя xml файла содержащего sitemap категории
    articles_to_parse - количество статей из категории которые нужно запарсить
    """

    category_data = []
    category_urls = get_category_urls_with_lastmod(category_filename)
    category_name = category_filename.removesuffix('.xml').removeprefix('sitemap-flow-').removeprefix('sitemap-')

    # Проверка что не хотим распарсить статей больше чем есть
    urls_to_parse = category_urls[:articles_to_parse]

    for article in urls_to_parse:
        article_url = article['url']
        last_mod = article['last_mod']
        try:
            article_data = parse_article(article_url, last_mod, category_name)
            # Проверка что article_data не пустой и содержит текст
            if (
                    article_data
                    and article_data.get("title")
                    and article_data.get("text")
            ):
                category_data.append(article_data)
                print(f"Successfully parsed: {article_url}")
            else:
                print(f"Успешный парсинг статьи: (empty result): {article_url}")
        except Exception as e:
            print(f"Ошибка при парсинге {article_url}: {e}")
            continue
    print("Все спарсенные статьи записаны в output.txt")
    return category_data


def get_category_file_names() -> list:
    """Возвращает название всех xml файлов папке категорий"""

    return [f for f in os.listdir(categories_path) if f.endswith(".xml")]


def prepare_chunks_from_category(category_filename: str, articles_to_parse: int) -> list:
    """
    Эта функция парсит статьи из категории и сразу же преобразует их
    в плоский список чанков, готовых для загрузки в ChromaDB.
    """
    # Получаем чистое имя категории из имени файла
    base_name = Path(category_filename).stem
    category_name = base_name.removeprefix('sitemap-flow-').removeprefix('sitemap-')

    # Это будет финальный список чанков со всех статей
    all_chunks_for_db = []

    articles_metadata = get_category_urls_with_lastmod(category_filename)
    urls_to_parse = articles_metadata[:articles_to_parse]

    # запись в файл для отладки
    with open("output.txt", "w", encoding="utf-8") as f:
        for article_meta in urls_to_parse:
            article_url = article_meta['url']
            last_mod = article_meta['last_mod']

            try:
                article_data = parse_article(article_url, last_mod, category_name)

                if not (article_data and article_data.get("text")):
                    print(f"Парсинг без результата (нет текста): {article_url}")
                    continue

                print(f"Успешно спарсена статья: {article_url}")

                for i, text_chunk in enumerate(article_data["text"]):
                    metadata = {
                        "source_url": article_data["source_url"],
                        "article_title": article_data["title"],
                        "last_mod": article_data["last_mod"],
                        "category": article_data["category"],
                        "chunk_id": i
                    }

                    chunk_object = {
                        "document": text_chunk,
                        "metadata": metadata
                    }
                    all_chunks_for_db.append(chunk_object)

                f.write(f"--- Статья: {article_data['title']} ---\n")
                for text in article_data["text"]:
                    f.write(text + "\n\n")
                f.write("=" * 50 + "\n\n")

            except Exception as e:
                print(f"Ошибка при парсинге {article_url}: {e}")
                continue

    print(f"Все спарсенные статьи из '{category_name}' записаны в output.txt")
    return all_chunks_for_db
