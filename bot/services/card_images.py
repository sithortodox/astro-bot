from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge_base"

SUIT_COLORS = {
    "wands": (220, 80, 60),
    "cups": (60, 120, 200),
    "swords": (180, 160, 60),
    "pentacles": (60, 160, 80),
    "major": (120, 80, 160),
}

SUIT_SYMBOLS = {
    "wands": "\u2694",
    "cups": "\u2615",
    "swords": "\u2694",
    "pentacles": "\u2608",
    "major": "\u2b50",
}


def load_cards() -> dict[str, dict]:
    cards = {}
    for f in ["tarot_major.json", "tarot_minor.json"]:
        path = KB_DIR / f
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                for card in json.load(fh):
                    cards[card["id"]] = card
    return cards


def generate_card_image(card: dict, is_reversed: bool = False) -> BytesIO:
    width, height = 400, 600
    suit = card.get("suit") or "major"
    base_color = SUIT_COLORS.get(suit, (100, 100, 100))
    symbol = SUIT_SYMBOLS.get(suit, "\u2b50")

    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    border_color = tuple(max(0, c - 40) for c in base_color)
    draw.rectangle([8, 8, width - 9, height - 9], outline=border_color, width=4)

    inner = tuple(min(255, c + 180) for c in base_color)
    draw.rectangle([16, 16, width - 17, height - 17], fill=inner)

    cx, cy = width // 2, height // 2 - 40
    r = 80
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=base_color, outline=border_color, width=3)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except OSError:
        font_large = ImageFont.load_default()
        font_name = ImageFont.load_default()
        font_label = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), symbol, font=font_large)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 10), symbol, fill=(255, 255, 255), font=font_large)

    name_ru = card.get("name_ru", card.get("name", "?"))
    words = name_ru.split()
    lines = []
    line = ""
    for w in words:
        test = f"{line} {w}".strip()
        bbox = draw.textbbox((0, 0), test, font=font_name)
        if bbox[2] - bbox[0] > width - 60:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)

    y = cy + r + 30
    for ln in lines[:3]:
        bbox = draw.textbbox((0, 0), ln, font=font_name)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, y), ln, fill=border_color, font=font_name)
        y += 28

    if is_reversed:
        label = "\u2b07\ufe0f \u041f\u0435\u0440\u0435\u0432\u0451\u0440\u043d\u0443\u0442\u0430"
        bbox = draw.textbbox((0, 0), label, font=font_label)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, height - 50), label, fill=(180, 40, 40), font=font_label)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


_all_cards = None


def get_card_image(card_id: str, is_reversed: bool = False) -> BytesIO | None:
    global _all_cards
    try:
        if _all_cards is None:
            _all_cards = load_cards()
            logger.info(f"Loaded {len(_all_cards)} cards from {KB_DIR}")
        card = _all_cards.get(card_id)
        if not card:
            logger.warning(f"Card not found: {card_id}")
            return None
        return generate_card_image(card, is_reversed)
    except Exception as e:
        logger.error(f"Error generating card image: {e}")
        return None
