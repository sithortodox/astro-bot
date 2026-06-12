from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy import select, func
from datetime import date
import hmac

from bot.config import settings
from bot.database import async_session
from bot.models import User, History, Payment

app = FastAPI(title="Astro Bot Admin API", version="1.0.0")


def verify_admin_key(x_admin_key: str = Header(...)):
    if not settings.admin_api_key:
        raise HTTPException(status_code=500, detail="ADMIN_API_KEY not configured")
    if not hmac.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return True


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "astro-bot"}


@app.get("/api/stats")
async def get_stats(admin: bool = Depends(verify_admin_key)):
    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        premium_users = await session.scalar(
            select(func.count(User.id)).where(User.is_premium)
        )
        today = date.today().isoformat()
        active_today = await session.scalar(
            select(func.count(User.id)).where(User.last_request_date == today)
        )
        total_requests = await session.scalar(select(func.sum(User.total_requests)))
        total_payments = await session.scalar(select(func.count(Payment.id)))

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "active_today": active_today,
        "total_requests": total_requests or 0,
        "total_payments": total_payments or 0,
    }


@app.get("/api/users")
async def get_users(
    limit: int = 50,
    offset: int = 0,
    admin: bool = Depends(verify_admin_key),
):
    async with async_session() as session:
        result = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        users = result.scalars().all()

    return {
        "users": [
            {
                "telegram_id": u.telegram_id,
                "username": u.username,
                "first_name": u.first_name,
                "zodiac_sign": u.zodiac_sign,
                "is_premium": u.is_premium,
                "total_requests": u.total_requests,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }


@app.get("/api/user/{telegram_id}")
async def get_user_detail(telegram_id: int, admin: bool = Depends(verify_admin_key)):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        history_result = await session.execute(
            select(History)
            .where(History.user_id == user.id)
            .order_by(History.created_at.desc())
            .limit(20)
        )
        history = history_result.scalars().all()

    return {
        "user": {
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "zodiac_sign": user.zodiac_sign,
            "birth_date": user.birth_date,
            "is_premium": user.is_premium,
            "premium_until": user.premium_until,
            "total_requests": user.total_requests,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "history": [
            {
                "command": h.command,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ],
    }


@app.get("/api/payments")
async def get_payments(
    limit: int = 50,
    admin: bool = Depends(verify_admin_key),
):
    async with async_session() as session:
        result = await session.execute(
            select(Payment).order_by(Payment.created_at.desc()).limit(limit)
        )
        payments = result.scalars().all()

    return {
        "payments": [
            {
                "user_id": p.user_id,
                "product": p.product,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payments
        ]
    }


@app.post("/api/broadcast")
async def broadcast_message(
    text: str,
    admin: bool = Depends(verify_admin_key),
):
    async with async_session() as session:
        result = await session.execute(select(User.telegram_id))
        user_ids = [row[0] for row in result.all()]

    return {
        "total_users": len(user_ids),
        "message": "Broadcast queued. Use Telegram bot to send.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
