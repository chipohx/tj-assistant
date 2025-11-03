import os

from pathlib import Path
from bs4 import BeautifulSoup

import selenium_loader

current_dir = Path(__file__).parent
categories_path = current_dir / "categories"


def parse_article(url: str) -> dict:
    # Получаем html контент

    driver = selenium_loader.create_driver()

    try:
        """if not selenium_loader.load_cookies_from_file(
            driver, current_dir / "cookies.json"
        ):
            print(f"Не удалось загрузить куки для {url}")
            return {}"""

        html_content = selenium_loader.get_page_source(url, driver)

        if not html_content:
            print(f"Не удалось получить HTML для {url}")
            return {}

        article_data = {}
        authors = []

        soup = BeautifulSoup(html_content, "html.parser")

        # Очищаем от скриптов навсякий
        for script in soup.find_all("script"):
            script.decompose()

        # Находим заголовок статьи
        article_data["title"] = (
            soup.find("h1").get_text().replace("\xad", "").replace("\xa0", " ")
        )

        # Парсим страницы авторов
        for author in soup.find_all("div", class_="_author_ab553_6"):
            author_page = author.find("a")["href"]
            authors.append(author_page)
        # Добавляем в словарь
        article_data["authors"] = authors

        # Находим текст статьи
        main_content = soup.find("div", {"class": "_articleView_davr3_1"})

        if not main_content:
            print("Текст статьи не найден")
            return {}

        found_elements = main_content.find_all("div", {"class": "_container_1k5mq_5"})
        text_by_headers = []
        text_parts = []

        # Парсим все блоки div в main_content
        for element in found_elements:

            """# Пропускаем авторов
            if element.find_all({"class": "_author_ab553_6"}):
                print(f"Пропускаю div, содержащий автора: {element.get_text()[:50]}...")
                continue
            # Пропускаем пропускаем ссылки статьи
            if element.find_all({"class": "_articleRef_1tqyq_5"}):
                print(
                    f"Пропускаю div, содержащий ссылку на статью: {element.get_text()[:50]}..."
                )
                continue"""

            # После каждого нового заголовка записываем и сбрасываем накопленный текст
            if len(element.find_all("h2")) != 0:
                text = " ".join(text_parts).strip()
                if text:
                    text_by_headers.append(text)
                text_parts = []

            element_text = (
                element.get_text(separator=" ")
                .strip()
                .replace("\xad", "")
                .replace("\xa0", " ")
            )

            if element_text:
                text_parts.append(element_text)

        # Записываем оставшиеся части
        if text_parts:
            text = " ".join(text_parts).strip()
            if text:
                text_by_headers.append(text)

        article_data["text"] = text_by_headers

        return article_data

    except Exception as e:
        print(f"Ошибка при парсинге {url}: {e}")
        return {}
    finally:
        print("Закрываю браузер для этой статьи...")
        try:
            driver.quit()
        except Exception as e:
            print(f"Возникла ошибка при закрытии браузера: {e}")


def get_category_urls(category_filename: str) -> str:
    file_path = categories_path / category_filename

    with open(file_path, "r", encoding="utf-8") as file:
        category_urls = []

        content = file.read()
        soup = BeautifulSoup(content, "xml")
        articles = soup.find_all("loc")

        for article in articles:
            article_url = article.text
            category_urls.append(article_url)

        return category_urls


def parse_category(category_filename: str, articles_to_parse: int) -> list:
    category_data = []
    category_urls = get_category_urls(category_filename)

    # Проверка что не хотим распарсить статей больше чем есть
    urls_to_parse = category_urls[:articles_to_parse]

    with open("output.txt", "w", encoding="utf-8") as f:
        for article_url in urls_to_parse:
            try:
                article_data = parse_article(article_url)
                # Проверка что article_data не пустой и содержит текст
                if (
                    article_data
                    and article_data.get("title")
                    and article_data.get("text")
                ):
                    category_data.append(article_data)
                    print(f"Successfully parsed: {article_url}")

                    # Запись в файл
                    f.write(f"--- Статья: {article_data['title']} ---\n")
                    # Записываем текст статьи
                    for text in article_data["text"]:
                        f.write(text)
                        f.write("\n\n")
                    f.write("\n\n" + "=" * 50 + "\n\n")
                else:
                    print(f"Успешный парсинг статьи: (empty result): {article_url}")
            except Exception as e:
                print(f"Ошибка при парсинге {article_url}: {e}")
                continue
    print("Все спарсенные статьи записаны в output.txt")
    return category_data

    """for article_url in urls_to_parse:
        try:
            article_data = parse_article(article_url)
            category_data.append(article_data)
            print(f"Успешный парсинг статьи: {article_url}")
        except Exception as e:
            print(f"Ошибка при парсинге {article_url}: {e}")
            continue
    return category_data"""


def get_category_file_names() -> list:
    return os.listdir(categories_path)


print(parse_category(get_category_file_names()[0], 1))
