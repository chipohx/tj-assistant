from typing import Annotated

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.secuirity import verify_password, decode_token, get_password_hash
from app.database.session_async import get_db
from app.models.models import User

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_user(db: AsyncSession, email: str, password: str):
    try:
        new_user = User(email=email, password=get_password_hash(password))
        db.add(new_user)

        await db.commit()
        await db.refresh(new_user)
    except Exception as e:
        await db.rollback()
        print(f"Не удалось создать пользователя: {e}")


async def get_user(username: str, db: AsyncSession) -> User | None:
    """Получаем объект пользователя в БД"""

    # db_gen = Depends(get_db)
    # db = next(db_gen)

    user: User = await db.scalar(select(User).where(User.email == username))
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str):
    """Проверяет пароль и email пользователя,
    а также факт верификации аккаунта
    """

    user = await get_user(username, db)
    if not user:
        return False
    if not user.activated:
        raise HTTPException(status_code=403, detail="Unverified user")
    if not verify_password(password, user.password):
        return False
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: AsyncSession = Depends(get_db)
):
    """oauth2_scheme возвращает ошибку 401 Not authenticated автоматически
    если заголовок запроса не содержит токена авторизации"""

    # ВРЕМЕННОЕ РЕШЕНИЕ: для тестирования без реальной авторизации
    # Проверяем, есть ли пользователь в базе
    if token == "example-token":
        # Ищем пользователя в базе (создадим его если нет)
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            # Создаем тестового пользователя для разработки
            from app.core.secuirity import get_password_hash
            user = User(
                email="test@example.com",
                password=get_password_hash("testpassword"),
                activated=True  # Активируем для тестирования
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

#     try:
#         username = decode_token(token)
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except ExpiredSignatureError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token has expired",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     except DecodeError:
#         raise credentials_exception
#     except InvalidTokenError:
#         raise credentials_exception
#     except Exception as e:
#         print(f"JWT error: {e}")
#         raise credentials_exception

#     user = get_user(db, username=token_data.username)
    username = decode_token(token)
    user = await get_user(username, db)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Проверяем верификацию аккаунта"""
    if not current_user.activated:
        raise HTTPException(status_code=403, detail="Unverified user")
    return current_user