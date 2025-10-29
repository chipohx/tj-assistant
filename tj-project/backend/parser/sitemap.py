import os
import requests
from bs4 import BeautifulSoup

sitemap_url: str = 'https://t-j.ru/sitemap.xml'

try:
    response = requests.get(sitemap_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'xml')
    with open('sitemap.xml','w',encoding='UTF-8') as file:
        file.write(str(soup))

    categories = soup.find_all('loc')

    for category in categories:
        category_url = category.text

        try:
            response = requests.get(category_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'xml')

            name = category_url.replace('https://t-j.ru/','')
            folder_path = "categories"
            file_path = os.path.join(folder_path, name)

            print(name)

            with open(file_path, 'w', encoding='UTF-8') as file:
                file.write(str(soup))

        except Exception as err:
            print(f'Ошибка запроса: {err}')

except Exception as err:
    print(f'Ошибка запроса: {err}')






