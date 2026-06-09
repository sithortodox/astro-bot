import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select

from bot.database import async_session
from bot.models import User, Payment

logger = logging.getLogger(__name__)

# Products configuration
PRODUCTS = {
    "premium_monthly": {
        "name": "Premium Monthly",
        "price_stars": 100,
        "price_rub": 199,
        "duration_days": 30,
        "description": "Unlimited tarot readings, detailed interpretations, monthly forecasts",
    },
    "premium_yearly": {
        "name": "Premium Yearly",
        "price_stars": 900,
        "price_rub": 1790,
        "duration_days": 365,
        "description": "Premium for a year - best value!",
    },
    "deep_reading": {
        "name": "Deep Reading",
        "price_stars": 50,
        "price_rub": 99,
        "duration_days": 0,
        "description": "One-time deep tarot reading with detailed analysis",
    },
    "pdf_report": {
        "name": "PDF Report",
        "price_stars": 75,
        "price_rub": 149,
        "duration_days": 0,
        "description": "Personal PDF report with your readings and forecasts",
    },
}


async def is_premium(user_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.is_premium:
            return False

        if user.premium_until:
            try:
                until = datetime.fromisoformat(user.premium_until)
                if datetime.now() > until:
                    user.is_premium = False
                    user.premium_until = None
                    await session.commit()
                    return False
            except ValueError:
                pass

        return True


async def activate_premium(user_id: int, product: str, payment_id: str, provider: str) -> bool:
    product_data = PRODUCTS.get(product)
    if not product_data:
        return False

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False

        duration = product_data.get("duration_days", 0)
        if duration > 0:
            if user.premium_until:
                try:
                    current_until = datetime.fromisoformat(user.premium_until)
                    if current_until > datetime.now():
                        new_until = current_until + timedelta(days=duration)
                    else:
                        new_until = datetime.now() + timedelta(days=duration)
                except ValueError:
                    new_until = datetime.now() + timedelta(days=duration)
            else:
                new_until = datetime.now() + timedelta(days=duration)

            user.is_premium = True
            user.premium_until = new_until.isoformat()
            user.subscription_type = product
        else:
            user.is_premium = True

        payment = Payment(
            user_id=user.id,
            payment_id=payment_id,
            provider=provider,
            amount=product_data.get("price_stars", 0),
            currency="XTR",
            product=product,
            status="completed",
        )
        session.add(payment)
        await session.commit()

    return True


async def get_user_payments(user_id: int) -> list[dict]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return []

        result = await session.execute(
            select(Payment)
            .where(Payment.user_id == user.id)
            .order_by(Payment.created_at.desc())
            .limit(10)
        )
        payments = result.scalars().all()

    return [
        {
            "product": p.product,
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "date": p.created_at.strftime("%d.%m.%Y %H:%M") if p.created_at else "?",
        }
        for p in payments
    ]


def get_product_info(product: str) -> Optional[dict]:
    return PRODUCTS.get(product)


def get_all_products() -> dict:
    return PRODUCTS
