from __future__ import annotations

from sqlalchemy import select, func

from bot.database import async_session
from bot.models import Payment


class PaymentRepo:
    @staticmethod
    async def add(user_id: int, payment_id: str, provider: str, amount: int, currency: str, product: str, status: str = "completed") -> Payment:
        async with async_session() as session:
            payment = Payment(
                user_id=user_id,
                payment_id=payment_id,
                provider=provider,
                amount=amount,
                currency=currency,
                product=product,
                status=status,
            )
            session.add(payment)
            await session.commit()
            await session.refresh(payment)
            return payment

    @staticmethod
    async def get_by_user(user_id: int, limit: int = 10) -> list[Payment]:
        async with async_session() as session:
            result = await session.execute(
                select(Payment)
                .where(Payment.user_id == user_id)
                .order_by(Payment.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    @staticmethod
    async def count_total() -> int:
        async with async_session() as session:
            return await session.scalar(select(func.count(Payment.id))) or 0
