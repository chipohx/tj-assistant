import pytest
import requests

from ..conftest import BASE_URL, user_with_token_parametrized
from ..utils.generator_data import generate_token


# Генерируем невалидные токены для негативного сценария
NEGATIVE_TOKENS = [generate_token() for _ in range(10)]


def test_users_me_positive(user_with_token_parametrized):
    """
    Позитивный сценарий получения информации о пользователе - 200 код ответа
    
    Пред-условия: Пользователь зарегистрирован, активирован и имеет валидный токен авторизации
    Шаги:
    1. Получить актуальный токен авторизации через /api/auth/login для пользователя из ACTIVATED_USERS_LOGIN
    2. Отправить GET запрос с заголовком Authorization: Bearer <актуальный_токен>
    3. Сравнить возвращенный email с соответствующим email из ACTIVATED_USERS_LOGIN
    
    Ожидаемый результат:
    Статус код 200 с телом ответа:
    {
      "email": "email@example.com",
      ...
    }
    Email в ответе должен соответствовать email из ACTIVATED_USERS_LOGIN для данного токена
    """
    email, token = user_with_token_parametrized
    
    response = requests.get(
        f"{BASE_URL}/api/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 200, (
        f"Ожидался статус 200, получен {response.status_code}. "
        f"Ответ: {response.text}"
    )
    
    response_data = response.json()
    assert "email" in response_data, f"В ответе отсутствует поле 'email'. Доступные поля: {list(response_data.keys())}"
    assert response_data["email"] == email, (
        f"Email в ответе не совпадает с ожидаемым. "
        f"Ожидался: {email}, получен: {response_data['email']}"
    )


@pytest.mark.parametrize("token", NEGATIVE_TOKENS)
def test_users_me_negative(token):
    """
    Негативный сценарий получения информации о пользователе - 401 код ответа
    
    Пред-условия: Используется невалидный или сгенерированный токен
    Шаги:
    1. Сгенерировать невалидные токены через генератор
    2. Отправить GET запрос с заголовком Authorization: Bearer <невалидный_токен>
    
    Ожидаемый результат:
    Статус код 401 с телом ответа:
    {
      "detail": "Not authenticated"
    }
    """
    response = requests.get(
        f"{BASE_URL}/api/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 401, (
        f"Ожидался статус 401, получен {response.status_code}. "
        f"Ответ: {response.text}"
    )
    
    response_data = response.json()
    assert "detail" in response_data, "В ответе отсутствует поле 'detail'"
    assert "Not authenticated" in response_data["detail"] or "Could not validate credentials" in response_data["detail"], (
        f"Неверное сообщение об ошибке: {response_data['detail']}"
    )

