from __future__ import annotations

from datetime import date, datetime, timezone
from sqlalchemy import select, func

from bot.database import async_session
from bot.models import User


class UserRepo:
    @staticmethod
    async def get_by_telegram_id(telegram_id: int) -> User | None:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create(telegram_id: int, username: str | None = None, first_name: str | None = None) -> User:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            return user

    @staticmethod
    async def update(telegram_id: int, **kwargs) -> User | None:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def increment_requests(telegram_id: int) -> None:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.daily_requests += 1
                user.total_requests += 1
                today = date.today()
                if user.last_request_date != today:
                    user.daily_requests = 1
                    user.last_request_date = today
                await session.commit()

    @staticmethod
    async def reset_daily_requests(telegram_id: int) -> None:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.daily_requests = 0
                await session.commit()

    @staticmethod
    async def count_total() -> int:
        async with async_session() as session:
            return await session.scalar(select(func.count(User.id))) or 0

    @staticmethod
    async def count_premium() -> int:
        async with async_session() as session:
            return await session.scalar(
                select(func.count(User.id)).where(User.is_premium)
            ) or 0

    @staticmethod
    async def count_active_today() -> int:
        async with async_session() as session:
            return await session.scalar(
                select(func.count(User.id)).where(User.last_request_date == date.today())
            ) or 0

    @staticmethod
    async def sum_total_requests() -> int:
        async with async_session() as session:
            return await session.scalar(select(func.sum(User.total_requests))) or 0

    @staticmethod
    async def list_recent(limit: int = 20) -> list[User]:
        async with async_session() as session:
            result = await session.execute(
                select(User).order_by(User.created_at.desc()).limit(limit)
            )
            return list(result.scalars().all())

    @staticmethod
    async def set_premium(telegram_id: int, until: datetime, subscription_type: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return False
            user.is_premium = True
            user.premium_until = until
            user.subscription_type = subscription_type
            await session.commit()
            return True

    @staticmethod
    async def expire_premium(telegram_id: int) -> None:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user and user.is_premium:
                if user.premium_until and datetime.now(timezone.utc) > user.premium_until.replace(tzinfo=timezone.utc):
                    user.is_premium = False
                    user.premium_until = None
                    await session.commit()
