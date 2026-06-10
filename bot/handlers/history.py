from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select

from bot.database import async_session
from bot.models import User, History

router = Router()


async def get_history_text(user_id: int) -> str:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return "\u274c Сначала нажми /start"

        result = await session.execute(
            select(History)
            .where(History.user_id == user.id)
            .order_by(History.created_at.desc())
            .limit(10)
        )
        history = result.scalars().all()

    if not history:
        return "\U0001f4cb Пока нет истории. Попробуй Таро или Гороскоп!"

    lines = ["\U0001f4dc История запросов (последние 10):\n"]
    for i, h in enumerate(history, 1):
        cmd = h.command.upper()
        time = h.created_at.strftime("%d.%m %H:%M") if h.created_at else "?"
        result_preview = h.result[:60] + "..." if len(h.result) > 60 else h.result
        lines.append(f"{i}. [{time}] {cmd}\n   {result_preview}\n")

    return "\n".join(lines)


@router.message(Command("history"))
async def cmd_history(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await message.answer(
        "\U0001f4dc Используй меню для просмотра истории.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\U0001f4dc История", callback_data="action:history")]
        ])
    )
