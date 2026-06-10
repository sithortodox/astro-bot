from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Text, ForeignKey, Integer, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    zodiac_sign: Mapped[str | None] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    birth_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    birth_place: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Subscription
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_until: Mapped[str | None] = mapped_column(String(30), nullable=True)
    subscription_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Rate limiting
    daily_requests: Mapped[int] = mapped_column(Integer, default=0)
    last_request_date: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Admin
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Stats
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    history: Mapped[list["History"]] = relationship(back_populates="user")
    payments: Mapped[list["Payment"]] = relationship(back_populates="user")


class History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    command: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="history")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    payment_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    product: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="payments")
