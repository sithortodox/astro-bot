from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select

from bot.database import async_session
from bot.models import User, History
from bot.handlers.start import get_user
from bot.services.horoscope_service import get_daily_horoscope
from bot.services.ai_service import adapt_text

router = Router()

ZODIAC_DATES = {
    "Овен": (21, 3, 19, 4), "Телец": (20, 4, 20, 5),
    "Близнецы": (21, 5, 20, 6), "Рак": (21, 6, 22, 7),
    "Лев": (23, 7, 22, 8), "Дева": (23, 8, 22, 9),
    "Весы": (23, 9, 22, 10), "Скорпион": (23, 10, 21, 11),
    "Стрелец": (22, 11, 21, 12), "Козерог": (22, 12, 19, 1),
    "Водолей": (20, 1, 18, 2), "Рыбы": (19, 2, 20, 3),
}

ZODIAC_EMOJI = {
    "Овен": "\u2648", "Телец": "\u2649", "Близнецы": "\u264a", "Рак": "\u264b",
    "Лев": "\u264c", "Дева": "\u264d", "Весы": "\u264e", "Скорпион": "\u264f",
    "Стрелец": "\u2650", "Козерог": "\u2651", "Водолей": "\u2652", "Рыбы": "\u2653",
}


@router.message(lambda m: m.text and m.text.startswith("/horoscope"))
async def cmd_horoscope(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Please /start the bot first.")
        return

    if not user.zodiac_sign:
        await message.answer("Please set your zodiac sign first: /setzodiac")
        return

    emoji = ZODIAC_EMOJI.get(user.zodiac_sign, "")
    horoscope = get_daily_horoscope(user.zodiac_sign)
    response = (
        f" {emoji} Daily Horoscope for {user.zodiac_sign}\n\n"
        f"{horoscope}"
    )
    response = await adapt_text(response, user, context_type="horoscope")
    await message.answer(response)

    async with async_session() as session:
        history = History(user_id=user.id, command="horoscope", result=response)
        session.add(history)
        await session.commit()
