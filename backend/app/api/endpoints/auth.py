from datetime import datetime
from typing import Annotated

from fastapi import Depends, APIRouter, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.schemas.schemas import UserSchema
from app.database.session import get_db
from app.models.models import User

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/auth/register")
async def register():
    """Регистрация нового пользователя"""

    return


@router.post("/auth/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Авторизует пользователся в системе

    Выдает токен авторизации
    """

    return {"access_token": "", "token_type": "bearer"}


@router.get("/users/me")
async def read_users_me(current_user: Annotated[UserSchema, Depends()]):
    return current_user
