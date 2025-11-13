from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from sqlalchemy.orm import Session
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    InvalidTokenError,
    DecodeError,
)
from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel

from app.api.schemas.schemas import UserSchema, NewUser
from app.database.session import get_db
from app.models.models import User

SECRET_KEY = "c5a21c5337abedebeffc85f52cf399579224637567d8121095f58a63cc27f285"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 360

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
password_hash = PasswordHash.recommended()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # pwdlib.exceptions.UnknownHashError
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def get_user(
    username: str,
):
    db_gen = get_db()
    db = next(db_gen)
    user = db.query(User).filter(User.email == username).first()
    db.close()
    return user


def authenticate_user(db: Session, username: str, password: str):
    user: User = db.query(User).filter(User.email == username).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """oauth2_scheme возвращает ошибку 401 Not authenticated автоматически
    если заголовок запроса не содержит токена авторазации, соответствие токена
    выданному системой проверяется ниже"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
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


@router.post("/auth/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    """Авторизует пользователя в системе

    Проверяет корректность пароля и почты
    Если данные корректны, выдает токен авторизации
    """

    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me")
async def read_users_me(current_user: Annotated[UserSchema, Depends(get_current_user)]):
    """Скрыто принимает параметр request, который должен содержать заголовок Authorization"""

    return current_user


@router.post("/auth/register")
async def register():
    """Регистрация нового пользователя"""

    return


@router.post("/create-new-user")
async def create_example_user(user: NewUser, db: Session = Depends(get_db)):
    """Создание нового пользователя

    Добавлял для теста авторизации
    """

    example = User(
        email=user.username,
        password=get_password_hash(user.plain_password),
    )
    db.add(example)
    db.commit()
    db.refresh(example)
    return {"message": "User created", "user_id": example.id}
