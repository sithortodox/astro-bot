from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy import select
from datetime import date

from bot.database import async_session
from bot.models import User
from bot.services.payment_service import is_premium


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            telegram_id = event.from_user.id

            async with async_session() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == telegram_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    user = User(
                        telegram_id=telegram_id,
                        username=event.from_user.username,
                        first_name=event.from_user.first_name,
                    )
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)

                data["db_user"] = user

        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, max_free_requests: int = 1):
        self.max_free_requests = max_free_requests
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            user: User = data.get("db_user")
            if not user:
                return await handler(event, data)

            premium = await is_premium(event.from_user.id)
            if premium:
                user.daily_requests = 0
                return await handler(event, data)

            today = date.today().isoformat()

            if user.last_request_date != today:
                user.daily_requests = 0
                user.last_request_date = today

            if user.daily_requests >= self.max_free_requests:
                await event.answer(
                    "\u26a0\ufe0f Daily limit reached!\n\n"
                    "You've used all free requests for today.\n"
                    "Upgrade to Premium for unlimited access:\n"
                    "/premium"
                )
                return

            user.daily_requests += 1
            user.total_requests += 1

            async with async_session() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == user.telegram_id)
                )
                db_user = result.scalar_one_or_none()
                if db_user:
                    db_user.daily_requests = user.daily_requests
                    db_user.total_requests = user.total_requests
                    db_user.last_request_date = user.last_request_date
                    await session.commit()

        return await handler(event, data)
