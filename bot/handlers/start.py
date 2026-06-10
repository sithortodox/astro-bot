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


async def get_or_create_user(telegram_id: int, username: str | None = None, first_name: str | None = None) -> User:
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
    await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    text = (
        f"\U0001f44b Привет, {message.from_user.first_name}!\n\n"
        "Я могу помочь тебе с:\n\n"
        "\U0001f0cf /tarot \u2014 Карта дня\n"
        "\U0001f0cf /tarot1 \u2014 Расклад на одну карту\n"
        "\U0001f0cf /tarot3 \u2014 Расклад на три карты\n\n"
        "\U0001f52e /numerology \u2014 Нумерология\n"
        "\u2b50 /horoscope \u2014 Гороскоп на сегодня\n"
        "\U0001f319 /lunar \u2014 Лунный календарь\n\n"
        "\u2698\ufe0f /setzodiac \u2014 Установить знак зодиака\n"
        "\U0001f4c5 /setbirth ДД.ММ.ГГГГ \u2014 Установить дату рождения\n"
        "\U0001f464 /profile \u2014 Твой профиль\n"
        "\U0001f4dc /history \u2014 История запросов"
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
    await message.answer("Выбери свой знак зодиака:", reply_markup=markup)


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
        await callback_query.message.answer(f"{emoji} Знак зодиака установлен: {sign}")
    else:
        await callback_query.message.answer("Сначала нажми /start")
    await callback_query.answer()


@router.message(Command("setbirth"))
async def cmd_setbirth(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Используй: /setbirth ДД.ММ.ГГГГ\n"
            "Пример: /setbirth 15.03.1990"
        )
        return

    date_str = parts[1].strip()
    try:
        day, month, year = date_str.split(".")
        day, month, year = int(day), int(month), int(year)
        if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2030):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("Неверный формат даты. Используй ДД.ММ.ГГГГ")
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.birth_date = date_str
            await session.commit()
            await message.answer(f"\U0001f4c5 Дата рождения установлена: {date_str}")
        else:
            await message.answer("Сначала нажми /start")


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала нажми /start")
        return

    zodiac_display = "Не установлен"
    if user.zodiac_sign:
        emoji = ZODIAC_EMOJI.get(user.zodiac_sign, "")
        zodiac_display = f"{emoji} {user.zodiac_sign}"

    text = (
        f"\U0001f464 Твой профиль\n\n"
        f" \U0001f464 Имя: {user.first_name or 'Не указано'}\n"
        f" \U0001f464 Username: @{user.username or 'Не указан'}\n"
        f" \u2b50 Знак зодиака: {zodiac_display}\n"
        f" \U0001f4c5 Дата рождения: {user.birth_date or 'Не указана'}\n"
        f" \U0001f48e Премиум: {'Да' if user.is_premium else 'Нет'}\n"
        f" \U0001f4c8 Запросов сегодня: {user.daily_requests}"
    )
    await message.answer(text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "\U0001f4d6 Доступные команды:\n\n"
        "\U0001f0cf Таро:\n"
        "   /tarot \u2014 Карта дня\n"
        "   /tarot1 \u2014 Расклад на одну карту\n"
        "   /tarot3 \u2014 Расклад на три карты\n\n"
        "\U0001f52e Нумерология:\n"
        "   /numerology \u2014 Число жизненного пути\n\n"
        "\u2b50 Гороскоп:\n"
        "   /horoscope \u2014 Гороскоп на сегодня\n\n"
        "\U0001f319 Луна:\n"
        "   /lunar \u2014 Фаза луны\n\n"
        "\u2699\ufe0f Настройки:\n"
        "   /setzodiac \u2014 Установить знак зодиака\n"
        "   /setbirth ДД.ММ.ГГГГ \u2014 Установить дату рождения\n"
        "   /profile \u2014 Профиль\n"
        "   /history \u2014 История запросов"
    )
    await message.answer(text)
