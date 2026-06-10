from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
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
        [InlineKeyboardButton(text="\U0001f552 Время рождения", callback_data="action:settime")],
        [InlineKeyboardButton(text="\U0001f4cd Место рождения", callback_data="action:setplace")],
        [InlineKeyboardButton(text="\U0001f48e Премиум", callback_data="action:premium")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


def get_year_keyboard() -> InlineKeyboardMarkup:
    years = list(range(2010, 1959, -1))
    keyboard = []
    for i in range(0, len(years), 5):
        row = [InlineKeyboardButton(text=str(y), callback_data=f"bd:y:{y}") for y in years[i:i+5]]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:settings")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


MONTHS = [
    ("\u2762 Январь", "01"), ("\u2766 Февраль", "02"), ("\U0001f33c Март", "03"),
    ("\U0001f33a Апрель", "04"), ("\U0001f33b Май", "05"), ("\U0001f33f Июнь", "06"),
    ("\U0001f33e Июль", "08"), ("\U0001f342 Август", "08"), ("\U0001f341 Сентябрь", "09"),
    ("\U0001f343 Октябрь", "10"), ("\U0001f344 Ноябрь", "11"), ("\u2744 Декабрь", "12"),
]


def get_month_keyboard(year: int) -> InlineKeyboardMarkup:
    keyboard = []
    for i in range(0, len(MONTHS), 3):
        row = []
        for name, num in MONTHS[i:i+3]:
            row.append(InlineKeyboardButton(text=name, callback_data=f"bd:m:{year}:{num}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="bd:back:year")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_day_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]
    keyboard = []
    for i in range(1, days_in_month + 1, 7):
        row = []
        for d in range(i, min(i + 7, days_in_month + 1)):
            row.append(InlineKeyboardButton(text=str(d), callback_data=f"bd:d:{year}:{month:02d}:{d:02d}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data=f"bd:back:month:{year}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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


class Onboarding(StatesGroup):
    birth_date = State()
    birth_time = State()
    birth_place = State()


class SettingsPlace(StatesGroup):
    waiting_place = State()


def _make_fake_msg(callback_query: CallbackQuery, text: str = "") -> Message:
    return Message(
        message_id=0,
        date=0,
        chat=callback_query.message.chat,
        from_user=callback_query.from_user,
        text=text,
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    is_admin = message.from_user.id in settings.admin_ids

    if not user.birth_date:
        await state.set_state(Onboarding.birth_date)
        text = (
            f"\U0001f44b Привет, {user.first_name}!\n\n"
            "Я \u00abТароКод Судьбы\u00bb \u2014 твой мистический помощник.\n\n"
            "Для точного нумерологического анализа мне нужно узнать о тебе.\n"
            "Начнём с даты рождения.\n\n"
            "\U0001f4c5 Отправь дату рождения в формате: ДД.ММ.ГГГГ\n"
            "Пример: 15.03.1990"
        )
        await message.answer(text)
        return

    text = (
        f"\U0001f44b Привет, {user.first_name}!\n\n"
        "Я \u00abТароКод Судьбы\u00bb \u2014 твой мистический помощник.\n"
        "Выбери раздел кнопкой внизу:"
    )
    await message.answer(text, reply_markup=get_main_keyboard(is_admin))


@router.message(Onboarding.birth_date)
async def onboarding_birth_date(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        day, month, year = text.split(".")
        day, month, year = int(day), int(month), int(year)
        if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2030):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("\u274c Неверный формат. Используй ДД.ММ.ГГГГ\nПример: 15.03.1990")
        return

    await state.update_data(birth_date=text)
    await state.set_state(Onboarding.birth_time)
    await message.answer(
        f"\u2705 Дата рождения: {text}\n\n"
        "\U0001f552 Теперь отправь время рождения (ЧЧ:ММ)\n"
        "Пример: 14:30\n\n"
        "Если не знаешь время, отправь \u00ab-\u00bb"
    )


@router.message(Onboarding.birth_time)
async def onboarding_birth_time(message: Message, state: FSMContext):
    text = message.text.strip()

    if text == "-":
        birth_time = None
    else:
        try:
            parts = text.split(":")
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
            birth_time = text
        except (ValueError, IndexError):
            await message.answer(
                "\u274c Неверный формат. Используй ЧЧ:ММ\n"
                "Пример: 14:30\n\n"
                "Если не знаешь время, отправь \u00ab-\u00bb"
            )
            return

    await state.update_data(birth_time=birth_time)
    await state.set_state(Onboarding.birth_place)
    time_display = birth_time or "Неизвестно"
    await message.answer(
        f"\u2705 Время рождения: {time_display}\n\n"
        "\U0001f4cd Теперь отправь место рождения (город)\n"
        "Пример: Москва\n\n"
        "Если не знаешь, отправь \u00ab-\u00bb"
    )


@router.message(Onboarding.birth_place)
async def onboarding_birth_place(message: Message, state: FSMContext):
    text = message.text.strip()
    birth_place = text if text != "-" else None

    data = await state.get_data()
    birth_date = data["birth_date"]
    birth_time = data.get("birth_time")

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.birth_date = birth_date
            user.birth_time = birth_time
            user.birth_place = birth_place
            await session.commit()

    await state.clear()

    place_display = birth_place or "Неизвестно"
    is_admin = message.from_user.id in settings.admin_ids

    await message.answer(
        f"\u2705 Место рождения: {place_display}\n\n"
        "\U0001f386 Отлично! Все данные собраны.\n"
        "Теперь я могу делать точные нумерологические расчёты.\n\n"
        "Выбери раздел кнопкой внизу:",
        reply_markup=get_main_keyboard(is_admin),
    )


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
    from bot.handlers.tarot import (
        draw_card, draw_cards, format_card_short, format_card_full,
        format_card_with_position, save_history,
    )
    from bot.services.ai_service import adapt_text
    from bot.services.card_images import get_card_image
    from aiogram.types import BufferedInputFile

    action = callback_query.data.split(":")[1]
    user = await get_or_create_user(
        callback_query.from_user.id,
        callback_query.from_user.username,
        callback_query.from_user.first_name,
    )

    if action == "tarot":
        card, is_reversed = draw_card()
        response = format_card_short(card, is_reversed)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="\U0001f50d Подробнее",
                callback_data=f"tarot_detail:{card['id']}:{1 if is_reversed else 0}"
            )]
        ])
        response = await adapt_text(response, user, context_type="tarot")
        img_buf = get_card_image(card["id"], is_reversed)
        if img_buf:
            photo = BufferedInputFile(img_buf.read(), filename=f"{card['id']}.png")
            await callback_query.message.answer_photo(photo=photo, caption=response, reply_markup=keyboard)
        else:
            await callback_query.message.answer(response, reply_markup=keyboard)
        await save_history(user.id, "tarot", response)

    elif action == "tarot1":
        card, is_reversed = draw_card()
        response = format_card_full(card, is_reversed)
        response = await adapt_text(response, user, context_type="tarot")
        img_buf = get_card_image(card["id"], is_reversed)
        if img_buf:
            photo = BufferedInputFile(img_buf.read(), filename=f"{card['id']}.png")
            await callback_query.message.answer_photo(photo=photo, caption=response)
        else:
            await callback_query.message.answer(response)
        await save_history(user.id, "tarot1", response)

    elif action == "tarot3":
        drawn = draw_cards(3)
        positions = ["Прошлое", "Настоящее", "Будущее"]
        for i, (card, is_rev) in enumerate(drawn):
            pos = positions[i] if i < 3 else f"Карта {i+1}"
            text = format_card_with_position(card, is_rev, pos)
            text = await adapt_text(text, user, context_type="tarot")
            img_buf = get_card_image(card["id"], is_rev)
            if img_buf:
                photo = BufferedInputFile(img_buf.read(), filename=f"{card['id']}.png")
                await callback_query.message.answer_photo(photo=photo, caption=text)
            else:
                await callback_query.message.answer(text)
        await save_history(user.id, "tarot3", "3 cards")


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
        "\U0001f4c5 Выбери год рождения:",
        reply_markup=get_year_keyboard()
    )


@router.callback_query(F.data.startswith("bd:y:"))
async def callback_bd_year(callback_query: CallbackQuery):
    year = int(callback_query.data.split(":")[2])
    await callback_query.answer()
    await callback_query.message.answer(
        f"\U0001f4c5 {year} — выбери месяц:",
        reply_markup=get_month_keyboard(year)
    )


@router.callback_query(F.data.startswith("bd:m:"))
async def callback_bd_month(callback_query: CallbackQuery):
    parts = callback_query.data.split(":")
    year, month = int(parts[2]), int(parts[3])
    await callback_query.answer()
    await callback_query.message.answer(
        f"\U0001f4c5 {year}/{month:02d} — выбери день:",
        reply_markup=get_day_keyboard(year, month)
    )


@router.callback_query(F.data.startswith("bd:d:"))
async def callback_bd_day(callback_query: CallbackQuery):
    parts = callback_query.data.split(":")
    year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
    date_str = f"{day:02d}.{month:02d}.{year}"
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback_query.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.birth_date = date_str
            await session.commit()
    
    await callback_query.answer()
    await callback_query.message.answer(f"\u2705 Дата рождения установлена: {date_str}")


@router.callback_query(F.data == "bd:back:year")
async def callback_bd_back_year(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer(
        "\U0001f4c5 Выбери год рождения:",
        reply_markup=get_year_keyboard()
    )


@router.callback_query(F.data.startswith("bd:back:month:"))
async def callback_bd_back_month(callback_query: CallbackQuery):
    year = int(callback_query.data.split(":")[3])
    await callback_query.answer()
    await callback_query.message.answer(
        f"\U0001f4c5 {year} — выбери месяц:",
        reply_markup=get_month_keyboard(year)
    )


@router.callback_query(F.data == "action:settime")
async def callback_action_settime(callback_query: CallbackQuery):
    await callback_query.answer()
    hours = list(range(0, 24))
    keyboard = []
    for i in range(0, 24, 6):
        row = [InlineKeyboardButton(text=f"{h:02d}", callback_data=f"bt:h:{h:02d}") for h in hours[i:i+6]]
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="\u274c Не знаю", callback_data="bt:skip")])
    keyboard.append([InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:settings")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback_query.message.answer("\U0001f552 Выбери час рождения:", reply_markup=markup)


@router.callback_query(F.data.startswith("bt:h:"))
async def callback_bt_hour(callback_query: CallbackQuery):
    hour = int(callback_query.data.split(":")[2])
    minutes = [0, 15, 30, 45]
    keyboard = []
    row = [InlineKeyboardButton(text=f":{m:02d}", callback_data=f"bt:m:{hour:02d}:{m:02d}") for m in minutes]
    keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="\u274c Не знаю", callback_data="bt:skip")])
    keyboard.append([InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="action:settime")])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback_query.answer()
    await callback_query.message.answer(f"\U0001f552 {hour:02d}:__ — выбери минуты:", reply_markup=markup)


@router.callback_query(F.data.startswith("bt:m:"))
async def callback_bt_minute(callback_query: CallbackQuery):
    parts = callback_query.data.split(":")
    hour, minute = int(parts[2]), int(parts[3])
    time_str = f"{hour:02d}:{minute:02d}"
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback_query.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.birth_time = time_str
            await session.commit()
    
    await callback_query.answer()
    await callback_query.message.answer(f"\u2705 Время рождения установлено: {time_str}")


@router.callback_query(F.data == "bt:skip")
async def callback_bt_skip(callback_query: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback_query.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.birth_time = None
            await session.commit()
    
    await callback_query.answer()
    await callback_query.message.answer("\u2705 Время рождения пропущено")


@router.callback_query(F.data == "action:setplace")
async def callback_action_setplace(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsPlace.waiting_place)
    await callback_query.answer()
    await callback_query.message.answer(
        "\U0001f4cd Отправь город рождения:\n\n"
        "Пример: Москва\n\n"
        "Если не знаешь — нажми кнопку ниже.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u274c Не знаю", callback_data="bp:skip")],
            [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:settings")],
        ])
    )


@router.callback_query(F.data == "bp:skip")
async def callback_bp_skip(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback_query.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.birth_place = None
            await session.commit()
    
    await callback_query.answer()
    await callback_query.message.answer("\u2705 Место рождения пропущено")


@router.callback_query(F.data == "action:premium")
async def callback_action_premium(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.services.payment_service import is_premium, get_all_products
    from datetime import datetime

    user = await get_user(callback_query.from_user.id)
    if not user:
        await callback_query.message.answer("\u274c Сначала нажми /start")
        return

    premium_status = await is_premium(callback_query.from_user.id)

    if premium_status and user.premium_until:
        try:
            until = datetime.fromisoformat(user.premium_until)
            days_left = (until - datetime.now()).days
            status_text = f"\U0001f48e Премиум активен\nДействует до: {until.strftime('%d.%m.%Y')}\nОсталось дней: {days_left}"
        except ValueError:
            status_text = "\U0001f48e Премиум активен"
    elif premium_status:
        status_text = "\U0001f48e Премиум активен (пожизненно)"
    else:
        status_text = "\U0001f4b3 Бесплатный план\nОбновись до Премиум для безлимитного доступа!"

    products = get_all_products()

    keyboard = []
    for key, product in products.items():
        if product.get("duration_days", 0) > 0:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{product['name']} - {product['price_stars']} Stars",
                    callback_data=f"buy:{key}"
                )
            ])

    keyboard.append([
        InlineKeyboardButton(text="\U0001f4b3 Мои платежи", callback_data="my_payments")
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    text = (
        f"\U0001f48e Премиум-подписка\n\n"
        f"{status_text}\n\n"
        f"\U0001f31f Преимущества:\n"
        f"  \u2728 Безлимитные расклады Таро\n"
        f"  \U0001f4d6 Подробные трактовки\n"
        f"  \U0001f4c5 Ежемесячные прогнозы\n"
        f"  \u2b50 Приоритетная AI-адаптация\n"
        f"  \u26a1 Без дневных лимитов\n\n"
        f"Выбери план:"
    )

    await callback_query.message.answer(text, reply_markup=markup)


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


@router.message(Command("settime"))
async def cmd_settime(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Используй: /settime ЧЧ:ММ\n"
            "Пример: /settime 14:30\n\n"
            "Если не знаешь время, отправь /settime -"
        )
        return

    time_str = parts[1].strip()

    if time_str == "-":
        time_str = None
    else:
        try:
            h, m = time_str.split(":")
            h, m = int(h), int(m)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except (ValueError, IndexError):
            await message.answer("Неверный формат. Используй ЧЧ:ММ или /settime -")
            return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.birth_time = time_str
            await session.commit()
            display = time_str or "Неизвестно"
            await message.answer(f"\U0001f552 Время рождения установлено: {display}")
        else:
            await message.answer("Сначала нажми /start")


@router.message(Command("setplace"))
async def cmd_setplace(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Используй: /setplace Город\n"
            "Пример: /setplace Москва\n\n"
            "Если не знаешь, отправь /setplace -"
        )
        return

    place_str = parts[1].strip()
    if place_str == "-":
        place_str = None

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.birth_place = place_str
            await session.commit()
            display = place_str or "Неизвестно"
            await message.answer(f"\U0001f4cd Место рождения установлено: {display}")
        else:
            await message.answer("Сначала нажми /start")


@router.message(SettingsPlace.waiting_place)
async def handle_place_input(message: Message, state: FSMContext):
    place = message.text.strip()
    if place == "-":
        place = None

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.birth_place = place
            await session.commit()

    await state.clear()
    display = place or "Неизвестно"
    await message.answer(f"\U0001f4cd Место рождения установлено: {display}")


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
        f" @{user.username or 'Не указан'}\n"
        f" \u2698\ufe0f Знак зодиака: {zodiac_display}\n"
        f" \U0001f4c5 Дата рождения: {user.birth_date or 'Не указана'}\n"
        f" \U0001f552 Время рождения: {user.birth_time or 'Неизвестно'}\n"
        f" \U0001f4cd Место рождения: {user.birth_place or 'Неизвестно'}\n"
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
