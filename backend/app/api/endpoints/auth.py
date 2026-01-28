from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.schemas import Token, UserSchema
from app.core.secuirity import create_token, decode_token
from app.core.user import (
    authenticate_user,
    get_current_active_user,
    get_user,
    create_user,
)
from app.database.session_async import get_db
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
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Авторизует пользователя в системе

    Проверяет корректность пароля и почты
    Если данные корректны, выдает токен авторизации
    """

    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    access_token = create_token(data={"sub": user.email})

    return Token(access_token=access_token, token_type="bearer")


@router.post("/auth/register")
async def register(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    """Создает пользователя в бд

    Перед этим проверяет существование его в бд,
    а также факт верификации аккаунта пользователя"""

    user: User = await get_user(form_data.username, db)
    if user and user.activated:
        raise HTTPException(status_code=409, detail="Account already exists")

    await create_user(db, form_data.username, form_data.password)

    email = form_data.username
    await send_verification_email(email)
    return {"detail": "Account created successfully", "email": email}

@router.post("/auth/test-register")
async def test_register(db: Session = Depends(get_db)):
    """Создает тестового пользователя для разработки"""

    from app.core.secuirity import get_password_hash

    test_user = db.query(User).filter(User.email == "test@test.com").first()
    if not test_user:
        new_user = User(
            email="test@test.com",
            password=get_password_hash("password123"),
            activated=True
        )
        db.add(new_user)
        db.commit()
        return {"detail": "Test user created", "email": "test@test.com"}
    return {"detail": "Test user already exists"}


@router.post("/auth/request-verify-token", status_code=status.HTTP_202_ACCEPTED)
async def request_verify_token(
    email: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)
):
    """Заново посылает уведомление для верификации на почту"""
    user: User = await get_user(email, db)
    if user:
        if not user.activated:
            await send_verification_email(email)
        else:
            # TODO Заменить на логгер
            print("Пользователь уже верифицирован")
    return None


@router.get("/auth/verify-email", status_code=status.HTTP_200_OK)
async def verify_account(token: str, db: AsyncSession = Depends(get_db)):
    """Принимает токен верификации из письма
    и активирует аккаунт пользователя"""

    email = decode_token(token)

    user: User = await get_user(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.activated:
        raise HTTPException(status_code=400, detail="Email already verified")

    try:
        user.activated = True
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to activate account")

    return {"message": "Email successfully verified"}
