import pytest
import requests

from ..conftest import BASE_URL, activated_users_login, generate_test_users



@pytest.mark.parametrize("username, password", 
                         activated_users_login if activated_users_login else [("skip", "skip")])
def test_login_positive(username, password):
    """
    Позитивный сценарий авторизации - 200 код ответа
    
    Пред-условия: Пользователь зарегистрирован в системе и активирован
    Шаги:
    1. Взять username и password из заранее определённого списка зарегистрированных и активированных пользователей из ACTIVATED_USERS_LOGIN
    2. Ввести в поле запроса username и password по формату тела запроса
    
    Ожидаемый результат:
    Статус код 200 с телом ответа:
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    """
    if username == "skip" and password == "skip":
        pytest.skip("ACTIVATED_USERS_LOGIN не задан в .env файле")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200, (
        f"Ожидался статус 200, получен {response.status_code}. "
        f"Ответ: {response.text}"
    )
    
    response_data = response.json()
    assert "access_token" in response_data, "В ответе отсутствует поле 'access_token'"
    assert "token_type" in response_data, "В ответе отсутствует поле 'token_type'"
    assert response_data["token_type"] == "bearer", (
        f"Неверное значение в поле 'token_type': {response_data['token_type']}"
    )
    assert len(response_data["access_token"]) > 0, "Токен доступа пустой"


NEGATIVE_TEST_USERS = generate_test_users(10)


@pytest.mark.parametrize("username, password", NEGATIVE_TEST_USERS)
def test_login_negative(username, password):
    """
    Негативный сценарий авторизации - 400 код ответа
    
    Пред-условия: Пользователь не зарегистрирован в системе или неверные учетные данные
    Шаги:
    1. Сгенерировать 10 уникальных тестовых username и password через генератор (пользователи не зарегистрированы)
    2. Ввести в поле запроса username и password по формату тела запроса
    
    Ожидаемый результат:
    Статус код 400 с телом ответа:
    {
      "detail": "Invalid username or password"
    }
    """
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 400, (
        f"Ожидался статус 400, получен {response.status_code}. "
        f"Ответ: {response.text}"
    )
    
    response_data = response.json()
    assert "detail" in response_data, "В ответе отсутствует поле 'detail'"
    assert response_data["detail"] == "Invalid username or password", (
        f"Неверное сообщение в поле 'detail': {response_data['detail']}"
    )

