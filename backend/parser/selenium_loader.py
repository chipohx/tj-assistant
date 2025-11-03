import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def create_driver():
    options = uc.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = uc.Chrome(options=options)
    return driver


def get_page_source(url: str, driver) -> str:
    try:
        # if not load_cookies_from_file(driver, "cookies.json"):
        # exit()

        driver.get(url)
        # Обновляем страницу, чтобы куки вступили в силу
        driver.refresh()

        # Ждем, пока появится основной контент
        wait = WebDriverWait(driver, 30)
        # Ждем появления элемента загрузки тега body
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-app-name='view-v2']")
            )
        )

        # Получаем HTML-код страницы после выполнения JS и с куки
        html_content = driver.page_source

        """if "qauth.js" in html_content and len(html_content) < 1500:
            print("Ошибка: Куки могли просрочиться, надо заново запустить bypass.py")
            return """

        return html_content

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return ""
