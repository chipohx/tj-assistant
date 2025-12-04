from typing import Annotated

from sqlalchemy.orm import Session
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    InvalidTokenError,
    DecodeError,
)
from fastapi import Depends, APIRouter, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm

from app.core.user import (
    authenticate_user,
    get_current_active_user,
)
from app.core.secuirity import get_password_hash, create_token, decode_token
from app.api.schemas.schemas import UserSchema, Token
from app.database.session import get_db
from app.models.models import User
from app.mailing.send_verification_email import send_verification_email

router = APIRouter()


@router.get("/users/me")
async def read_users_me(
    current_user: Annotated[UserSchema, Depends(get_current_active_user)],
):
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
async def register(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """Создает пользователя в бд

    Перед этим проверяет существование его в бд,
    а также факт верификации аккаунта пользователя"""

    db_user = db.query(User).filter(User.email == form_data.username).first()
    if db_user:
        if db_user.activated:
            raise HTTPException(status_code=409, detail="Account already exists")

    new_user = User(
        email=form_data.username, password=get_password_hash(form_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    email = form_data.username
    await send_verification_email(email)
    return {"detail": f"Account created successfully", "email": email}


@router.post("/auth/request-verify-token", status_code=status.HTTP_202_ACCEPTED)
async def request_verify_token(email: str = Body(..., embed=True)):
    """Заново посылает уведомление для верификации на почту"""

    await send_verification_email(email)
    return None


@router.get("/auth/verify-email", status_code=status.HTTP_200_OK)
async def verify_account(token: str, db: Session = Depends(get_db)):
    """Принимает токен верификации из письма
    и активирует аккаунт пользователя"""

    try:
        email = decode_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")
    except DecodeError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.activated:
        raise HTTPException(status_code=400, detail="Email already verified")

    try:
        user.activated = True
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to activate account")

    return {"message": "Email successfully verified"}
