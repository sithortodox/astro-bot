from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto,
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


async def safe_edit(callback_query: CallbackQuery, text: str, reply_markup=None):
    try:
        await callback_query.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        try:
            await callback_query.message.delete()
        except Exception:
            pass
        await callback_query.message.answer(text, reply_markup=reply_markup)

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы",
]

ZODIAC_EMOJI = {
    "Овен": "\u2648", "Телец": "\u2649", "Близнецы": "\u264a", "Рак": "\u264b",
    "Лев": "\u264c", "Дева": "\u264d", "Весы": "\u264e", "Скорпион": "\u264f",
    "Стрелец": "\u2650", "Козерог": "\u2651", "Водолей": "\u2652", "Рыбы": "\u2653",
}


def get_main_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="\U0001f0cf Таро", callback_data="menu:tarot"),
         InlineKeyboardButton(text="\U0001f52e Нумерология", callback_data="menu:numerology")],
        [InlineKeyboardButton(text="\u2b50 Гороскоп", callback_data="menu:horoscope"),
         InlineKeyboardButton(text="\U0001f319 Луна", callback_data="menu:lunar")],
        [InlineKeyboardButton(text="\U0001f48e Премиум", callback_data="menu:premium")],
        [InlineKeyboardButton(text="\U0001f464 Профиль", callback_data="menu:profile"),
         InlineKeyboardButton(text="\u2699\ufe0f Настройки", callback_data="menu:settings")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(text="\U0001f6e1\ufe0f Админ", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_tarot_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f0cf Карта дня", callback_data="action:tarot")],
        [InlineKeyboardButton(text="\U0001f0cf Расклад на одну карту", callback_data="action:tarot1")],
        [InlineKeyboardButton(text="\U0001f0cf Расклад на три карты", callback_data="action:tarot3")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


def get_numerology_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f52e Мой нумерологический анализ", callback_data="action:numerology")],
        [InlineKeyboardButton(text="\u2728 Число жизненного пути", callback_data="action:life_path")],
        [InlineKeyboardButton(text="\U0001f31f Число судьбы", callback_data="action:destiny")],
        [InlineKeyboardButton(text="\U0001f451 Число личности", callback_data="action:personality")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


def get_horoscope_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b50 Сегодня", callback_data="action:horoscope:daily")],
        [InlineKeyboardButton(text="\U0001f52e Неделя", callback_data="action:horoscope:weekly")],
        [InlineKeyboardButton(text="\U0001f4c5 Месяц", callback_data="action:horoscope:monthly")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


def get_lunar_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f319 Луна сегодня", callback_data="action:lunar:today")],
        [InlineKeyboardButton(text="\U0001f319 Лунный календарь", callback_data="action:lunar:calendar")],
        [InlineKeyboardButton(text="\U0001f33e Лунные рекомендации", callback_data="action:lunar:tips")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


def get_premium_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f48e Купить Премиум", callback_data="action:premium")],
        [InlineKeyboardButton(text="\U0001f4b3 Мои платежи", callback_data="my_payments")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


def get_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2698\ufe0f Знак зодиака", callback_data="action:setzodiac")],
        [InlineKeyboardButton(text="\U0001f4c5 Дата рождения", callback_data="action:setbirth")],
        [InlineKeyboardButton(text="\U0001f552 Время рождения", callback_data="action:settime")],
        [InlineKeyboardButton(text="\U0001f4cd Место рождения", callback_data="action:setplace")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


def get_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4dc История", callback_data="action:history")],
        [InlineKeyboardButton(text="\u2699\ufe0f Настройки", callback_data="menu:settings")],
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


@router.callback_query(F.data == "menu:main")
async def callback_menu_main(callback_query: CallbackQuery):
    is_admin = callback_query.from_user.id in settings.admin_ids
    text = "\U0001f44f Выбери раздел:"
    await safe_edit(callback_query, text, reply_markup=get_main_keyboard(is_admin))
    await callback_query.answer()


@router.callback_query(F.data == "menu:tarot")
async def callback_menu_tarot(callback_query: CallbackQuery):
    text = "\U0001f0cf Выбери расклад:"
    await safe_edit(callback_query, text, reply_markup=get_tarot_keyboard())
    await callback_query.answer()


@router.callback_query(F.data == "menu:numerology")
async def callback_menu_numerology(callback_query: CallbackQuery):
    text = "\U0001f52e Нумерологический анализ:"
    await safe_edit(callback_query, text, reply_markup=get_numerology_keyboard())
    await callback_query.answer()


@router.callback_query(F.data == "menu:horoscope")
async def callback_menu_horoscope(callback_query: CallbackQuery):
    text = "\u2b50 Выбери гороскоп:"
    await safe_edit(callback_query, text, reply_markup=get_horoscope_keyboard())
    await callback_query.answer()


@router.callback_query(F.data == "menu:lunar")
async def callback_menu_lunar(callback_query: CallbackQuery):
    text = "\U0001f319 Лунный раздел:"
    await safe_edit(callback_query, text, reply_markup=get_lunar_keyboard())
    await callback_query.answer()


@router.callback_query(F.data == "menu:premium")
async def callback_menu_premium(callback_query: CallbackQuery):
    text = "\U0001f48e Премиум-подписка:"
    await safe_edit(callback_query, text, reply_markup=get_premium_keyboard())
    await callback_query.answer()


@router.callback_query(F.data == "menu:settings")
async def callback_menu_settings(callback_query: CallbackQuery):
    text = "\u2699\ufe0f Настройки:"
    await safe_edit(callback_query, text, reply_markup=get_settings_keyboard())
    await callback_query.answer()


@router.callback_query(F.data == "menu:profile")
async def callback_menu_profile(callback_query: CallbackQuery):
    user = await get_user(callback_query.from_user.id)
    if not user:
        await callback_query.message.answer("\u274c Сначала нажми /start")
        await callback_query.answer()
        return

    zodiac_display = "Не установлен"
    if user.zodiac_sign:
        emoji = ZODIAC_EMOJI.get(user.zodiac_sign, "")
        zodiac_display = f"{emoji} {user.zodiac_sign}"

    text = (
        f"\U0001f464 Твой профиль\n\n"
        f"\U0001f464 Имя: {user.first_name or 'Не указано'}\n"
        f"@{user.username or 'Не указан'}\n"
        f"\u2698\ufe0f Знак зодиака: {zodiac_display}\n"
        f"\U0001f4c5 Дата рождения: {user.birth_date or 'Не указана'}\n"
        f"\U0001f552 Время рождения: {user.birth_time or 'Неизвестно'}\n"
        f"\U0001f4cd Место рождения: {user.birth_place or 'Неизвестно'}\n"
        f"\U0001f48e Премиум: {'Да' if user.is_premium else 'Нет'}\n"
        f"\U0001f4c8 Запросов сегодня: {user.daily_requests}"
    )
    await safe_edit(callback_query, text, reply_markup=get_profile_keyboard())
    await callback_query.answer()


@router.callback_query(F.data == "menu:admin")
async def callback_menu_admin(callback_query: CallbackQuery):
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("\u274c Нет доступа")
        return
    text = "\U0001f6e1\ufe0f Админ-панель:"
    await safe_edit(callback_query, text, reply_markup=get_admin_keyboard())
    await callback_query.answer()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4ca Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton(text="\U0001f465 Пользователи", callback_data="admin:users")],
        [InlineKeyboardButton(text="\U0001f4e2 Рассылка", callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="\U0001f6ab Бан", callback_data="admin:ban")],
        [InlineKeyboardButton(text="\U0001f48e Выдать премиум", callback_data="admin:setpremium")],
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:main")],
    ])


@router.callback_query(F.data.startswith("action:tarot"))
async def callback_action_tarot(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.tarot import (
        draw_card, draw_cards, format_card_short, format_card_full,
        save_history,
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
            )],
            [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:tarot")]
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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:tarot")]
        ])
        img_buf = get_card_image(card["id"], is_reversed)
        if img_buf:
            photo = BufferedInputFile(img_buf.read(), filename=f"{card['id']}.png")
            await callback_query.message.answer_photo(photo=photo, caption=response, reply_markup=keyboard)
        else:
            await callback_query.message.answer(response, reply_markup=keyboard)
        await save_history(user.id, "tarot1", response)

    elif action == "tarot3":
        from bot.state import bot_instance

        if not bot_instance:
            await callback_query.answer("\u274c Ошибка")
            return

        from bot.handlers.tarot import format_card_interpretation

        drawn = draw_cards(3)
        media = []
        card_names = []
        interpretations = []

        for i, (card, is_rev) in enumerate(drawn):
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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:tarot")]
        ])

        if media and len(media) == 3:
            media[-1] = InputMediaPhoto(
                media=media[-1].media,
                caption=header,
            )
            await bot_instance.send_media_group(chat_id=callback_query.message.chat.id, media=media)
            interp_text = "\n\n".join(interpretations)
            if len(interp_text) > 4000:
                for part in interpretations:
                    await callback_query.message.answer(part)
            else:
                await callback_query.message.answer(interp_text, reply_markup=keyboard)
        else:
            full_text = header + "\n\n" + "\n\n".join(interpretations)
            await callback_query.message.answer(full_text, reply_markup=keyboard)

        await save_history(user.id, "tarot3", "3 cards")


@router.callback_query(F.data.startswith("action:numerology"))
async def callback_action_numerology(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.services.numerology_service import (
        calculate_life_path, calculate_birth_day_number,
        calculate_soul_number, calculate_personality_from_place,
        calculate_destiny_number, calculate_personality_number,
    )

    user = await get_user(callback_query.from_user.id)
    if not user:
        await callback_query.message.answer("\u274c Сначала нажми /start")
        return

    if not user.birth_date:
        await callback_query.message.answer(
            "\U0001f4c5 Сначала установи дату рождения в Настройках.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="\u2699\ufe0f Настройки", callback_data="menu:settings")]
            ])
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

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:numerology")]
    ])
    await callback_query.message.answer(response, reply_markup=keyboard)


@router.callback_query(F.data.startswith("action:horoscope:"))
async def callback_action_horoscope(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.horoscope import generate_horoscope
    from bot.services.ai_service import adapt_text

    user = await get_user(callback_query.from_user.id)
    if not user:
        await callback_query.message.answer("\u274c Сначала нажми /start")
        return

    if not user.zodiac_sign:
        await callback_query.message.answer(
            "\u2698\ufe0f Сначала установи знак зодиака в Настройках.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="\u2699\ufe0f Настройки", callback_data="menu:settings")]
            ])
        )
        return

    period = callback_query.data.split(":")[2]
    response = generate_horoscope(user.zodiac_sign, period)
    response = await adapt_text(response, user, context_type="horoscope")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:horoscope")]
    ])
    await callback_query.message.answer(response, reply_markup=keyboard)


@router.callback_query(F.data.startswith("action:lunar:"))
async def callback_action_lunar(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.lunar import get_lunar_info
    from bot.services.ai_service import adapt_text

    user = await get_user(callback_query.from_user.id)
    if not user:
        await callback_query.message.answer("\u274c Сначала нажми /start")
        return

    period = callback_query.data.split(":")[2]
    response = get_lunar_info(period)
    response = await adapt_text(response, user, context_type="lunar")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:lunar")]
    ])
    await callback_query.message.answer(response, reply_markup=keyboard)


@router.callback_query(F.data == "action:history")
async def callback_action_history(callback_query: CallbackQuery):
    await callback_query.answer()
    from bot.handlers.history import get_history_text

    user = await get_user(callback_query.from_user.id)
    if not user:
        await callback_query.message.answer("\u274c Сначала нажми /start")
        return

    text = await get_history_text(user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:profile")]
    ])
    await callback_query.message.answer(text, reply_markup=keyboard)


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


@router.callback_query(F.data.startswith("admin:"))
async def callback_admin(callback_query: CallbackQuery):
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("\u274c Нет доступа")
        return

    action = callback_query.data.split(":")[1]

    if action == "stats":
        await _admin_stats(callback_query)
    elif action == "users":
        await _admin_users(callback_query)
    elif action == "broadcast":
        await _admin_broadcast(callback_query)
    elif action == "ban":
        await _admin_ban(callback_query)
    elif action == "setpremium":
        await _admin_setpremium(callback_query)

    await callback_query.answer()


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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:admin")]
    ])
    await callback_query.message.answer(text, reply_markup=keyboard)


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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:admin")]
    ])
    await callback_query.message.answer("\n".join(lines), reply_markup=keyboard)


async def _admin_broadcast(callback_query: CallbackQuery):
    await callback_query.message.answer(
        "Отправь сообщение для рассылки в формате:\n"
        "/broadcast Текст сообщения",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:admin")]
        ])
    )


async def _admin_ban(callback_query: CallbackQuery):
    await callback_query.message.answer(
        "Отправь команду:\n/ban USER_ID",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:admin")]
        ])
    )


async def _admin_setpremium(callback_query: CallbackQuery):
    await callback_query.message.answer(
        "Отправь команду:\n/setpremium USER_ID",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\u2b05\ufe0f Назад", callback_data="menu:admin")]
        ])
    )


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
        1: "\U0001f451 Лидер. Ты независимый, амбициозный и прирождённый лидер.",
        2: "\U0001f91d Дипломат. Ты сотрудничаешь, чувствуешь других и приносишь гармонию.",
        3: "\U0001f3ad Творец. Ты выразительный, общительный и обладаешь даром общения.",
        4: "\U0001f3e0 Строитель. Ты практичен, стабилен и трудолюбив.",
        5: "\U0001f30d Путешественник. Ты разносторонний, любознательный и ценишь свободу.",
        6: "\u2764\ufe0f Опекун. Ты ответственный, заботливый и сердце семьи.",
        7: "\U0001f52d Искатель. Ты аналитичен, духовен и ищешь более глубокую истину.",
        8: "\U0001f4b0 Менеджер. Ты амбициозен, успешен и обладаешь деловой хваткой.",
        9: "\U0001f30d Гуманист. Ты сострадательный, идеалистичный и помогаешь другим.",
    }
    return meanings.get(number, "\U0001f31f Уникальная вибрация твоего жизненного пути.")


def get_birth_day_meaning(number: int) -> str:
    meanings = {
        1: "Ты родился под знаком первопроходца. Тебе суждено начинать новое.",
        2: "Ты несёшь энергию сотрудничества и дипломатии.",
        3: "Ты творческая личность с даром выражения.",
        4: "Ты несёшь энергию стабильности и порядка.",
        5: "Ты несёшь энергию перемен и свободы.",
        6: "Ты несёшь энергию гармонии и заботы.",
        7: "Ты несёшь энергию духовного поиска.",
        8: "Ты несёшь энергию успеха и изобилия.",
        9: "Ты несёшь энергию служения и завершения.",
    }
    return meanings.get(number, "Твоя энергия уникальна.")


def get_soul_meaning(number: int) -> str:
    meanings = {
        1: "Твоя душа жаждет лидерства и самостоятельности.",
        2: "Твоя душа ищет гармонии и глубоких связей.",
        3: "Твоя душа стремится к творчеству самовыражения.",
        4: "Твоя душа渴ет стабильности и порядка.",
        5: "Твоя душа жаждет свободы и приключений.",
        6: "Твоя душа стремится к заботе и любви.",
        7: "Твоя душа ищет мудрость и истину.",
        8: "Твоя душа渴ет успеха и признания.",
        9: "Твоя душа стремится к служению человечеству.",
    }
    return meanings.get(number, "Твоя душа уникальна.")


def get_place_meaning(number: int) -> str:
    meanings = {
        1: "Место рождения даёт тебе энергию лидерства.",
        2: "Место рождения даёт тебе энергию сотрудничества.",
        3: "Место рождения даёт тебе творческую энергию.",
        4: "Место рождения даёт тебе энергию стабильности.",
        5: "Место рождения даёт тебе энергию перемен.",
        6: "Место рождения даёт тебе энергию гармонии.",
        7: "Место рождения даёт тебе духовную энергию.",
        8: "Место рождения даёт тебе энергию успеха.",
        9: "Место рождения даёт тебе энергию служения.",
    }
    return meanings.get(number, "Место рождения даёт тебе уникальную энергию.")


def get_destiny_meaning(number: int) -> str:
    meanings = {
        1: "Твоя судьба — вести и вдохновлять других своим видением.",
        2: "Твоя судьба — создавать гармонию и выстраивать партнёрства.",
        3: "Твоя судьба — выражать творчество и дарить радость другим.",
        4: "Твоя судьба — строить прочные основы и создавать стабильность.",
        5: "Твоя судьба — принимать изменения и исследовать горизонты.",
        6: "Твоя судьба — заботиться и создавать прекрасную среду.",
        7: "Твоя судьба — искать мудрость и делиться знаниями.",
        8: "Твоя судьба — добиться успеха и материального изобилия.",
        9: "Твоя судьба — служить человечеству и оказывать воздействие.",
    }
    return meanings.get(number, "Твоя судьба уникальна и принадлежит только тебе.")


def get_personality_meaning(number: int) -> str:
    meanings = {
        1: "Другие видят тебя уверенным, независимым и харизматичным.",
        2: "Другие видят тебя мягким, сотрудничающим и дипломатичным.",
        3: "Другие видят тебя творческим, выразительным и общительным.",
        4: "Другие видят тебя надёжным, практичным и трудолюбивым.",
        5: "Другие видят тебя предприимчивым, энергичным и разносторонним.",
        6: "Другие видят тебя тёплым, заботливым и ответственным.",
        7: "Другие видят тебя вдумчивым, аналитичным и загадочным.",
        8: "Другие видят тебя амбициозным, влиятельным и успешным.",
        9: "Другие видят тебя сострадательным, щедрым и мудрым.",
    }
    return meanings.get(number, "Другие видят тебя уникальным и интересным.")
