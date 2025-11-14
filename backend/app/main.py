from fastapi import FastAPI
from app.api.endpoints import chat, auth


app = FastAPI()

app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
