from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services.horoscope_service import get_daily_horoscope

router = Router()

ZODIAC_EMOJI = {
    "Овен": "\u2648", "Телец": "\u2649", "Близнецы": "\u264a", "Рак": "\u264b",
    "Лев": "\u264c", "Дева": "\u264d", "Весы": "\u264e", "Скорпион": "\u264f",
    "Стрелец": "\u2650", "Козерог": "\u2651", "Водолей": "\u2652", "Рыбы": "\u2653",
}


async def generate_horoscope(zodiac_sign: str, period: str, user=None) -> str:
    emoji = ZODIAC_EMOJI.get(zodiac_sign, "")

    if period == "weekly":
        from bot.services.ai_service import adapt_text
        content = f"Знак зодиака: {zodiac_sign}. Составь гороскоп на неделю."
        text = await adapt_text(content, user, context_type="horoscope_weekly")
        return f"{emoji} Гороскоп на неделю: {zodiac_sign}\n\n{text}"

    horoscope = get_daily_horoscope(zodiac_sign)
    return f"{emoji} Гороскоп на сегодня: {zodiac_sign}\n\n{horoscope}"


@router.message(Command("horoscope"))
async def cmd_horoscope(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await message.answer(
        "\u2b50 Используй меню для гороскопа.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b50 Гороскоп", callback_data="menu:horoscope")]
        ])
    )
