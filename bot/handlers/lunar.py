from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from bot.services.lunar_service import (
    get_lunar_phase,
    get_lunar_recommendation,
    get_lunar_calendar,
)

router = Router()


def get_lunar_info(period: str) -> str:
    phase_name, phase_emoji, illumination = get_lunar_phase()

    if period == "today":
        recommendation = get_lunar_recommendation(phase_name, "general")
        return (
            f"{phase_emoji} Луна сегодня: {phase_name}\n"
            f"\U0001f4a1 Освещённость: {illumination:.0f}%\n\n"
            f"\U0001f4a1 Рекомендация:\n{recommendation}"
        )
    elif period == "calendar":
        calendar_data = get_lunar_calendar()
        if isinstance(calendar_data, list):
            lines = ["\U0001f4c5 Лунный календарь:\n"]
            for day in calendar_data:
                date_str = day.get("date", "?")
                phase = day.get("phase", "?")
                emoji = day.get("emoji", "")
                lines.append(f"{date_str} — {emoji} {phase}")
            return "\n".join(lines)
        return str(calendar_data)
    elif period == "tips":
        recommendation = get_lunar_recommendation(phase_name, "general")
        return f"{phase_emoji} Лунные рекомендации:\n\n{recommendation}"
    else:
        return f"{phase_emoji} Луна: {phase_name}"


@router.message(Command("lunar"))
async def cmd_lunar(message: Message):
    await message.answer(
        "\U0001f319 Используй меню для лунного раздела.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="\U0001f319 Луна", callback_data="menu:lunar")]
        ])
    )
