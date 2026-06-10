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


def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f0cf Таро", callback_data="menu:tarot"),
            InlineKeyboardButton(text="\U0001f52e Нумерология", callback_data="menu:numerology"),
        ],
        [
            InlineKeyboardButton(text="\u2b50 Гороскоп", callback_data="menu:horoscope"),
            InlineKeyboardButton(text="\U0001f319 Луна", callback_data="menu:lunar"),
        ],
        [
            InlineKeyboardButton(text="\U0001f464 Профиль", callback_data="menu:profile"),
            InlineKeyboardButton(text="\U0001f4dc История", callback_data="menu:history"),
        ],
        [
            InlineKeyboardButton(text="\u2699\ufe0f Настройки", callback_data="menu:settings"),
        ],
    ])


def get_tarot_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f0cf Карта дня", callback_data="action:tarot")],
        [InlineKeyboardButton(text="\U0001f0cf Расклад на одну карту", callback_data="action:tarot1")],
        [InlineKeyboardButton(text="\U0001f0cf Расклад на три карты", callback_data="action:tarot3")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


def get_settings_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2698\ufe0f Знак зодиака", callback_data="action:setzodiac")],
        [InlineKeyboardButton(text="\U0001f4c5 Дата рождения", callback_data="action:setbirth")],
        [InlineKeyboardButton(text="\U0001f48e Премиум", callback_data="action:premium")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


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
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    text = (
        f"\U0001f44b Привет, {user.first_name}!\n\n"
        "Я \u00abТароКод Судьбы\u00bb \u2014 твой мистический помощник.\n"
        "Выбери, чем я могу тебе помочь:"
    )
    await message.answer(text, reply_markup=get_main_menu())


@router.callback_query(F.data == "menu:main")
async def callback_menu_main(callback_query: CallbackQuery):
    text = (
        "\U0001f44b Чем могу помочь?\n\n"
        "Выбери раздел:"
    )
    await callback_query.message.edit_text(text, reply_markup=get_main_menu())
    await callback_query.answer()


@router.callback_query(F.data == "menu:tarot")
async def callback_menu_tarot(callback_query: CallbackQuery):
    text = "\U0001f0cf Выбери расклад:"
    await callback_query.message.edit_text(text, reply_markup=get_tarot_menu())
    await callback_query.answer()


@router.callback_query(F.data == "menu:numerology")
async def callback_menu_numerology(callback_query: CallbackQuery):
    await callback_query.answer()
    from aiogram.types import Message as Msg
    fake_msg = Msg(
        message_id=0,
        date=0,
        chat=callback_query.message.chat,
        from_user=callback_query.from_user,
        text="/numerology",
    )
    from bot.handlers.numerology import cmd_numerology
    await cmd_numerology(fake_msg)


@router.callback_query(F.data == "menu:horoscope")
async def callback_menu_horoscope(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.horoscope import cmd_horoscope
    fake_msg = type('obj', (object,), {
        'message_id': 0, 'date': 0, 'chat': callback_query.message.chat,
        'from_user': callback_query.from_user, 'text': '/horoscope',
    })()
    await cmd_horoscope(fake_msg)


@router.callback_query(F.data == "menu:lunar")
async def callback_menu_lunar(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.lunar import cmd_lunar
    fake_msg = type('obj', (object,), {
        'message_id': 0, 'date': 0, 'chat': callback_query.message.chat,
        'from_user': callback_query.from_user, 'text': '/lunar',
    })()
    await cmd_lunar(fake_msg)


@router.callback_query(F.data == "menu:profile")
async def callback_menu_profile(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.start import cmd_profile
    fake_msg = type('obj', (object,), {
        'message_id': 0, 'date': 0, 'chat': callback_query.message.chat,
        'from_user': callback_query.from_user, 'text': '/profile',
    })()
    await cmd_profile(fake_msg)


@router.callback_query(F.data == "menu:history")
async def callback_menu_history(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.history import cmd_history
    fake_msg = type('obj', (object,), {
        'message_id': 0, 'date': 0, 'chat': callback_query.message.chat,
        'from_user': callback_query.from_user, 'text': '/history',
    })()
    await cmd_history(fake_msg)


@router.callback_query(F.data == "menu:settings")
async def callback_menu_settings(callback_query: CallbackQuery):
    text = "\u2699\ufe0f Настройки:"
    await callback_query.message.edit_text(text, reply_markup=get_settings_menu())
    await callback_query.answer()


@router.callback_query(F.data == "action:tarot")
async def callback_action_tarot(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.tarot import cmd_tarot
    fake_msg = type('obj', (object,), {
        'message_id': 0, 'date': 0, 'chat': callback_query.message.chat,
        'from_user': callback_query.from_user, 'text': '/tarot',
    })()
    await cmd_tarot(fake_msg)


@router.callback_query(F.data == "action:tarot1")
async def callback_action_tarot1(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.tarot import cmd_tarot1
    fake_msg = type('obj', (object,), {
        'message_id': 0, 'date': 0, 'chat': callback_query.message.chat,
        'from_user': callback_query.from_user, 'text': '/tarot1',
    })()
    await cmd_tarot1(fake_msg)


@router.callback_query(F.data == "action:tarot3")
async def callback_action_tarot3(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.tarot import cmd_tarot3
    fake_msg = type('obj', (object,), {
        'message_id': 0, 'date': 0, 'chat': callback_query.message.chat,
        'from_user': callback_query.from_user, 'text': '/tarot3',
    })()
    await cmd_tarot3(fake_msg)


@router.callback_query(F.data == "action:setzodiac")
async def callback_action_setzodiac(callback_query: CallbackQuery):
    await callback_query.answer()
    await cmd_setzodiac_callback(callback_query)


@router.callback_query(F.data == "action:setbirth")
async def callback_action_setbirth(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer(
        "Отправь дату рождения в формате:\n"
        "/setbirth ДД.ММ.ГГГГ\n\n"
        "Пример: /setbirth 15.03.1990"
    )


@router.callback_query(F.data == "action:premium")
async def callback_action_premium(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.premium import cmd_premium
    fake_msg = type('obj', (object,), {
        'message_id': 0, 'date': 0, 'chat': callback_query.message.chat,
        'from_user': callback_query.from_user, 'text': '/premium',
    })()
    await cmd_premium(fake_msg)


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


async def cmd_setzodiac_callback(callback_query: CallbackQuery):
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
    await callback_query.message.answer("Выбери свой знак зодиака:", reply_markup=markup)


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
