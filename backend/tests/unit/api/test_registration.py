import pytest
import requests

from ..conftest import BASE_URL, generate_test_users, activated_users


TEST_USERS = generate_test_users(10)


@pytest.mark.parametrize("username, password", TEST_USERS)
def test_register_positive(username, password):
    """
    Позитивный сценарий регистрации - 200 код ответа
    
    Пред-условия: Пользователь не зарегистрирован в системе или не активирован
    Шаги:
    1. Сгенерировать 10 уникальных тестовых username и password через генератор
    2. Ввести в поле запроса username и password по формату тела запроса
    
    Ожидаемый результат:
    Статус код 200 с телом ответа:
    {
      "detail": "Account created successfully",
      "email": "youremail@email.com"
    }
    """
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
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
    assert "detail" in response_data, "В ответе отсутствует поле 'detail'"
    assert "email" in response_data, "В ответе отсутствует поле 'email'"
    assert response_data["detail"] == "Account created successfully", (
        f"Неверное сообщение в поле 'detail': {response_data['detail']}"
    )
    assert response_data["email"] == username, (
        f"Email в ответе не совпадает с переданным username. "
        f"Ожидался: {username}, получен: {response_data['email']}"
    )


@pytest.mark.parametrize("username, password", activated_users if activated_users else [("skip", "skip")])
def test_register_negative(username, password):
    """Негативный сценарий регистрации - 409 код ответа
    
    Пред-условия: Пользователь зарегистрирован в системе и активирован
    Шаги:
    1. Взять username и password из заранее определённого списка зарегистрированных и активированных пользователей из файла .env (список activated_users)
    2. Ввести в поле запроса username и password по формату тела запроса из списка activated_users
    
    Ожидаемый результат:
    Статус код 409 с телом ответа:
    {
      "detail": "Account already exists"
    }
    """
    if username == "skip" and password == "skip":
        pytest.skip("ACTIVATED_USERS не задан в .env файле")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 409, (
        f"Ожидался статус 409, получен {response.status_code}. "
        f"Ответ: {response.text}"
    )

    response_data = response.json()
    assert "detail" in response_data, "В ответе отсутствует поле 'detail'"
    assert response_data["detail"] == "Account already exists", (
        f"Неверное сообщение в поле 'detail': {response_data['detail']}"
    )
