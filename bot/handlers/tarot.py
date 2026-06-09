import json
import random
from pathlib import Path
from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from bot.database import async_session
from bot.models import User, History
from bot.handlers.start import get_user, get_or_create_user
from bot.services.ai_service import adapt_text

router = Router()

KB_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge_base"


def load_tarot_cards() -> list[dict]:
    cards = []
    for f in ["tarot_major.json", "tarot_minor.json"]:
        path = KB_DIR / f
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                cards.extend(json.load(fh))
    return cards


def draw_card() -> tuple[dict, bool]:
    cards = load_tarot_cards()
    card = random.choice(cards)
    is_reversed = random.random() < 0.3
    return card, is_reversed


def draw_cards(count: int) -> list[tuple[dict, bool]]:
    cards = load_tarot_cards()
    drawn = random.sample(cards, min(count, len(cards)))
    return [(card, random.random() < 0.3) for card in drawn]


def format_card_short(card: dict, is_reversed: bool = False) -> str:
    prefix = "\u2b07\ufe0f " if is_reversed else ""
    meaning = card.get("reversed_meaning" if is_reversed else "upright_meaning", "")
    if len(meaning) > 180:
        meaning = meaning[:177] + "..."
    return f"{prefix}{card.get('name_ru', card.get('name', '?'))}\n\n{meaning}"


def format_card_full(card: dict, is_reversed: bool = False) -> str:
    prefix = "\u2b07\ufe0f \u041f\u0435\u0440\u0435\u0432\u0451\u0440\u043d\u0443\u0442\u0430\u044f " if is_reversed else ""
    meaning = card.get("reversed_meaning" if is_reversed else "upright_meaning", "")
    keywords = ", ".join(card.get("keywords", [])[:6])

    lines = [
        f"{prefix}{card.get('name_ru', card.get('name', '?'))}",
        "",
        meaning,
        "",
        f"\u2764\ufe0f Love: {card.get('love', 'N/A')}",
        f"\u2605 Career: {card.get('career', 'N/A')}",
        f"\u2728 Finance: {card.get('finance', 'N/A')}",
        "",
        f"\U0001f3af Keywords: {keywords}",
    ]
    return "\n".join(lines)


def format_card_with_position(card: dict, is_reversed: bool, position: str) -> str:
    emoji_map = {"Past": "\u23f0", "Present": "\u2714\ufe0f", "Future": "\U0001f52e"}
    emoji = emoji_map.get(position, "\u25b6")
    return f"{emoji} {position}\n{format_card_short(card, is_reversed)}"


@router.message(Command("tarot"))
async def cmd_tarot(message: Message):
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    card, is_reversed = draw_card()
    response = format_card_short(card, is_reversed)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\U0001f50d Detailed",
            callback_data=f"tarot_detail:{card['id']}:{1 if is_reversed else 0}"
        )]
    ])

    response = await adapt_text(response, user, context_type="tarot")
    await message.answer(response, reply_markup=keyboard)
    await save_history(user.id, "tarot", response)


@router.message(Command("tarot1"))
async def cmd_tarot1(message: Message):
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    card, is_reversed = draw_card()
    response = format_card_full(card, is_reversed)
    response = await adapt_text(response, user, context_type="tarot")
    await message.answer(response)
    await save_history(user.id, "tarot1", response)


@router.message(Command("tarot3"))
async def cmd_tarot3(message: Message):
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
    )

    drawn = draw_cards(3)
    positions = ["Past", "Present", "Future"]
    parts = []
    for i, (card, is_rev) in enumerate(drawn):
        pos = positions[i] if i < 3 else f"Card {i+1}"
        parts.append(format_card_with_position(card, is_rev, pos))
    response = "\n\n---\n\n".join(parts)
    response = await adapt_text(response, user, context_type="tarot")
    await message.answer(response)
    await save_history(user.id, "tarot3", response)


@router.callback_query(lambda c: c.data and c.data.startswith("tarot_detail:"))
async def callback_tarot_detail(callback_query: CallbackQuery):
    parts = callback_query.data.split(":")
    card_id = parts[1]
    is_reversed = parts[2] == "1"

    cards = load_tarot_cards()
    card = next((c for c in cards if c["id"] == card_id), None)

    if not card:
        await callback_query.answer("Card not found.")
        return

    response = format_card_full(card, is_reversed)
    await callback_query.message.answer(response)
    await callback_query.answer()


async def save_history(user_id: int, command: str, result: str):
    async with async_session() as session:
        history = History(user_id=user_id, command=command, result=result)
        session.add(history)
        await session.commit()
