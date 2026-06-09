from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select

from bot.database import async_session
from bot.models import User, History
from bot.handlers.start import get_user, get_or_create_user
from bot.services.numerology_service import (
    calculate_life_path,
    calculate_destiny_number,
    calculate_personality_number,
)
from bot.services.ai_service import adapt_text

router = Router()


@router.message(lambda m: m.text and m.text.startswith("/numerology"))
async def cmd_numerology(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Please /start the bot first.")
        return

    if not user.birth_date:
        await message.answer(
            " Please set your birth date first.\n"
            "Usage: /setbirth DD.MM.YYYY"
        )
        return

    life_path = calculate_life_path(user.birth_date)
    name = user.first_name or "User"
    destiny = calculate_destiny_number(name)
    personality = calculate_personality_number(name)

    response = (
        f" \U0001f52e Numerology for {name}\n\n"
        f" \u2728 Life Path: {life_path}\n"
        f" {get_life_path_meaning(life_path)}\n\n"
        f" \U0001f31f Destiny: {destiny}\n"
        f" {get_destiny_meaning(destiny)}\n\n"
        f" \U0001f451 Personality: {personality}\n"
        f" {get_personality_meaning(personality)}"
    )
    response = await adapt_text(response, user, context_type="numerology")
    await message.answer(response)

    async with async_session() as session:
        history = History(user_id=user.id, command="numerology", result=response)
        session.add(history)
        await session.commit()


@router.message(lambda m: m.text and m.text.startswith("/setbirth"))
async def cmd_setbirth(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /setbirth DD.MM.YYYY")
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

    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )
    if user:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == message.from_user.id)
            )
            db_user = result.scalar_one_or_none()
            if db_user:
                db_user.birth_date = date_str
                await session.commit()
                await message.answer(f"Birth date set to: {date_str}")


def get_life_path_meaning(number: int) -> str:
    meanings = {
        1: "\U0001f451 Leader. You are independent, ambitious, and a natural born leader.",
        2: "\U0001f91d Diplomat. You are cooperative, sensitive, and bring harmony.",
        3: "\U0001f3ad Creative. You are expressive, social, and have a gift for communication.",
        4: "\U0001f3e0 Builder. You are practical, stable, and hardworking.",
        5: "\U0001f30d Adventurer. You are versatile, curious, and love freedom.",
        6: "\u2764\ufe0f Nurturer. You are responsible, caring, and the heart of the family.",
        7: "\U0001f52d Seeker. You are analytical, spiritual, and seek deeper truth.",
        8: "\U0001f4b0 Executive. You are ambitious, successful, and have business acumen.",
        9: "\U0001f30d Humanitarian. You are compassionate, idealistic, and serve others.",
    }
    return meanings.get(number, "\U0001f31f Unique vibration of your life path.")


def get_destiny_meaning(number: int) -> str:
    meanings = {
        1: "Your destiny is to lead and inspire others through your vision.",
        2: "Your destiny is to create harmony and build meaningful partnerships.",
        3: "Your destiny is to express creativity and bring joy to others.",
        4: "Your destiny is to build lasting foundations and create stability.",
        5: "Your destiny is to embrace change and explore new horizons.",
        6: "Your destiny is to nurture and create beautiful environments.",
        7: "Your destiny is to seek wisdom and share deep insights.",
        8: "Your destiny is to achieve success and material abundance.",
        9: "Your destiny is to serve humanity and make a global impact.",
    }
    return meanings.get(number, "Your destiny is uniquely your own.")


def get_personality_meaning(number: int) -> str:
    meanings = {
        1: "Others see you as confident, independent, and charismatic.",
        2: "Others see you as gentle, cooperative, and diplomatic.",
        3: "Others see you as creative, expressive, and social.",
        4: "Others see you as reliable, practical, and hardworking.",
        5: "Others see you as adventurous, energetic, and versatile.",
        6: "Others see you as warm, caring, and responsible.",
        7: "Others see you as thoughtful, analytical, and mysterious.",
        8: "Others see you as ambitious, powerful, and successful.",
        9: "Others see you as compassionate, generous, and wise.",
    }
    return meanings.get(number, "Others see you as unique and intriguing.")
