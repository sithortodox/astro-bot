from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select

from bot.database import async_session
from bot.models import User, History

router = Router()


@router.message(lambda m: m.text and m.text.startswith("/history"))
async def cmd_history(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("\u274c Сначала нажми /start")
            return

        result = await session.execute(
            select(History)
            .where(History.user_id == user.id)
            .order_by(History.created_at.desc())
            .limit(10)
        )
        history = result.scalars().all()

    if not history:
        await message.answer("\U0001f4cb Пока нет истории. Попробуй /tarot или /horoscope!")
        return

    lines = ["\U0001f4dc История запросов (последние 10):\n"]
    for i, h in enumerate(history, 1):
        cmd = h.command.upper()
        time = h.created_at.strftime("%d.%m %H:%M") if h.created_at else "?"
        result_preview = h.result[:60] + "..." if len(h.result) > 60 else h.result
        lines.append(f"{i}. [{time}] {cmd}\n   {result_preview}\n")

    await message.answer("\n".join(lines))
