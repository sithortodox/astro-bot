from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select

from bot.database import async_session
from bot.models import User, History
from bot.handlers.start import get_user, get_or_create_user
from bot.services.numerology_service import (
    calculate_life_path,
    calculate_birth_day_number,
    calculate_soul_number,
    calculate_personality_from_place,
    calculate_destiny_number,
    calculate_personality_number,
)
from bot.services.ai_service import adapt_text

router = Router()


@router.message(lambda m: m.text and m.text.startswith("/numerology"))
async def cmd_numerology(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("\u274c Сначала нажми /start")
        return

    if not user.birth_date:
        await message.answer(
            "\U0001f4c5 Сначала установи дату рождения.\n"
            "Используй: /setbirth ДД.ММ.ГГГГ"
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
        response += (
            f"\U0001f525 Число души: {soul}\n"
            f"{get_soul_meaning(soul)}\n\n"
        )

    if place_personality is not None:
        response += (
            f"\U0001f4cd Число места: {place_personality}\n"
            f"{get_place_meaning(place_personality)}\n\n"
        )

    response += (
        f"\U0001f31f Число судьбы: {destiny}\n"
        f"{get_destiny_meaning(destiny)}\n\n"
        f"\U0001f451 Число личности: {personality}\n"
        f"{get_personality_meaning(personality)}"
    )

    if user.birth_time or user.birth_place:
        response += "\n\n\U0001f4a1 Дополнительные числа рассчитаны на основе времени и места рождения."

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
        await message.answer("Используй: /setbirth ДД.ММ.ГГГГ")
        return

    date_str = parts[1].strip()
    try:
        day, month, year = date_str.split(".")
        day, month, year = int(day), int(month), int(year)
        if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2030):
            raise ValueError
    except (ValueError, IndexError):
        await message.answer("\u274c Неверный формат даты. Используй ДД.ММ.ГГГГ")
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
                await message.answer(f"\u2705 Дата рождения установлена: {date_str}")


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
        4: "Твоя душа渴求 стабильности и порядка.",
        5: "Твоя душа жаждет свободы и приключений.",
        6: "Твоя душа стремится к заботе и любви.",
        7: "Твоя душа ищет мудрость и истину.",
        8: "Твоя душа渴ет успеха и признания.",
        9: "Твоя душа стремится к служению человечеству.",
    }
    return meanings.get(number, "Твоя душе уникальна.")


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
        1: "Твоя судьба — вести и вдохновлять других своей видением.",
        2: "Твоя судьба — создавать гармонию и выстраивать значимые партнёрства.",
        3: "Твоя судьба — выражать творчество и дарить радость другим.",
        4: "Твоя судьба — строить прочные основы и создавать стабильность.",
        5: "Твоя судьба — принимать изменения и исследовать новые горизонты.",
        6: "Твоя судьба — заботиться и создавать прекрасную среду.",
        7: "Твоя судьба — искать мудрость и делиться глубокими знаниями.",
        8: "Твоя судьба — добиться успеха и материального изобилия.",
        9: "Твоя судьба — служить человечеству и оказывать глобальное воздействие.",
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
