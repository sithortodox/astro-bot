from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.lunar_service import (
    get_lunar_phase,
    get_lunar_recommendation,
    get_daily_lunar_summary,
    get_lunar_calendar,
)
from bot.services.ai_service import adapt_text
from bot.handlers.start import get_user
from bot.database import async_session
from bot.models import History

router = Router()


@router.message(lambda m: m.text and m.text.startswith("/lunar"))
async def cmd_lunar(message: Message):
    phase_name, phase_emoji, illumination = get_lunar_phase()
    recommendation = get_lunar_recommendation(phase_name, "general")

    response = (
        f"{phase_emoji} Лунная фаза: {phase_name}\n"
        f"\U0001f4a1 Освещённость: {illumination:.0f}%\n\n"
        f"\U0001f4a1 Рекомендация:\n{recommendation}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f4c5 Календарь", callback_data="lunar_calendar"),
            InlineKeyboardButton(text="\U0001f52e Сводка", callback_data="lunar_summary"),
        ],
        [
            InlineKeyboardButton(text="\u2764\ufe0f Любовь", callback_data="lunar_cat:love"),
            InlineKeyboardButton(text="\u2605 Карьера", callback_data="lunar_cat:career"),
        ],
    ])

    user = await get_user(message.from_user.id)
    if user:
        response = await adapt_text(response, user, context_type="lunar")
        async with async_session() as session:
            history = History(user_id=user.id, command="lunar", result=response)
            session.add(history)
            await session.commit()

    await message.answer(response, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "lunar_calendar")
async def callback_lunar_calendar(callback_query):
    calendar = get_lunar_calendar(7)

    lines = ["\U0001f4c5 Лунный календарь (7 дней):\n"]
    for day in calendar:
        lines.append(
            f"{day['date_display']}: {day['emoji']} {day['phase']} "
            f"({day['illumination']}%) - {day['moon_sign']}"
        )

    await callback_query.message.answer("\n".join(lines))
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "lunar_summary")
async def callback_lunar_summary(callback_query):
    summary = get_daily_lunar_summary()
    await callback_query.message.answer(summary)
    await callback_query.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("lunar_cat:"))
async def callback_lunar_category(callback_query):
    category = callback_query.data.split(":")[1]
    phase_name, _, _ = get_lunar_phase()
    recommendation = get_lunar_recommendation(phase_name, category)

    cat_labels = {
        "love": "\u2764\ufe0f Любовь",
        "career": "\u2605 Карьера",
        "finance": "\U0001f4b0 Финансы",
        "health": "\U0001f3a5 Здоровье",
    }
    label = cat_labels.get(category, category.title())

    response = f"{label} — Рекомендация\n\n{recommendation}"
    await callback_query.message.answer(response)
    await callback_query.answer()
