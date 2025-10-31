from fastapi import FastAPI

from app.database.session import SessionLocal, engine
from app.models.models import Base

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

@app.get("/")
async def index():
    return "Hello, World!"
