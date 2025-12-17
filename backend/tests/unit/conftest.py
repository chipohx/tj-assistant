import pytest
import os
import requests

from dotenv import load_dotenv

from .utils.generator_data import generate_email, generate_password

BASE_URL = "http://localhost:8000"

load_dotenv()  


def parsing_data(raw_users):
    """Парсит строку формата 'email:password,email:password' в список кортежей"""
    users = []
    if not raw_users or not raw_users.strip():
        return users
    
    for pair in raw_users.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if ":" in pair:
            email, password = pair.split(":", 1)  
            users.append((email.strip(), password.strip()))
    return users

raw_activated_users_register = os.getenv("ACTIVATED_USERS", "")
activated_users = parsing_data(raw_activated_users_register)

raw_activated_users_login = os.getenv("ACTIVATED_USERS_LOGIN", "")
activated_users_login = parsing_data(raw_activated_users_login)


def generate_test_users(count: int = 10):
    """Генерирует список уникальных тестовых пользователей"""
    users = []
    emails = set()
    
    for _ in range(count):
        email = generate_email()
        while email in emails:
            email = generate_email()
        emails.add(email)
        
        password = generate_password()
        users.append((email, password))
    
    return users


def get_auth_token(email: str, password: str) -> str:
    """Получает актуальный токен авторизации через /api/auth/login"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": email,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        raise ValueError(f"Не удалось получить токен для {email}: {response.status_code} - {response.text}")
    
    response_data = response.json()
    return response_data["access_token"]


@pytest.fixture(scope="function")
def user_with_token():
    """Фикстура для получения актуального токена для пользователя из ACTIVATED_USERS_LOGIN"""
    if not activated_users_login:
        pytest.skip("ACTIVATED_USERS_LOGIN не задан в .env файле")
    
    email, password = activated_users_login[0]
    
    try:
        token = get_auth_token(email, password)
        yield (email, token)
    except Exception as e:
        pytest.skip(f"Не удалось получить токен: {e}")


@pytest.fixture(scope="function", params=activated_users_login if activated_users_login else [])
def user_with_token_parametrized(request):
    """Фикстура для параметризации тестов с актуальными токенами из ACTIVATED_USERS_LOGIN"""
    if not activated_users_login:
        pytest.skip("ACTIVATED_USERS_LOGIN не задан в .env файле")
    
    email, password = request.param
    
    try:
        token = get_auth_token(email, password)
        yield (email, token)
    except Exception as e:
        pytest.skip(f"Не удалось получить токен для {email}: {e}")

