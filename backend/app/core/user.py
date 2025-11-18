from typing import Annotated

from sqlalchemy.orm import Session
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    InvalidTokenError,
    DecodeError,
)
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.secuirity import verify_password, decode_token
from app.api.schemas.schemas import TokenData
from app.database.session import get_db
from app.models.models import User

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_user(
    username: str,
):
    """Получаем объект пользователя в БД"""

    db_gen = get_db()
    db = next(db_gen)
    user = db.query(User).filter(User.email == username).first()
    db.close()
    return user


def authenticate_user(db: Session, username: str, password: str):
    """Проверяет пароль и email пользователя,
    а также факт верификации аккауета
    """

    user: User = db.query(User).filter(User.email == username).first()
    if not user:
        return False
    if not user.activated:
        raise HTTPException(status_code=403, detail="Unverified user")
    if not verify_password(password, user.password):
        return False
    return user


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """oauth2_scheme возвращает ошибку 401 Not authenticated автоматически
    если заголовок запроса не содержит токена авторазации, соответствие токена
    выданному системой проверяется ниже"""

    try:
        username = decode_token(token)
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except DecodeError:
        raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    except Exception as e:
        print(f"JWT error: {e}")
        raise credentials_exception

    user = get_user(username=token_data.username)

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
