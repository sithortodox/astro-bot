"""
Обработчик команд таро на основе колоды Astralis Tarot.

Заменяет текущий обработчик Rider-Waite.
Использует Semantic Engine для анализа карт и GigaChat для трактовок.
"""

import random
from aiogram import Router
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command

from bot.database import async_session
from bot.models import History
from bot.handlers.start import get_or_create_user
from bot.services.ai_service import adapt_text
from bot.services.card_images import get_card_image
from bot.services.astralis_engine import engine, CardData

router = Router()


# ===========================
# ФОРМАТИРОВАНИЕ
# ===========================

def format_card_short(card: CardData, is_reversed: bool = False) -> str:
    """Краткое описание карты."""
    prefix = "\u2b07\ufe0f " if is_reversed else ""
    meaning = card.shadow_meaning if is_reversed else card.light_meaning
    if len(meaning) > 180:
        meaning = meaning[:177] + "..."
    return f"{prefix}{card.name_ru}\n\n{meaning}"


def format_card_full(card: CardData, is_reversed: bool = False) -> str:
    """Полное описание карты с контекстными трактовками."""
    prefix = "\u2b07\ufe0f \u041f\u0435\u0440\u0435\u0432\u0451\u0440\u043d\u0443\u0442\u0430\u044f " if is_reversed else ""
    meaning = card.shadow_meaning if is_reversed else card.light_meaning

    # Доминирующие архетипы
    dom_arch = card.archetypes.dominant(3)
    arch_str = ", ".join(f"{name}({val})" for name, val in dom_arch)

    # Доминирующие метрики
    dom_met = card.metrics.dominant(5)
    met_str = ", ".join(f"{name}({val})" for name, val in dom_met)

    lines = [
        f"{prefix}{card.name_ru}",
        "",
        meaning,
        "",
        f"\u2764\ufe0f \u041b\u044e\u0431\u043e\u0432\u044c: {card.love}",
        f"\u2605 \u041a\u0430\u0440\u044c\u0435\u0440\u0430: {card.career}",
        f"\u2728 \u0424\u0438\u043d\u0430\u043d\u0441\u044b: {card.money}",
        "",
        f"\u26a1 \u0421\u043e\u0432\u0435\u0442: {card.advice}",
        f"\u26a0\ufe0f \u041f\u0440\u0435\u0434\u0443\u043f\u0440\u0435\u0436\u0434\u0435\u043d\u0438\u0435: {card.warning}",
    ]
    return "\n".join(lines)


def format_card_with_position(card: CardData, is_reversed: bool, position: str) -> str:
    """Форматирование карты с позицией в раскладе."""
    emoji_map = {
        "\u041f\u0440\u043e\u0448\u043b\u043e\u0435": "\u23f0",
        "\u041d\u0430\u0441\u0442\u043e\u044f\u0449\u0435\u0435": "\u2714\ufe0f",
        "\u0411\u0443\u0434\u0443\u0449\u0435\u0435": "\U0001f52e",
    }
    emoji = emoji_map.get(position, "\u25b6")
    prefix = "\u2b07\ufe0f " if is_reversed else ""
    return f"{emoji} {position}\n{prefix}{card.name_ru}"


# ===========================
# КОМАНДЫ
# ===========================

@router.message(Command("tarot"))
async def cmd_tarot(message: Message):
    """Карта дня — одна карта."""
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    cards = engine.draw_random(1)
    if not cards:
        await message.answer("\u274c \u0411\u0430\u0437\u0430 \u0437\u043d\u0430\u043d\u0438\u0439 \u043f\u0443\u0441\u0442\u0430.")
        return

    card = cards[0]
    is_reversed = random.random() < 0.3
    response = format_card_short(card, is_reversed)

    img_buf = get_card_image(card.id, is_reversed)
    if img_buf:
        photo = BufferedInputFile(img_buf.read(), filename=f"{card.id}.png")
        await message.answer_photo(photo=photo, caption=response)
    else:
        await message.answer(response)

    await save_history(user.id, "tarot", response)


@router.message(Command("tarot1"))
async def cmd_tarot1(message: Message):
    """Полная карта — с контекстными трактовками."""
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    cards = engine.draw_random(1)
    if not cards:
        await message.answer("\u274c \u0411\u0430\u0437\u0430 \u0437\u043d\u0430\u043d\u0438\u0439 \u043f\u0443\u0441\u0442\u0430.")
        return

    card = cards[0]
    is_reversed = random.random() < 0.3
    response = format_card_full(card, is_reversed)

    img_buf = get_card_image(card.id, is_reversed)
    if img_buf:
        photo = BufferedInputFile(img_buf.read(), filename=f"{card.id}.png")
        await message.answer_photo(photo=photo, caption=response)
    else:
        await message.answer(response)

    await save_history(user.id, "tarot1", response)


@router.message(Command("tarot3"))
async def cmd_tarot3(message: Message):
    """Три карты — прошлое, настоящее, будущее."""
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    cards = engine.draw_random(3)
    if not cards:
        await message.answer("\u274c \u0411\u0430\u0437\u0430 \u0437\u043d\u0430\u043d\u0438\u0439 \u043f\u0443\u0441\u0442\u0430.")
        return

    positions = ["\u041f\u0440\u043e\u0448\u043b\u043e\u0435", "\u041d\u0430\u0441\u0442\u043e\u044f\u0449\u0435\u0435", "\u0411\u0443\u0434\u0443\u0449\u0435\u0435"]
    drawn = [(card, random.random() < 0.3) for card in cards]

    for i, (card, is_rev) in enumerate(drawn):
        pos = positions[i] if i < 3 else f"\u041a\u0430\u0440\u0442\u0430 {i + 1}"
        text = format_card_with_position(card, is_rev, pos)

        img_buf = get_card_image(card.id, is_rev)
        if img_buf:
            photo = BufferedInputFile(img_buf.read(), filename=f"{card.id}.png")
            await message.answer_photo(photo=photo, caption=text)
        else:
            await message.answer(text)

    # Краткий итог
    summary_lines = ["\U0001f52e \u0418\u0442\u043e\u0433 \u0440\u0430\u0441\u043a\u043b\u0430\u0434\u0430:"]
    for i, (card, is_rev) in enumerate(drawn):
        pos = positions[i] if i < 3 else f"\u041a\u0430\u0440\u0442\u0430 {i + 1}"
        summary_lines.append(f"{pos}: {card.name_ru}")
    await message.answer("\n".join(summary_lines))

    await save_history(user.id, "tarot3", "3 cards")


@router.message(Command("tarot_spread"))
async def cmd_tarot_spread(message: Message):
    """Расклад с вопросом — анализ через GigaChat."""
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    # Извлекаем вопрос из сообщения
    parts = message.text.split(maxsplit=1)
    question = parts[1] if len(parts) > 1 else ""

    if not question:
        await message.answer(
            "\U0001f52e \u041d\u0430\u043f\u0438\u0448\u0438\u0442\u0435 \u0432\u043e\u043f\u0440\u043e\u0441 \u043f\u043e\u0441\u043b\u0435 /tarot_spread\n"
            "\u041f\u0440\u0438\u043c\u0435\u0440: /tarot_spread \u041a\u0430\u043a \u0441\u043b\u043e\u0436\u0438\u0442\u0441\u044f \u043c\u043e\u0438 \u0434\u0435\u043b\u0430?"
        )
        return

    cards = engine.draw_random(3)
    if not cards:
        await message.answer("\u274c \u0411\u0430\u0437\u0430 \u0437\u043d\u0430\u043d\u0438\u0439 \u043f\u0443\u0441\u0442\u0430.")
        return

    positions = ["\u041f\u0440\u043e\u0448\u043b\u043e\u0435", "\u041d\u0430\u0441\u0442\u043e\u044f\u0449\u0435\u0435", "\u0411\u0443\u0434\u0443\u0449\u0435\u0435"]

    # Показываем карты
    for i, card in enumerate(cards):
        pos = positions[i] if i < 3 else f"\u041a\u0430\u0440\u0442\u0430 {i + 1}"
        is_rev = random.random() < 0.3
        text = format_card_with_position(card, is_rev, pos)

        img_buf = get_card_image(card.id, is_rev)
        if img_buf:
            photo = BufferedInputFile(img_buf.read(), filename=f"{card.id}.png")
            await message.answer_photo(photo=photo, caption=text)
        else:
            await message.answer(text)

    # Формируем контекст для GigaChat
    context = engine.build_reading_context(
        cards=cards,
        positions=positions,
        question=question,
        spread_type="three_cards",
    )
    prompt = engine.build_interpretation_prompt(context, spread_type="three_cards")

    # Отправляем на анализ
    interpretation = await adapt_text(prompt, user, context_type="tarot", temperature=0.7)

    await message.answer(f"\U0001f52e \u0422\u0440\u0430\u043a\u0442\u043e\u0432\u043a\u0430:\n\n{interpretation}")
    await save_history(user.id, "tarot_spread", f"Question: {question}\nCards: {[c.name_ru for c in cards]}")


@router.message(Command("tarot_love"))
async def cmd_tarot_love(message: Message):
    """Расклад на любовь."""
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    cards = engine.draw_random(3)
    if not cards:
        await message.answer("\u274c \u0411\u0430\u0437\u0430 \u0437\u043d\u0430\u043d\u0438\u0439 \u043f\u0443\u0441\u0442\u0430.")
        return

    positions = [
        "\u0412\u044b \u0432 \u043e\u0442\u043d\u043e\u0448\u0435\u043d\u0438\u044f\u0445",
        "\u041f\u0430\u0440\u0442\u043d\u0451\u0440",
        "\u041f\u043e\u0442\u0435\u043d\u0446\u0438\u0430\u043b",
    ]

    for i, card in enumerate(cards):
        pos = positions[i] if i < 3 else f"\u041a\u0430\u0440\u0442\u0430 {i + 1}"
        is_rev = random.random() < 0.3
        text = format_card_with_position(card, is_rev, pos)

        img_buf = get_card_image(card.id, is_rev)
        if img_buf:
            photo = BufferedInputFile(img_buf.read(), filename=f"{card.id}.png")
            await message.answer_photo(photo=photo, caption=text)
        else:
            await message.answer(text)

    # Контекст для трактовки
    love_context = "\n".join([
        "\u0422\u0435\u043c\u0430 \u0440\u0430\u0441\u043a\u043b\u0430\u0434\u0430: \u041b\u044e\u0431\u043e\u0432\u044c \u0438 \u043e\u0442\u043d\u043e\u0448\u0435\u043d\u0438\u044f",
        "",
        *[f"{positions[i]}: {cards[i].love}" for i in range(3)],
    ])

    interpretation = await adapt_text(love_context, user, context_type="tarot", temperature=0.7)
    await message.answer(f"\u2764\ufe0f \u0422\u0440\u0430\u043a\u0442\u043e\u0432\u043a\u0430 \u043d\u0430 \u043b\u044e\u0431\u043e\u0432\u044c:\n\n{interpretation}")
    await save_history(user.id, "tarot_love", "3 cards love spread")


# ===========================
# CALLBACK
# ===========================

@router.callback_query(lambda c: c.data and c.data.startswith("tarot_detail:"))
async def callback_tarot_detail(callback_query: CallbackQuery):
    """Подробное описание карты по callback."""
    parts = callback_query.data.split(":")
    card_id = parts[1]
    is_reversed = parts[2] == "1" if len(parts) > 2 else False

    card = engine.get_card(card_id)
    if not card:
        await callback_query.answer("\u274c \u041a\u0430\u0440\u0442\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430")
        return

    response = format_card_full(card, is_reversed)

    img_buf = get_card_image(card_id, is_reversed)
    if img_buf:
        photo = BufferedInputFile(img_buf.read(), filename=f"{card_id}.png")
        await callback_query.message.answer_photo(photo=photo, caption=response)
    else:
        await callback_query.message.answer(response)

    await callback_query.answer()


# ===========================
# HELPERS
# ===========================

async def save_history(user_id: int, command: str, result: str):
    """Сохраняет расклад в историю."""
    async with async_session() as session:
        history = History(user_id=user_id, command=command, result=result)
        session.add(history)
        await session.commit()
