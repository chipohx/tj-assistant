import os
from pathlib import Path

from bs4 import BeautifulSoup
import requests

current_file = Path(__file__)
current_dir = current_file.parent
categories_path = current_dir / "categories"


def parse_article(url: str) -> dict:
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

    if response.status_code != 200:
       return f"Status code: {response.status_code}"
        
    html_content = response.text

    article_data = {}

    authors = []

    soup = BeautifulSoup(html_content, 'html.parser')

    for script in soup.find_all('script'):
        script.decompose()
    
    text_parts = []

    # Заголовок статьи
    article_data['title'] = soup.find('h1').get_text().replace('\xad', '').replace('\xa0', ' ')
    
    # Текст статьи
    main_content = soup.find('div', {'data-app-name': 'view-v2'})
    
    if main_content:
      # Парсим страницы авторов
      for author in soup.find_all('div',class_='_author_ab553_6'):
        name = author.find('p', {'data-bold':'true'}).get_text(strip=True)
        author_page = author.find('a')['href']
        authors.append(author_page)

      # Авторы статьи
      article_data['authors'] = authors

      text_by_headers = []
      text_parts = []

      # Парсим заголовки второго уровня и параграфы (текст статей)
      for element in main_content.find_all(['h2','h3','h4','p']):
            
        # Исключаем из текста авторов и вторичную информацию
        if element.has_attr('data-grade'):
          if element['data-grade'] in ['medium','secondary']:
            continue
            
        # После каждого нового заголовка записываем и сбрасываем накопленный текст
        if element.name == 'h2':
          text = ' '.join(text_parts).strip()
          if text:
            text_by_headers.append(text)
          text_parts = []
          
        element_text = element.get_text(separator=' ').strip().replace('\xad', '').replace('\xa0', ' ')

        if element_text:
            text_parts.append(element_text)

      # Записываем оставшиеся части
      if text_parts:
        text_by_headers.append(' '.join(text_parts).strip())

      article_data['text'] = text_by_headers

    return article_data


def get_category_urls(category_filename: str) -> str:
  file_path = categories_path / category_filename

  with open(file_path, 'r', encoding='utf-8') as file:
      category_urls = []

      content = file.read()
      soup = BeautifulSoup(content, 'xml')
      articles = soup.find_all('loc')

      for article in articles:
        article_url = article.text
        category_urls.append(article_url)

      return category_urls


def parse_category(category_filename: str, articles_to_parse: int) -> list:
  category_data = []
  category_urls = get_category_urls(category_filename)

  for article_url_i in range(articles_to_parse):
      article_url = category_urls[article_url_i]
      try:
        article_data = parse_article(article_url)
        category_data.append(article_data)
        print(f"Successfully parsed: {article_url}")
      except Exception as e:
        print(f"Error parsing {article_url}: {e}")
        continue 
  return category_data


def get_category_filenames() -> list:
  return os.listdir(categories_path)


