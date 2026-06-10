from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.filters import CommandStart, Command
from sqlalchemy import select, func
from datetime import date

from bot.database import async_session
from bot.models import User, Payment
from bot.config import settings

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


def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="\U0001f0cf Таро"), KeyboardButton(text="\U0001f52e Нумерология")],
        [KeyboardButton(text="\u2b50 Гороскоп"), KeyboardButton(text="\U0001f319 Луна")],
        [KeyboardButton(text="\U0001f464 Профиль"), KeyboardButton(text="\U0001f4dc История")],
        [KeyboardButton(text="\u2699\ufe0f Настройки")],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="\U0001f6e1\ufe0f Админ")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_tarot_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f0cf Карта дня", callback_data="action:tarot")],
        [InlineKeyboardButton(text="\U0001f0cf Расклад на одну карту", callback_data="action:tarot1")],
        [InlineKeyboardButton(text="\U0001f0cf Расклад на три карты", callback_data="action:tarot3")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


def get_settings_keyboard() -> InlineKeyboardMarkup:
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


def _make_fake_msg(callback_query: CallbackQuery, text: str = "") -> Message:
    return Message(
        message_id=0,
        date=0,
        chat=callback_query.message.chat,
        from_user=callback_query.from_user,
        text=text,
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    is_admin = message.from_user.id in settings.admin_ids
    text = (
        f"\U0001f44b Привет, {user.first_name}!\n\n"
        "Я \u00abТароКод Судьбы\u00bb \u2014 твой мистический помощник.\n"
        "Выбери раздел кнопкой внизу:"
    )
    await message.answer(text, reply_markup=get_main_keyboard(is_admin))


@router.message(F.text == "\U0001f0cf Таро")
@router.message(Command("tarot_menu"))
async def msg_tarot(message: Message):
    text = "\U0001f0cf Выбери расклад:"
    await message.answer(text, reply_markup=get_tarot_keyboard())


@router.message(F.text == "\U0001f52e Нумерология")
@router.message(Command("numerology"))
async def msg_numerology(message: Message):
    from bot.handlers.numerology import cmd_numerology
    await cmd_numerology(message)


@router.message(F.text == "\u2b50 Гороскоп")
@router.message(Command("horoscope"))
async def msg_horoscope(message: Message):
    from bot.handlers.horoscope import cmd_horoscope
    await cmd_horoscope(message)


@router.message(F.text == "\U0001f319 Луна")
@router.message(Command("lunar"))
async def msg_lunar(message: Message):
    from bot.handlers.lunar import cmd_lunar
    await cmd_lunar(message)


@router.message(F.text == "\U0001f464 Профиль")
@router.message(Command("profile"))
async def msg_profile(message: Message):
    await cmd_profile(message)


@router.message(F.text == "\U0001f4dc История")
@router.message(Command("history"))
async def msg_history(message: Message):
    from bot.handlers.history import cmd_history
    await cmd_history(message)


@router.message(F.text == "\u2699\ufe0f Настройки")
@router.message(Command("settings"))
async def msg_settings(message: Message):
    text = "\u2699\ufe0f Настройки:"
    await message.answer(text, reply_markup=get_settings_keyboard())


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4ca Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton(text="\U0001f465 Пользователи", callback_data="admin:users")],
        [InlineKeyboardButton(text="\U0001f4e2 Рассылка", callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="\U0001f6ab Бан", callback_data="admin:ban")],
        [InlineKeyboardButton(text="\U0001f48e Выдать премиум", callback_data="admin:setpremium")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


@router.message(F.text == "\U0001f6e1\ufe0f Админ")
@router.message(Command("admin"))
async def msg_admin(message: Message):
    if message.from_user.id not in settings.admin_ids:
        await message.answer("\u274c У тебя нет доступа")
        return
    text = "\U0001f6e1\ufe0f Админ-панель:"
    await message.answer(text, reply_markup=get_admin_keyboard())


async def _admin_stats(callback_query: CallbackQuery):
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
    text = (
        f"\U0001f4ca Статистика\n\n"
        f"\U0001f465 Всего пользователей: {total_users}\n"
        f"\U0001f48e Премиум: {premium_users}\n"
        f"\U0001f525 Активны сегодня: {active_today}\n"
        f"\U0001f4c8 Всего запросов: {total_requests or 0}\n"
        f"\U0001f4b3 Всего платежей: {total_payments or 0}"
    )
    await callback_query.message.answer(text)


async def _admin_users(callback_query: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(20)
        )
        users = result.scalars().all()
    if not users:
        await callback_query.message.answer("\U0001f4cb Пользователей пока нет")
        return
    lines = ["\U0001f465 Последние пользователи:\n"]
    for u in users:
        premium = "\U0001f48e" if u.is_premium else ""
        lines.append(
            f"  {u.telegram_id} | @{u.username or '?'} | "
            f"{u.first_name or '?'} | {u.zodiac_sign or '?'} {premium}"
        )
    await callback_query.message.answer("\n".join(lines))


async def _admin_broadcast(callback_query: CallbackQuery):
    await callback_query.message.answer(
        "Отправь сообщение для рассылки в формате:\n"
        "/broadcast Текст сообщения"
    )


async def _admin_ban(callback_query: CallbackQuery):
    await callback_query.message.answer(
        "Отправь команду:\n/ban USER_ID"
    )


async def _admin_setpremium(callback_query: CallbackQuery):
    await callback_query.message.answer(
        "Отправь команду:\n/setpremium USER_ID"
    )


@router.callback_query(F.data == "admin:stats")
async def callback_admin_stats(callback_query: CallbackQuery):
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("\u274c Нет доступа")
        return
    await _admin_stats(callback_query)
    await callback_query.answer()


@router.callback_query(F.data == "admin:users")
async def callback_admin_users(callback_query: CallbackQuery):
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("\u274c Нет доступа")
        return
    await _admin_users(callback_query)
    await callback_query.answer()


@router.callback_query(F.data == "admin:broadcast")
async def callback_admin_broadcast(callback_query: CallbackQuery):
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("\u274c Нет доступа")
        return
    await _admin_broadcast(callback_query)
    await callback_query.answer()


@router.callback_query(F.data == "admin:ban")
async def callback_admin_ban(callback_query: CallbackQuery):
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("\u274c Нет доступа")
        return
    await _admin_ban(callback_query)
    await callback_query.answer()


@router.callback_query(F.data == "admin:setpremium")
async def callback_admin_setpremium(callback_query: CallbackQuery):
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("\u274c Нет доступа")
        return
    await _admin_setpremium(callback_query)
    await callback_query.answer()


@router.callback_query(F.data == "menu:main")
async def callback_menu_main(callback_query: CallbackQuery):
    text = "\U0001f44b Чем могу помочь?"
    await callback_query.message.edit_text(text)
    await callback_query.answer()


@router.callback_query(F.data == "menu:tarot")
async def callback_menu_tarot(callback_query: CallbackQuery):
    text = "\U0001f0cf Выбери расклад:"
    await callback_query.message.edit_text(text, reply_markup=get_tarot_keyboard())
    await callback_query.answer()


@router.callback_query(F.data == "menu:settings")
async def callback_menu_settings(callback_query: CallbackQuery):
    text = "\u2699\ufe0f Настройки:"
    await callback_query.message.edit_text(text, reply_markup=get_settings_keyboard())
    await callback_query.answer()


@router.callback_query(F.data.startswith("action:tarot"))
async def callback_action_tarot(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.tarot import cmd_tarot, cmd_tarot1, cmd_tarot3
    action = callback_query.data.split(":")[1]
    fake_msg = _make_fake_msg(callback_query, f"/{action}")
    if action == "tarot":
        await cmd_tarot(fake_msg)
    elif action == "tarot1":
        await cmd_tarot1(fake_msg)
    elif action == "tarot3":
        await cmd_tarot3(fake_msg)


@router.callback_query(F.data == "action:setzodiac")
async def callback_action_setzodiac(callback_query: CallbackQuery):
    await callback_query.answer()
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
    fake_msg = _make_fake_msg(callback_query, "/premium")
    await cmd_premium(fake_msg)


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
        f" Имя: {user.first_name or 'Не указано'}\n"
        f" Username: @{user.username or 'Не указан'}\n"
        f" Знак зодиака: {zodiac_display}\n"
        f" Дата рождения: {user.birth_date or 'Не указана'}\n"
        f" Премиум: {'Да' if user.is_premium else 'Нет'}\n"
        f" Запросов сегодня: {user.daily_requests}"
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
