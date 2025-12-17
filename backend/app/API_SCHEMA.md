# API Schema Documentation

Документация всех API эндпоинтов приложения.

## Базовый URL
```
http://localhost:8000/api
```

## Аутентификация

Большинство эндпоинтов требуют аутентификации через Bearer токен в заголовке `Authorization`:
```
Authorization: Bearer <access_token>
```

---

## Эндпоинты аутентификации (Auth)

### 1. Получить информацию о текущем пользователе

**Метод:** `GET`  
**Путь:** `/api/users/me`  
**Требует аутентификации:** Да

#### Описание
Возвращает информацию о текущем аутентифицированном пользователе.

#### Заголовки запроса
```
Authorization: Bearer <access_token>
```

#### Параметры запроса
Нет

#### Тело запроса
Нет

#### Ответы

**200 OK** - Успешный запрос
```json
{
  "username": "user@example.com"
}
```

**401 Unauthorized** - Токен отсутствует или невалиден
```json
{
  "detail": "Not authenticated"
}
```

#### Как работает
1. Извлекает токен из заголовка `Authorization`
2. Декодирует токен и получает email пользователя
3. Проверяет, что пользователь существует и активен
4. Возвращает схему пользователя

---

### 2. Авторизация (логин)

**Метод:** `POST`  
**Путь:** `/api/auth/login`  
**Требует аутентификации:** Нет

#### Описание
Авторизует пользователя в системе. Проверяет корректность пароля и email. Если данные корректны, выдает токен авторизации.

#### Заголовки запроса
```
Content-Type: application/x-www-form-urlencoded
```

#### Параметры запроса
Форма данных (OAuth2PasswordRequestForm):
- `username` (string, required) - Email пользователя
- `password` (string, required) - Пароль пользователя

#### Тело запроса
```
username=user@example.com&password=password123
```

#### Ответы

**200 OK** - Успешная авторизация
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**400 Bad Request** - Неверные учетные данные
```json
{
  "detail": "Invalid username or password"
}
```

#### Как работает
1. Принимает email и пароль из формы
2. Проверяет существование пользователя в БД
3. Сверяет хеш пароля с сохраненным
4. Если данные корректны, создает JWT токен с email в payload
5. Возвращает токен доступа

---

### 3. Регистрация нового пользователя

**Метод:** `POST`  
**Путь:** `/api/auth/register`  
**Требует аутентификации:** Нет

#### Описание
Создает нового пользователя в базе данных. Перед созданием проверяет существование пользователя в БД и факт верификации аккаунта. После регистрации отправляет письмо для верификации email.

#### Заголовки запроса
```
Content-Type: application/x-www-form-urlencoded
```

#### Параметры запроса
Форма данных (OAuth2PasswordRequestForm):
- `username` (string, required) - Email пользователя
- `password` (string, required) - Пароль пользователя

#### Тело запроса
```
username=test@gmail.com&password=123123
```

**Пример с curl:**
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@gmail.com&password=123123"
```

**Пример с Python (requests):**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/register",
    data={
        "username": "test@gmail.com",
        "password": "123123"
    }
)
```

#### Ответы

**200 OK** - Успешная регистрация
```json
{
  "detail": "Account created successfully",
  "email": "user@example.com"
}
```

**409 Conflict** - Аккаунт уже существует и активирован
```json
{
  "detail": "Account already exists"
}
```

#### Как работает
1. Принимает email и пароль из формы
2. Проверяет, существует ли пользователь с таким email
3. Если пользователь существует и активирован - возвращает ошибку 409
4. Если пользователь не существует или не активирован:
   - Хеширует пароль
   - Создает нового пользователя в БД (activated = false)
   - Генерирует токен верификации
   - Отправляет письмо с ссылкой верификации на email
5. Возвращает сообщение об успешной регистрации

---

### 4. Повторная отправка токена верификации

**Метод:** `POST`  
**Путь:** `/api/auth/request-verify-token`  
**Требует аутентификации:** Нет  
**Статус код успеха:** `202 Accepted`

#### Описание
Заново отправляет письмо с токеном верификации на указанный email.

#### Заголовки запроса
```
Content-Type: application/json
```

#### Параметры запроса
Нет

#### Тело запроса
```json
{
  "email": "user@example.com"
}
```

#### Ответы

**202 Accepted** - Письмо отправлено
```json
null
```

#### Как работает
1. Принимает email в теле запроса
2. Генерирует новый токен верификации
3. Отправляет письмо с ссылкой верификации на указанный email
4. Возвращает статус 202 Accepted

---

### 5. Верификация email

**Метод:** `GET`  
**Путь:** `/api/auth/verify-email`  
**Требует аутентификации:** Нет

#### Описание
Принимает токен верификации из письма и активирует аккаунт пользователя.

#### Заголовки запроса
Нет

#### Параметры запроса
- `token` (string, required) - Токен верификации из письма

#### Тело запроса
Нет

#### Пример запроса
```
GET /api/auth/verify-email?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Ответы

**200 OK** - Email успешно верифицирован
```json
{
  "message": "Email successfully verified"
}
```

**400 Bad Request** - Невалидный или истекший токен
```json
{
  "detail": "Invalid token"
}
```
или
```json
{
  "detail": "Token expired"
}
```
или
```json
{
  "detail": "Email already verified"
}
```

**404 Not Found** - Пользователь не найден
```json
{
  "detail": "User not found"
}
```

**500 Internal Server Error** - Ошибка при активации аккаунта
```json
{
  "detail": "Failed to activate account"
}
```

#### Как работает
1. Принимает токен верификации из query параметра
2. Декодирует токен и извлекает email
3. Обрабатывает возможные ошибки токена (невалидный, истекший)
4. Ищет пользователя по email в БД
5. Проверяет, не активирован ли уже аккаунт
6. Устанавливает `activated = true` для пользователя
7. Сохраняет изменения в БД
8. Возвращает сообщение об успешной верификации

---

## Эндпоинты чата (Chat)

### 6. Создать новый чат

**Метод:** `POST`  
**Путь:** `/api/new-chat`  
**Требует аутентификации:** Да

#### Описание
Создает новый чат для текущего пользователя с заголовком "Новый чат".

#### Заголовки запроса
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Параметры запроса
Нет

#### Тело запроса
Нет

#### Ответы

**200 OK** - Чат успешно создан
```json
{
  "chat_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**401 Unauthorized** - Токен отсутствует или невалиден
```json
{
  "detail": "Not authenticated"
}
```

#### Как работает
1. Проверяет аутентификацию пользователя
2. Создает новый чат в БД с заголовком "Новый чат"
3. Связывает чат с текущим пользователем
4. Возвращает UUID созданного чата

---

### 7. Отправить сообщение в чат

**Метод:** `POST`  
**Путь:** `/api/chat`  
**Требует аутентификации:** Да

#### Описание
Отправляет сообщение пользователя в чат и получает ответ от LLM сервиса. Если `chat_id` не указан, создается новый чат. Сохраняет как сообщение пользователя, так и ответ системы в БД.

#### Заголовки запроса
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

#### Параметры запроса
Нет

#### Тело запроса
```json
{
  "content": "Привет, как дела?",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000"  // опционально
}
```

**Схема ChatRequest:**
- `content` (string, required) - Текст сообщения пользователя
- `chat_id` (UUID, optional) - ID существующего чата. Если не указан, создается новый чат

#### Ответы

**200 OK** - Сообщение отправлено и получен ответ
```json
{
  "message_id": "660e8400-e29b-41d4-a716-446655440001",
  "content": "Привет! У меня всё отлично, спасибо!",
  "timestamp": "2024-01-15T10:30:00",
  "chat_created": "550e8400-e29b-41d4-a716-446655440000"  // только если создан новый чат
}
```

**401 Unauthorized** - Токен отсутствует или невалиден
```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error** - LLM сервис недоступен
```json
{
  "detail": "LLM service unreachable"
}
```

**502 Bad Gateway** - Ошибка при генерации ответа
```json
{
  "detail": "Failed generating response"
}
```
или
```json
{
  "detail": "Invalid JSON from LLM service"
}
```
или
```json
{
  "detail": "Empty response from LLM service"
}
```

**503 Service Unavailable** - LLM сервис не прошел health check
```json
{
  "detail": "LLM service health check failed: ..."
}
```

#### Как работает
1. Проверяет аутентификацию пользователя
2. Если `chat_id` не указан:
   - Создает новый чат с заголовком из первых 30 символов сообщения
   - Использует ID созданного чата
3. Сохраняет сообщение пользователя в БД с ролью `USER`
4. Выполняет health check LLM сервиса (GET http://localhost:8001/health)
5. Если health check успешен, отправляет запрос к LLM сервису (POST http://localhost:8001/llm_response)
6. Получает ответ от LLM сервиса
7. Сохраняет ответ системы в БД с ролью `SYSTEM`
8. Возвращает ответ с ID сообщения, содержимым, временем и ID созданного чата (если был создан)

---

### 8. Получить список чатов (сессий)

**Метод:** `GET`  
**Путь:** `/api/chat`  
**Требует аутентификации:** Нет (TODO: добавить авторизацию)

#### Описание
Возвращает все чаты (сессии) пользователя.

#### Заголовки запроса
```
Authorization: Bearer <access_token>  // TODO: будет обязательным
```

#### Параметры запроса
Нет

#### Тело запроса
Нет

#### Ответы

**200 OK** - Список чатов
```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Новый чат",
      "created": "2024-01-15T10:00:00",
      "updated": "2024-01-15T10:30:00"
    }
  ],
  "total": 1
}
```

**Примечание:** Эндпоинт в разработке, текущая реализация возвращает пустую строку.

#### Как работает
1. TODO: Проверка аутентификации пользователя
2. TODO: Получение всех чатов пользователя из БД
3. TODO: Форматирование ответа согласно схеме SessionListResponse
4. Возвращает список сессий с метаданными

---

## Схемы данных

### UserSchema
```json
{
  "username": "string"  // Email пользователя
}
```

### Token
```json
{
  "access_token": "string",
  "token_type": "string"  // Обычно "bearer"
}
```

### ChatRequest
```json
{
  "content": "string",
  "chat_id": "uuid | null"  // Опционально
}
```

### ChatResponse
```json
{
  "message_id": "uuid",
  "content": "string",
  "timestamp": "datetime",
  "chat_created": "string"  // UUID чата, если был создан новый
}
```

### NewChat
```json
{
  "chat_id": "uuid"
}
```

### SessionResponse
```json
{
  "id": "uuid",
  "title": "string",
  "created": "datetime",
  "updated": "datetime"
}
```

### SessionListResponse
```json
{
  "sessions": [
    {
      "id": "uuid",
      "title": "string",
      "created": "datetime",
      "updated": "datetime"
    }
  ],
  "total": "integer"
}
```

---

## Коды состояния HTTP

- **200 OK** - Успешный запрос
- **202 Accepted** - Запрос принят к обработке
- **400 Bad Request** - Неверный запрос (невалидные данные, токен и т.д.)
- **401 Unauthorized** - Требуется аутентификация
- **404 Not Found** - Ресурс не найден
- **409 Conflict** - Конфликт (например, пользователь уже существует)
- **500 Internal Server Error** - Внутренняя ошибка сервера
- **502 Bad Gateway** - Ошибка внешнего сервиса (LLM)
- **503 Service Unavailable** - Сервис временно недоступен

---

## Зависимости от внешних сервисов

### LLM Service
- **URL:** `http://localhost:8001`
- **Health Check:** `GET /health`
- **Endpoint:** `POST /llm_response`
- **Используется в:** `/api/chat`

### Email Service (SMTP)
- Используется для отправки писем верификации
- **Используется в:** `/api/auth/register`, `/api/auth/request-verify-token`

---

## Примечания

1. Все UUID представлены в стандартном формате UUID v4
2. Даты и время представлены в формате ISO 8601
3. Пароли никогда не возвращаются в ответах API
4. Токены JWT имеют срок действия (expiration time)
5. Эндпоинт `/api/chat` (GET) находится в разработке и требует доработки

