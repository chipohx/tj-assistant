from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.schemas.schemas import Token, UserSchema
from app.core.secuirity import create_token, decode_token, get_password_hash
from app.core.user import authenticate_user, get_current_active_user
from app.database.session import get_db
from app.mailing.send_verification_email import send_verification_email
from app.models.models import User


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
    if db_user and db_user.activated:
        raise HTTPException(status_code=409, detail="Account already exists")

    new_user = User(
        email=form_data.username, password=get_password_hash(form_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    email = form_data.username
    await send_verification_email(email)
    return {"detail": "Account created successfully", "email": email}


@router.post("/auth/request-verify-token", status_code=status.HTTP_202_ACCEPTED)
async def request_verify_token(
    email: str = Body(..., embed=True), db: Session = Depends(get_db)
):
    """Заново посылает уведомление для верификации на почту"""
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        if not db_user.activated:
            await send_verification_email(email)
        else:
            # TODO Заменить на логгер
            print("Пользователь уже верифицирован")
    return None


@router.get("/auth/verify-email", status_code=status.HTTP_200_OK)
async def verify_account(token: str, db: Session = Depends(get_db)):
    """Принимает токен верификации из письма
    и активирует аккаунт пользователя"""

    email = decode_token(token)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.activated:
        raise HTTPException(status_code=400, detail="Email already verified")

    try:
        user.activated = True
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to activate account")

    return {"message": "Email successfully verified"}
