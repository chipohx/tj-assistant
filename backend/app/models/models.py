from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, ForeignKey
from datetime import datetime

class Base(DeclarativeBase):
  pass

class User(Base):
  __tablename__ = "user"

  id: Mapped[int] = mapped_column(primary_key = True)
  email: Mapped[str] = mapped_column(String)
  password: Mapped[str] = mapped_column(String)
  created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class Chat(Base):
  __tablename__ = "chat"

  id: Mapped[int] = mapped_column(primary_key = True)
  title: Mapped[str] = mapped_column(String)
  created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
  updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
  user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))