from __future__ import annotations

from sqlalchemy import select

from bot.database import async_session
from bot.models import History


class HistoryRepo:
    @staticmethod
    async def add(user_id: int, command: str, result: str) -> None:
        async with async_session() as session:
            history = History(user_id=user_id, command=command, result=result)
            session.add(history)
            await session.commit()

    @staticmethod
    async def get_by_user(user_id: int, limit: int = 10) -> list[History]:
        async with async_session() as session:
            result = await session.execute(
                select(History)
                .where(History.user_id == user_id)
                .order_by(History.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    @staticmethod
    async def count_total() -> int:
        from sqlalchemy import func
        async with async_session() as session:
            return await session.scalar(select(func.count(History.id))) or 0
