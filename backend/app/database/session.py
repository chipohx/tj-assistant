# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

# from app.models.models import Base
# from app.core.config import settings

# engine = create_engine(settings.DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)

# Base.metadata.create_all(bind=engine)


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
