from datetime import datetime
import uuid
from enum import Enum as PyEnum

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, ForeignKey, Enum, Boolean, func
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    email: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    activated: Mapped[bool] = mapped_column(Boolean, default=False)


class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    title: Mapped[str] = mapped_column(String)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"))


class Role(PyEnum):
    USER = "user"
    SYSTEM = "system"


class Message(Base):
    __tablename__ = "message"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat.id"))
    content: Mapped[str] = mapped_column(String)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER)
