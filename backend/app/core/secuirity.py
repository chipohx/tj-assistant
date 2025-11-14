import jwt
from datetime import datetime, timezone, timedelta
from pwdlib import PasswordHash
from pydantic import BaseModel

SECRET_KEY = "c5a21c5337abedebeffc85f52cf399579224637567d8121095f58a63cc27f285"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 360

password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # pwdlib.exceptions.UnknownHashError
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def create_token(data: dict):
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    return username
