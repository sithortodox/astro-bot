from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy import select

from bot.database import async_session
from bot.models import User

router = Router()

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]

ZODIAC_EMOJI = {
    "Овен": "\u2648", "Телец": "\u2649", "Близнецы": "\u264a", "Рак": "\u264b",
    "Лев": "\u264c", "Дева": "\u264d", "Весы": "\u264e", "Скорпион": "\u264f",
    "Стрелец": "\u2650", "Козерог": "\u2651", "Водолей": "\u2652", "Рыбы": "\u2653",
}


async def get_user(telegram_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None) -> User:
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


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    text = (
        f" Welcome, {message.from_user.first_name}!\n\n"
        " I can help you with:\n\n"
        " /tarot \u2014 Card of the day\n"
        " /tarot1 \u2014 One card reading (detailed)\n"
        " /tarot3 \u2014 Three card reading\n\n"
        " /numerology \u2014 Life path number\n"
        " /horoscope \u2014 Daily horoscope\n"
        " /lunar \u2014 Lunar phase\n\n"
        " /setzodiac \u2014 Set your zodiac sign\n"
        " /setbirth DD.MM.YYYY \u2014 Set birth date\n"
        " /profile \u2014 Your profile\n"
        " /history \u2014 Request history"
    )
    await message.answer(text)


@router.message(Command("setzodiac"))
async def cmd_setzodiac(message: Message):
    keyboard = []
    for i in range(0, len(ZODIAC_SIGNS), 3):
        row = []
        for sign in ZODIAC_SIGNS[i:i + 3]:
            emoji = ZODIAC_EMOJI.get(sign, "")
            row.append(InlineKeyboardButton(
                text=f"{emoji} {sign}",
                callback_data=f"zodiac:{sign}"
            ))
        keyboard.append(row)

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer("Choose your zodiac sign:", reply_markup=markup)


@router.callback_query(F.data.startswith("zodiac:"))
async def callback_zodiac(callback_query: CallbackQuery):
    sign = callback_query.data.split(":", 1)[1]
    user = await get_or_create_user(callback_query.from_user.id)
    if user:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == callback_query.from_user.id)
            )
            db_user = result.scalar_one_or_none()
            if db_user:
                db_user.zodiac_sign = sign
                await session.commit()
        emoji = ZODIAC_EMOJI.get(sign, "")
        await callback_query.message.answer(f"{emoji} Zodiac sign set to: {sign}")
    else:
        await callback_query.message.answer("Please /start the bot first.")
    await callback_query.answer()


@router.message(Command("setbirth"))
async def cmd_setbirth(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Usage: /setbirth DD.MM.YYYY\n"
            "Example: /setbirth 15.03.1990"
        )
        return

    date_str = parts[1].strip()
    try:
        day, month, year = date_str.split(".")
        day, month, year = int(day), int(month), int(year)
        if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2030):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("Invalid date format. Use DD.MM.YYYY")
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.birth_date = date_str
            await session.commit()
            await message.answer(f"Birth date set to: {date_str}")
        else:
            await message.answer("Please /start the bot first.")


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Please /start the bot first.")
        return

    zodiac_display = "Not set"
    if user.zodiac_sign:
        emoji = ZODIAC_EMOJI.get(user.zodiac_sign, "")
        zodiac_display = f"{emoji} {user.zodiac_sign}"

    text = (
        f" Your Profile\n\n"
        f" Name: {user.first_name or 'Not set'}\n"
        f" Username: @{user.username or 'Not set'}\n"
        f" Zodiac: {zodiac_display}\n"
        f" Birth date: {user.birth_date or 'Not set'}\n"
        f" Premium: {'Yes' if user.is_premium else 'No'}\n"
        f" Requests today: {user.daily_requests}"
    )
    await message.answer(text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        " Available Commands:\n\n"
        " Tarot:\n"
        "   /tarot \u2014 Card of the day\n"
        "   /tarot1 \u2014 One card reading\n"
        "   /tarot3 \u2014 Three card reading\n\n"
        " Numerology:\n"
        "   /numerology \u2014 Life path number\n\n"
        " Horoscope:\n"
        "   /horoscope \u2014 Daily horoscope\n\n"
        " Lunar:\n"
        "   /lunar \u2014 Lunar phase\n\n"
        " Settings:\n"
        "   /setzodiac \u2014 Set zodiac sign\n"
        "   /setbirth DD.MM.YYYY \u2014 Set birth date\n"
        "   /profile \u2014 View profile\n"
        "   /history \u2014 Request history"
    )
    await message.answer(text)
