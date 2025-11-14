from typing import Annotated

from sqlalchemy.orm import Session
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    InvalidTokenError,
    DecodeError,
)
from fastapi import Depends, APIRouter, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core.secuirity import (
    verify_password,
    get_password_hash,
    create_token,
    decode_access_token,
)
from app.api.schemas.schemas import UserSchema, NewUser, Token, TokenData
from app.database.session import get_db
from app.models.models import User
from app.mailing.send_verification_email import send_verification_email

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


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
        username = decode_access_token(token)
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


@router.get("/users/me")
async def read_users_me(current_user: Annotated[UserSchema, Depends(get_current_user)]):
    """Скрыто принимает параметр request, который должен содержать заголовок Authorization"""

    return current_user


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
        raise HTTPException(status_code=400, detail="Invalid username or password")

    access_token = create_token(data={"sub": user.email})

    return Token(access_token=access_token, token_type="bearer")


@router.post("/auth/register")
async def register(user: NewUser, db: Session = Depends(get_db)):
    """Создает пользователя в бд

    Перед этим проверяет существование его в бд,
    а также факт верификации аккаунта пользователя"""

    db_user = db.query(User).filter(User.email == user.username).first()
    if db_user:
        if db_user.activated:
            raise HTTPException(status_code=409, detail="Account already exists")
        else:
            await send_verification_email(user.username)
            return {"detail": "Verification email resent"}

    new_user = User(
        email=user.username, password=get_password_hash(user.plain_password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    email = user.username
    await send_verification_email(email)
    return {"detail": f"Account created successfully", "email": email}


@router.post("/auth/request-verify-token", status_code=status.HTTP_202_ACCEPTED)
async def request_verify_token(email: str = Body(..., embed=True)):
    """Заново посылает уведомление для верификации на почту"""

    await send_verification_email(email)
    return None
