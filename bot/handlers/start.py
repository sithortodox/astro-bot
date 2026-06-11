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
        [KeyboardButton(text="\U0001f48e Премиум")],
        [KeyboardButton(text="\U0001f464 Профиль"), KeyboardButton(text="\u2699\ufe0f Настройки")],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="\U0001f6e1\ufe0f Админ")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_tarot_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="\U0001f0cf Карта дня")],
        [KeyboardButton(text="\U0001f0cf Расклад на одну карту")],
        [KeyboardButton(text="\U0001f0cf Расклад на три карты")],
        [KeyboardButton(text="\u2b05\ufe0f Назад")],
    ], resize_keyboard=True)


def get_numerology_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="\U0001f52e Мой анализ")],
        [KeyboardButton(text="\u2728 Число пути")],
        [KeyboardButton(text="\U0001f31f Число судьбы")],
        [KeyboardButton(text="\U0001f451 Число личности")],
        [KeyboardButton(text="\u2b05\ufe0f Назад")],
    ], resize_keyboard=True)


def get_horoscope_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="\u2b50 Сегодня"), KeyboardButton(text="\U0001f52e Неделя")],
        [KeyboardButton(text="\U0001f4c5 Месяц")],
        [KeyboardButton(text="\u2b05\ufe0f Назад")],
    ], resize_keyboard=True)


def get_lunar_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="\U0001f319 Луна сегодня")],
        [KeyboardButton(text="\U0001f319 Лунный календарь")],
        [KeyboardButton(text="\U0001f33e Лунные рекомендации")],
        [KeyboardButton(text="\u2b05\ufe0f Назад")],
    ], resize_keyboard=True)


def get_premium_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="\U0001f48e Купить Премиум")],
        [KeyboardButton(text="\U0001f4b3 Мои платежи")],
        [KeyboardButton(text="\u2b05\ufe0f Назад")],
    ], resize_keyboard=True)


def get_settings_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="\u2698\ufe0f Знак зодиака")],
        [KeyboardButton(text="\U0001f4c5 Дата рождения")],
        [KeyboardButton(text="\U0001f552 Время рождения")],
        [KeyboardButton(text="\U0001f4cd Место рождения")],
        [KeyboardButton(text="\u2b05\ufe0f Назад")],
    ], resize_keyboard=True)


def get_profile_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="\U0001f4dc История")],
        [KeyboardButton(text="\u2699\ufe0f Настройки")],
        [KeyboardButton(text="\u2b05\ufe0f Назад")],
    ], resize_keyboard=True)


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
    ("\U0001f33e Июль", "07"), ("\U0001f342 Август", "08"), ("\U0001f341 Сентябрь", "09"),
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
            "\U0001f4c5 Выбери год рождения:"
        )
        await message.answer(text, reply_markup=get_year_keyboard())
        return

    text = (
        f"\U0001f44b Привет, {user.first_name}!\n\n"
        "Я \u00abТароКод Судьбы\u00bb \u2014 твой мистический помощник.\n\n"
        "\U0001f44f Доступные разделы:"
    )
    await message.answer(text, reply_markup=get_main_keyboard(is_admin))


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    user = await get_user(message.from_user.id)
    is_admin = message.from_user.id in settings.admin_ids if user else False
    await message.answer("\U0001f44f Выбери раздел:", reply_markup=get_main_keyboard(is_admin))


@router.message(F.text == "\u2b05\ufe0f Назад")
async def handler_back(message: Message):
    user = await get_user(message.from_user.id)
    is_admin = message.from_user.id in settings.admin_ids if user else False
    await message.answer("\U0001f44f Выбери раздел:", reply_markup=get_main_keyboard(is_admin))


@router.message(F.text == "\U0001f0cf Таро")
async def handler_tarot_menu(message: Message):
    await message.answer("\U0001f0cf Выбери расклад:", reply_markup=get_tarot_keyboard())


@router.message(F.text == "\U0001f52e Нумерология")
async def handler_numerology_menu(message: Message):
    await message.answer("\U0001f52e Нумерологический анализ:", reply_markup=get_numerology_keyboard())


@router.message(F.text == "\u2b50 Гороскоп")
async def handler_horoscope_menu(message: Message):
    await message.answer("\u2b50 Выбери гороскоп:", reply_markup=get_horoscope_keyboard())


@router.message(F.text == "\U0001f319 Луна")
async def handler_lunar_menu(message: Message):
    await message.answer("\U0001f319 Лунный раздел:", reply_markup=get_lunar_keyboard())


@router.message(F.text == "\U0001f48e Премиум")
async def handler_premium_menu(message: Message):
    await message.answer("\U0001f48e Премиум-подписка:", reply_markup=get_premium_keyboard())


@router.message(F.text == "\u2699\ufe0f Настройки")
async def handler_settings_menu(message: Message):
    await message.answer("\u2699\ufe0f Настройки:", reply_markup=get_settings_keyboard())


@router.message(F.text == "\U0001f464 Профиль")
async def handler_profile_menu(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("\u274c Сначала нажми /start")
        return

    lines = [
        f"\U0001f464 Профиль: {user.first_name}",
        "",
    ]
    if user.birth_date:
        lines.append(f"\U0001f4c5 Дата рождения: {user.birth_date}")
    if user.birth_time:
        lines.append(f"\U0001f552 Время рождения: {user.birth_time}")
    if user.birth_place:
        lines.append(f"\U0001f4cd Место рождения: {user.birth_place}")
    if user.zodiac_sign:
        emoji = ZODIAC_EMOJI.get(user.zodiac_sign, "")
        lines.append(f"\u2b50 Знак зодиака: {emoji} {user.zodiac_sign}")

    text = "\n".join(lines)
    await message.answer(text, reply_markup=get_profile_keyboard())


@router.message(F.text == "\U0001f6e1\ufe0f Админ")
async def handler_admin_menu(message: Message):
    if message.from_user.id not in settings.admin_ids:
        await message.answer("\u274c Нет доступа")
        return
    await message.answer("\U0001f6e1\ufe0f Админ-панель:", reply_markup=get_admin_keyboard())


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="\U0001f4ca Статистика")],
        [KeyboardButton(text="\U0001f465 Пользователи")],
        [KeyboardButton(text="\U0001f4e2 Рассылка")],
        [KeyboardButton(text="\U0001f6ab Бан")],
        [KeyboardButton(text="\U0001f48e Выдать премиум")],
        [KeyboardButton(text="\u2b05\ufe0f Назад")],
    ], resize_keyboard=True)


@router.message(F.text == "\U0001f4ca Статистика")
async def handler_admin_stats(message: Message):
    if message.from_user.id not in settings.admin_ids:
        return
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
    await message.answer(text, reply_markup=get_admin_keyboard())


@router.message(F.text == "\U0001f465 Пользователи")
async def handler_admin_users(message: Message):
    if message.from_user.id not in settings.admin_ids:
        return
    async with async_session() as session:
        result = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(20)
        )
        users = result.scalars().all()
    if not users:
        await message.answer("\U0001f4cb Пользователей пока нет", reply_markup=get_admin_keyboard())
        return
    lines = ["\U0001f465 Последние пользователи:\n"]
    for u in users:
        premium = "\U0001f48e" if u.is_premium else ""
        lines.append(
            f"  {u.telegram_id} | @{u.username or '?'} | "
            f"{u.first_name or '?'} | {u.zodiac_sign or '?'} {premium}"
        )
    await message.answer("\n".join(lines), reply_markup=get_admin_keyboard())


@router.message(F.text == "\U0001f4e2 Рассылка")
async def handler_admin_broadcast(message: Message):
    if message.from_user.id not in settings.admin_ids:
        return
    await message.answer(
        "Отправь сообщение для рассылки в формате:\n"
        "/broadcast Текст сообщения",
        reply_markup=get_admin_keyboard()
    )


@router.message(F.text == "\U0001f6ab Бан")
async def handler_admin_ban(message: Message):
    if message.from_user.id not in settings.admin_ids:
        return
    await message.answer(
        "Отправь команду:\n/ban USER_ID",
        reply_markup=get_admin_keyboard()
    )


@router.message(F.text == "\U0001f48e Выдать премиум")
async def handler_admin_setpremium(message: Message):
    if message.from_user.id not in settings.admin_ids:
        return
    await message.answer(
        "Отправь команду:\n/setpremium USER_ID",
        reply_markup=get_admin_keyboard()
    )


@router.message(F.text == "\U0001f0cf Карта дня")
async def handler_tarot_day(message: Message):
    from bot.handlers.tarot import draw_card, format_card_short, save_history
    from bot.services.ai_service import adapt_text
    from bot.services.card_images import get_card_image
    from aiogram.types import BufferedInputFile

    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    card, is_reversed = draw_card()
    response = format_card_short(card, is_reversed)
    response = await adapt_text(response, user, context_type="tarot")

    img_buf = get_card_image(card["id"], is_reversed)
    if img_buf:
        photo = BufferedInputFile(img_buf.read(), filename=f"{card['id']}.png")
        await message.answer_photo(photo=photo, caption=response, reply_markup=get_tarot_keyboard())
    else:
        await message.answer(response, reply_markup=get_tarot_keyboard())

    await save_history(user.id, "tarot", response)


@router.message(F.text == "\U0001f0cf Расклад на одну карту")
async def handler_tarot1(message: Message):
    from bot.handlers.tarot import draw_card, format_card_full, save_history
    from bot.services.ai_service import adapt_text
    from bot.services.card_images import get_card_image
    from aiogram.types import BufferedInputFile

    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    card, is_reversed = draw_card()
    response = format_card_full(card, is_reversed)
    response = await adapt_text(response, user, context_type="tarot")

    img_buf = get_card_image(card["id"], is_reversed)
    if img_buf:
        photo = BufferedInputFile(img_buf.read(), filename=f"{card['id']}.png")
        await message.answer_photo(photo=photo, caption=response, reply_markup=get_tarot_keyboard())
    else:
        await message.answer(response, reply_markup=get_tarot_keyboard())

    await save_history(user.id, "tarot1", response)


@router.message(F.text == "\U0001f0cf Расклад на три карты")
async def handler_tarot3(message: Message):
    from bot.state import bot_instance
    from bot.handlers.tarot import draw_cards, format_card_interpretation, save_history
    from bot.services.ai_service import adapt_text
    from bot.services.card_images import get_card_image
    from aiogram.types import BufferedInputFile, InputMediaPhoto

    if not bot_instance:
        await message.answer("\u274c Ошибка")
        return

    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    drawn = draw_cards(3)
    media = []
    card_names = []
    interpretations = []

    for card, is_rev in drawn:
        name = card.get('name_ru', card.get('name', '?'))
        prefix = "\u2b07\ufe0f " if is_rev else ""
        card_names.append(f"{prefix}{name}")

        interp = format_card_interpretation(card, is_rev)
        interp = await adapt_text(interp, user, context_type="tarot")
        interpretations.append(interp)

        img_buf = get_card_image(card["id"], is_rev)
        if img_buf:
            img_buf.seek(0)
            media.append(InputMediaPhoto(
                media=BufferedInputFile(img_buf.read(), filename=f"{card['id']}.png"),
            ))

    header = "\U0001f0cf Тебе выпали: " + " | ".join(card_names)

    if media and len(media) == 3:
        media[-1] = InputMediaPhoto(
            media=media[-1].media,
            caption=header,
        )
        await bot_instance.send_media_group(chat_id=message.chat.id, media=media)
        interp_text = "\n\n".join(interpretations)
        if len(interp_text) > 4000:
            for part in interpretations:
                await message.answer(part)
        else:
            await message.answer(interp_text, reply_markup=get_tarot_keyboard())
    else:
        full_text = header + "\n\n" + "\n\n".join(interpretations)
        await message.answer(full_text, reply_markup=get_tarot_keyboard())

    await save_history(user.id, "tarot3", "3 cards")


@router.message(F.text == "\U0001f52e Мой анализ")
async def handler_numerology(message: Message):
    from bot.services.numerology_service import (
        calculate_life_path, calculate_birth_day_number,
        calculate_soul_number, calculate_personality_from_place,
        calculate_destiny_number, calculate_personality_number,
    )

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("\u274c Сначала нажми /start")
        return

    if not user.birth_date:
        await message.answer(
            "\U0001f4c5 Сначала установи дату рождения в Настройках.",
            reply_markup=get_settings_keyboard()
        )
        return

    life_path = calculate_life_path(user.birth_date)
    birth_day = calculate_birth_day_number(user.birth_date)
    soul = calculate_soul_number(user.birth_time)
    place_personality = calculate_personality_from_place(user.birth_place)
    name = user.first_name or "Пользователь"
    destiny = calculate_destiny_number(name)
    personality = calculate_personality_number(name)

    response = (
        f"\U0001f52e Нумерология для {name}\n\n"
        f"\u2728 Число жизненного пути: {life_path}\n"
        f"{get_life_path_meaning(life_path)}\n\n"
        f"\U0001f4c5 Число дня рождения: {birth_day}\n"
        f"{get_birth_day_meaning(birth_day)}\n\n"
    )

    if soul is not None:
        response += f"\U0001f525 Число души: {soul}\n{get_soul_meaning(soul)}\n\n"

    if place_personality is not None:
        response += f"\U0001f4cd Число места: {place_personality}\n{get_place_meaning(place_personality)}\n\n"

    response += (
        f"\U0001f31f Число судьбы: {destiny}\n"
        f"{get_destiny_meaning(destiny)}\n\n"
        f"\U0001f451 Число личности: {personality}\n"
        f"{get_personality_meaning(personality)}"
    )

    await message.answer(response, reply_markup=get_numerology_keyboard())


@router.message(F.text == "\u2b50 Сегодня")
async def handler_horoscope_daily(message: Message):
    from bot.handlers.horoscope import generate_horoscope

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("\u274c Сначала нажми /start")
        return

    if not user.zodiac_sign:
        await message.answer(
            "\u2698\ufe0f Сначала установи знак зодиака в Настройках.",
            reply_markup=get_settings_keyboard()
        )
        return

    response = await generate_horoscope(user.zodiac_sign, "daily", user)
    await message.answer(response, reply_markup=get_horoscope_keyboard())


@router.message(F.text == "\U0001f52e Неделя")
async def handler_horoscope_weekly(message: Message):
    from bot.handlers.horoscope import generate_horoscope

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("\u274c Сначала нажми /start")
        return

    if not user.zodiac_sign:
        await message.answer(
            "\u2698\ufe0f Сначала установи знак зодиака в Настройках.",
            reply_markup=get_settings_keyboard()
        )
        return

    response = await generate_horoscope(user.zodiac_sign, "weekly", user)
    await message.answer(response, reply_markup=get_horoscope_keyboard())


@router.message(F.text == "\U0001f4c5 Месяц")
async def handler_horoscope_monthly(message: Message):
    from bot.handlers.horoscope import generate_horoscope

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("\u274c Сначала нажми /start")
        return

    if not user.zodiac_sign:
        await message.answer(
            "\u2698\ufe0f Сначала установи знак зодиака в Настройках.",
            reply_markup=get_settings_keyboard()
        )
        return

    response = await generate_horoscope(user.zodiac_sign, "monthly", user)
    await message.answer(response, reply_markup=get_horoscope_keyboard())


@router.message(F.text == "\U0001f319 Луна сегодня")
async def handler_lunar_today(message: Message):
    from bot.handlers.lunar import get_lunar_info

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("\u274c Сначала нажми /start")
        return

    response = get_lunar_info("today")
    await message.answer(response, reply_markup=get_lunar_keyboard())


@router.message(F.text == "\U0001f319 Лунный календарь")
async def handler_lunar_calendar(message: Message):
    from bot.handlers.lunar import get_lunar_info

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("\u274c Сначала нажми /start")
        return

    response = get_lunar_info("calendar")
    await message.answer(response, reply_markup=get_lunar_keyboard())


@router.message(F.text == "\U0001f33e Лунные рекомендации")
async def handler_lunar_tips(message: Message):
    from bot.handlers.lunar import get_lunar_info

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("\u274c Сначала нажми /start")
        return

    response = get_lunar_info("tips")
    await message.answer(response, reply_markup=get_lunar_keyboard())


@router.message(F.text == "\U0001f4dc История")
async def handler_history(message: Message):
    from bot.handlers.history import get_history_text

    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("\u274c Сначала нажми /start")
        return

    text = await get_history_text(user.id)
    await message.answer(text, reply_markup=get_profile_keyboard())


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
    keyboard.append([InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:settings")])
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
    await callback_query.message.answer(
        f"\u2705 Дата рождения установлена: {date_str}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b05\ufe0f Настройки", callback_data="menu:settings")]
        ])
    )


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
    await callback_query.message.answer(
        f"\u2705 Время рождения установлено: {time_str}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b05\ufe0f Настройки", callback_data="menu:settings")]
        ])
    )


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
    await callback_query.message.answer(
        "\u2705 Время рождения пропущено",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b05\ufe0f Настройки", callback_data="menu:settings")]
        ])
    )


@router.callback_query(F.data == "action:setplace")
async def callback_action_setplace(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsPlace.waiting_place)
    await callback_query.answer()
    await callback_query.message.answer(
        "\U0001f4cd Отправь город рождения:\n\n"
        "Пример: Москва",
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
    await callback_query.message.answer(
        "\u2705 Место рождения пропущено",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b05\ufe0f Настройки", callback_data="menu:settings")]
        ])
    )


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
    await message.answer(
        f"\U0001f4cd Место рождения установлено: {display}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b05\ufe0f Настройки", callback_data="menu:settings")]
        ])
    )


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
        await callback_query.message.answer(
            f"{emoji} Знак зодиака установлен: {sign}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="\u2b05\ufe0f Настройки", callback_data="menu:settings")]
            ])
        )
    else:
        await callback_query.message.answer("Сначала нажми /start")
    await callback_query.answer()


@router.message(Command("setbirth"))
async def cmd_setbirth(message: Message):
    await message.answer(
        "\U0001f4c5 Используй меню настроек для установки даты.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2699\ufe0f Настройки", callback_data="menu:settings")]
        ])
    )


@router.message(Command("settime"))
async def cmd_settime(message: Message):
    await message.answer(
        "\U0001f552 Используй меню настроек для установки времени.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2699\ufe0f Настройки", callback_data="menu:settings")]
        ])
    )


@router.message(Command("setplace"))
async def cmd_setplace(message: Message):
    await message.answer(
        "\U0001f4cd Используй меню настроек для установки места.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2699\ufe0f Настройки", callback_data="menu:settings")]
        ])
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "\U0001f4d6 Как пользоваться ботом:\n\n"
        "\u2022 Нажми /menu для открытия главного меню\n"
        "\u2022 Все функции доступны через кнопки\n"
        "\u2022 Не нужно вводить команды вручную\n\n"
        "\U0001f44f Разделы:\n"
        "  \U0001f0cf Таро — расклады и трактовки\n"
        "  \U0001f52e Нумерология — анализ по дате рождения\n"
        "  \u2b50 Гороскоп — прогнозы на день/неделю/месяц\n"
        "  \U0001f319 Луна — лунный календарь и рекомендации\n"
        "  \U0001f48e Премиум — безлимитный доступ\n"
        "  \U0001f464 Профиль — твои данные\n"
        "  \u2699\ufe0f Настройки — изменить данные"
    )
    await message.answer(text, reply_markup=get_main_keyboard())


def get_life_path_meaning(number: int) -> str:
    meanings = {
        1: "\U0001f451 Лидер. Ты независимый, амбициозный и прирождённый лидер. Тебе суждено вести за собой, принимать решения и нести ответственность. Твоя сила — в уверенности и способности вдохновлять других.",
        2: "\U0001f91d Дипломат. Ты тонко чувствуешь людей, умеешь находить компромиссы и создавать гармонию. Твоя миссия — помогать другим через сотрудничество и взаимопонимание.",
        3: "\U0001f3ad Творец. Ты обладаешь яркой индивидуальностью и даром самовыражения. Творчество — твой путь к радости. Ты умеешь видеть красоту в обычных вещах и делиться этим с другими.",
        4: "\U0001f3e0 Строитель. Ты практичен, надёжен и трудолюбив. Ты создаёшь прочные основы во всём — в работе, в отношениях, в жизни. Твоя сила в последовательности и упорстве.",
        5: "\U0001f30d Путешественник. Ты любознательный, разносторонний и жаждешь новых впечатлений. Свобода — твоя стихия. Ты учишься через опыт и изменения.",
        6: "\u2764\ufe0f Опекун. Ты ответственный, заботливый и вcenterе семьи. Люди тянутся к тебе за теплотой и поддержкой. Твоя миссия — создавать любовь и уют вокруг себя.",
        7: "\U0001f52d Искатель. Ты аналитичен, духовен и стремишься к глубокой истине. Ты видишь за поверхностью и ищешь скрытый смысл. Твой путь — познание себя и мира.",
        8: "\U0001f4b0 Менеджер. Ты амбициозен, целеустремлён и обладаешь деловой хваткой. Финансы и статус — твои инструменты для изменения мира. Ты умеешь управлять ресурсами.",
        9: "\U0001f30d Гуманист. Ты сострадательный, идеалистичный и стремишься помочь всему человечеству. Твоя миссия — делать мир лучше через любовь и служение.",
    }
    return meanings.get(number, "\U0001f31f Уникальная вибрация твоего жизненного пути. Ты несёшь в себе особую миссию, которую нужно раскрыть через опыт и самопознание.")


def get_birth_day_meaning(number: int) -> str:
    meanings = {
        1: "Ты родился под знаком первопроходца. Тебе суждено начинать новое, прокладывать свой путь. Ты обладаешь силой воли и способностью вести за собой.",
        2: "Ты несёшь энергию сотрудничества и дипломатии. Ты умеешь чувствовать других и создавать гармонию в отношениях.",
        3: "Ты творческая личность с ярким даром выражения. Ты умеешь радоваться жизни и делиться этой радостью с другими.",
        4: "Ты несёшь энергию стабильности и порядка. Ты надёжный человек, на которого можно положиться.",
        5: "Ты несёшь энергию перемен и свободы. Ты легко адаптируешься и ищешь новые горизонты.",
        6: "Ты несёшь энергию гармонии и заботы. Люди чувствуют себя спокойно рядом с тобой.",
        7: "Ты несёшь энергию духовного поиска. Ты стремишься к глубокому пониманию мира и себя.",
        8: "Ты несёшь энергию успеха и изобилия. Ты умеешь привлекать материальные ресурсы.",
        9: "Ты несёшь энергию служения и завершения. Твоя миссия — помогать другим завершать циклы.",
    }
    return meanings.get(number, "Твоя энергия уникальна и несёт в себе особый смысл, который раскроется через опыт.")


def get_soul_meaning(number: int) -> str:
    meanings = {
        1: "Твоя душа жаждет лидерства и самостоятельности. Ты ищешь возможность проявить свою индивидуальность и повести за собой.",
        2: "Твоя душа ищет гармонии и глубоких связей. Ты стремишься к партнёрству и взаимопониманию.",
        3: "Твоя душа стремится к творчеству самовыражения. Ты ищешь способы выразить свой внутренний мир.",
        4: "Твоя душа жаждет стабильности и порядка. Ты ищешь прочную основу для жизни.",
        5: "Твоя душа жаждет свободы и приключений. Ты не можешь жить без перемен и новых впечатлений.",
        6: "Твоя душа стремится к заботе и любви. Ты ищешь глубокие эмоциональные связи.",
        7: "Твоя душа ищет мудрость и истину. Ты стремишься к духовному росту и познанию.",
        8: "Твоя душа жаждет успеха и признания. Ты ищешь возможность проявить себя в материальном мире.",
        9: "Твоя душа стремится к служению человечеству. Ты ищешь способ помочь другим.",
    }
    return meanings.get(number, "Твоя душа уникальна и несёт в себе особую миссию.")


def get_place_meaning(number: int) -> str:
    meanings = {
        1: "Место рождения даёт тебе энергию лидерства. Ты черпаешь силу из уверенности в себе и способности принимать решения.",
        2: "Место рождения даёт тебе энергию сотрудничества. Ты учишься работать с другими и создавать гармонию.",
        3: "Место рождения даёт тебе творческую энергию. Ты черпаешь вдохновение из общения и самовыражения.",
        4: "Место рождения даёт тебе энергию стабильности. Ты черпаешь силу из порядка и надёжности.",
        5: "Место рождения даёт тебе энергию перемен. Ты черпаешь силу из новых впечатлений и свободы.",
        6: "Место рождения даёт тебе энергию гармонии. Ты черпаешь силу из заботы о близких и любви.",
        7: "Место рождения даёт тебе духовную энергию. Ты черпаешь силу из познания и размышлений.",
        8: "Место рождения даёт тебе энергию успеха. Ты черпаешь силу из достижений и материального благополучия.",
        9: "Место рождения даёт тебе энергию служения. Ты черпаешь силу из помощи другим и альтруизма.",
    }
    return meanings.get(number, "Место рождения даёт тебе уникальную энергию, которая формирует твой характер.")


def get_destiny_meaning(number: int) -> str:
    meanings = {
        1: "Твоя судьба — вести и вдохновлять других своим видением. Ты призван стать примером и показать путь.",
        2: "Твоя судьба — создавать гармонию и выстраивать партнёрства. Ты умеешь объединять людей.",
        3: "Твоя судьба — выражать творчество и дарить радость другим. Твои творения вдохновляют.",
        4: "Твоя судьба — строить прочные основы и создавать стабильность для себя и других.",
        5: "Твоя судьба — принимать изменения и исследовать горизонты. Ты — проводник перемен.",
        6: "Твоя судьба — заботиться и создавать прекрасную среду для жизни.",
        7: "Твоя судьба — искать мудрость и делиться знаниями с другими.",
        8: "Твоя судьба — добиться успеха и материального изобилия, чтобы помочь окружающим.",
        9: "Твоя судьба — служить человечеству и оказывать глубокое воздействие на мир.",
    }
    return meanings.get(number, "Твоя судьба уникальна и принадлежит только тебе. Раскрой её через опыт и самопознание.")


def get_personality_meaning(number: int) -> str:
    meanings = {
        1: "Другие видят тебя уверенным, независимым и харизматичным. Ты производишь впечатление лидера.",
        2: "Другие видят тебя мягким, сотрудничающим и дипломатичным. Ты вызываешь доверие.",
        3: "Другие видят тебя творческим, выразительным и общительным. Ты заряжаешь позитивом.",
        4: "Другие видят тебя надёжным, практичным и трудолюбивым. На тебя можно положиться.",
        5: "Другие видят тебя предприимчивым, энергичным и разносторонним. Ты вдохновляешь свободой.",
        6: "Другие видят тебя тёплым, заботливым и ответственным. Ты создашь ощущение дома.",
        7: "Другие видят тебя вдумчивым, аналитичным и загадочным. Ты вызываешь интерес и уважение.",
        8: "Другие видят тебя амбициозным, влиятельным и успешным. Ты производишь впечатление сильного человека.",
        9: "Другие видят тебя сострадательным, щедрым и мудрым. Ты вызываешь восхищение и благодарность.",
    }
    return meanings.get(number, "Другие видят тебя уникальным и интересным человеком.")
