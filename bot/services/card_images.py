from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import json
import math
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge_base"

SUIT_COLORS = {
    "wands": {"primary": (180, 60, 40), "secondary": (240, 160, 80), "accent": (255, 220, 150)},
    "cups": {"primary": (40, 100, 180), "secondary": (100, 180, 240), "accent": (200, 230, 255)},
    "swords": {"primary": (80, 80, 110), "secondary": (140, 140, 180), "accent": (200, 200, 240)},
    "pentacles": {"primary": (50, 130, 60), "secondary": (100, 190, 110), "accent": (180, 240, 180)},
    "major": {"primary": (100, 60, 140), "secondary": (160, 120, 200), "accent": (220, 200, 255)},
}

SUIT_SYMBOLS = {
    "wands": "\u2694",
    "cups": "\u2615",
    "swords": "\u2694\uFE0F",
    "pentacles": "\u2608",
    "major": "\u2B50",
}

CARD_NUMERALS = {
    0: "0", 1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
    11: "XI", 12: "XII", 13: "XIII", 14: "XIV", 15: "XV",
    16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX", 21: "XXI",
}


def _card_hash(card_id: str) -> int:
    h = hashlib.md5(card_id.encode()).hexdigest()
    return int(h[:8], 16)


def _extract_card_index(card_id: str) -> int:
    parts = card_id.split("_")
    for p in parts:
        if p.isdigit():
            return int(p)
    return 0


def load_cards() -> dict[str, dict]:
    cards = {}
    for f in ["tarot_major.json", "tarot_minor.json"]:
        path = KB_DIR / f
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                for card in json.load(fh):
                    cards[card["id"]] = card
    return cards


def draw_gradient(draw, width, height, color1, color2, angle_deg=0):
    angle = math.radians(angle_deg)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    max_dim = int(abs(width * cos_a) + abs(height * sin_a))
    cx, cy = width / 2, height / 2

    for y in range(-max_dim, max_dim):
        ratio = (y + max_dim) / (2 * max_dim)
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        x1 = int(cx + (y * sin_a - width * cos_a))
        y1 = int(cy - (y * cos_a + width * sin_a))
        x2 = int(cx + (y * sin_a + width * cos_a))
        y2 = int(cy - (y * cos_a - width * sin_a))
        draw.line([(x1, y1), (x2, y2)], fill=(r, g, b))


def draw_geometric_element(draw, cx, cy, size, shape_type, color, alpha=60):
    elem_color = (*color, alpha)
    if shape_type == 0:
        draw.ellipse([cx - size, cy - size, cx + size, cy + size], outline=elem_color, width=2)
    elif shape_type == 1:
        points = [(cx, cy - size), (cx + size, cy + size // 2), (cx - size, cy + size // 2)]
        draw.polygon(points, outline=elem_color)
    elif shape_type == 2:
        draw.rectangle([cx - size, cy - size, cx + size, cy + size], outline=elem_color, width=2)
    elif shape_type == 3:
        points = []
        for i in range(6):
            a = math.radians(i * 60 - 30)
            points.append((cx + int(size * math.cos(a)), cy + int(size * math.sin(a))))
        draw.polygon(points, outline=elem_color)
    elif shape_type == 4:
        for i in range(4):
            a = math.radians(i * 45)
            x1, y1 = cx + int(size * math.cos(a)), cy + int(size * math.sin(a))
            x2, y2 = cx + int(size * math.cos(a + math.pi)), cy + int(size * math.sin(a + math.pi))
            draw.line([(x1, y1), (x2, y2)], fill=elem_color, width=2)


def draw_ornate_border(draw, width, height, color, thickness=4, corner_style=0):
    draw.rectangle([4, 4, width - 5, height - 5], outline=color, width=thickness)
    draw.rectangle([10, 10, width - 11, height - 11], outline=color, width=2)

    corner_size = 15
    corners = [(10, 10), (width - 25, 10), (10, height - 25), (width - 25, height - 25)]
    if corner_style == 0:
        for cx, cy in corners:
            draw.ellipse([cx, cy, cx + corner_size, cy + corner_size], fill=color)
    elif corner_style == 1:
        for cx, cy in corners:
            draw.rectangle([cx, cy, cx + corner_size, cy + corner_size], fill=color)
    elif corner_style == 2:
        for cx, cy in corners:
            s = corner_size // 2
            draw.polygon([(cx + s, cy), (cx + corner_size, cy + corner_size), (cx, cy + corner_size)], fill=color)
    else:
        for cx, cy in corners:
            draw.ellipse([cx, cy, cx + corner_size, cy + corner_size], fill=color)
            draw.ellipse([cx + 3, cy + 3, cx + corner_size - 3, cy + corner_size - 3], fill=(255, 255, 255, 128))


def draw_suit_symbols(draw, cx, cy, suit, count, size, color):
    symbol = SUIT_SYMBOLS.get(suit, "\u2B50")
    actual_count = count if count > 0 else 1
    if actual_count == 1:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), symbol, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, cy - size // 2), symbol, fill=color, font=font)
    elif actual_count <= 10:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(size * 0.7))
        except OSError:
            font = ImageFont.load_default()
        cols = min(actual_count, 5)
        rows = (actual_count + cols - 1) // cols
        spacing_x = min(60, (300 - 40) // cols)
        spacing_y = min(50, 150 // max(rows, 1))
        start_y = cy - (rows - 1) * spacing_y // 2
        idx = 0
        for r in range(rows):
            items = min(cols, actual_count - idx)
            row_x = cx - (items - 1) * spacing_x // 2
            for c in range(items):
                sx = row_x + c * spacing_x
                sy = start_y + r * spacing_y
                bbox = draw.textbbox((0, 0), symbol, font=font)
                tw = bbox[2] - bbox[0]
                draw.text((sx - tw // 2, sy - size // 4), symbol, fill=color, font=font)
                idx += 1
    else:
        draw_suit_symbols(draw, cx, cy, suit, 1, size, color)


def draw_court_card_element(draw, cx, cy, court_type, color, size=40):
    if court_type == "page":
        draw.ellipse([cx - size, cy - size, cx + size, cy + size], outline=color, width=3)
        draw.ellipse([cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2], fill=color)
    elif court_type == "knight":
        points = [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
        draw.polygon(points, outline=color, width=3)
    elif court_type == "queen":
        for i in range(3):
            offset = i * 8
            draw.ellipse([cx - size + offset, cy - size + offset, cx + size - offset, cy + size - offset],
                         outline=color, width=2)
    elif court_type == "king":
        draw.rectangle([cx - size, cy - size, cx + size, cy + size], outline=color, width=3)
        draw.line([(cx - size, cy), (cx + size, cy)], fill=color, width=3)
        draw.line([(cx, cy - size), (cx, cy + size)], fill=color, width=3)


def generate_card_image(card: dict, is_reversed: bool = False) -> BytesIO:
    width, height = 400, 600
    card_id = card.get("id", "unknown")
    suit = card.get("suit") or "major"
    colors = SUIT_COLORS.get(suit, SUIT_COLORS["major"])
    ch = _card_hash(card_id)
    idx = _extract_card_index(card_id)

    img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    gradient_angle = (ch % 180) - 90
    r_shift = (ch % 40) - 20
    g_shift = ((ch >> 8) % 40) - 20
    b_shift = ((ch >> 16) % 40) - 20
    c1 = tuple(max(0, min(255, colors["secondary"][i] + r_shift if i == 0 else colors["secondary"][i] + g_shift if i == 1 else colors["secondary"][i] + b_shift)) for i in range(3))
    c2 = tuple(max(0, min(255, colors["primary"][i] + r_shift if i == 0 else colors["primary"][i] + g_shift if i == 1 else colors["primary"][i] + b_shift)) for i in range(3))
    draw_gradient(draw, width, height, c1, c2, gradient_angle)

    pattern_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pattern_draw = ImageDraw.Draw(pattern_layer)
    pattern_count = 3 + (ch % 4)
    for i in range(pattern_count):
        px = 40 + ((ch >> (i * 4)) % (width - 80))
        py = 40 + ((ch >> (i * 4 + 2)) % (height - 80))
        shape_type = (ch >> (i * 3)) % 5
        elem_size = 15 + ((ch >> (i * 2)) % 25)
        draw_geometric_element(pattern_draw, px, py, elem_size, shape_type, colors["accent"], alpha=35)
    img = Image.alpha_composite(img, pattern_layer)
    draw = ImageDraw.Draw(img)

    corner_style = ch % 4
    draw_ornate_border(draw, width, height, colors["accent"], corner_style=corner_style)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_reversed = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_numeral = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except OSError:
        font_large = font_name = font_small = font_reversed = font_numeral = ImageFont.load_default()

    cx, cy = width // 2, height // 2 - 60

    is_court = card_id.endswith(("page", "knight", "queen", "king"))
    is_numbered_minor = suit != "major" and not is_court

    if is_numbered_minor:
        num = idx + 1
        draw_suit_symbols(draw, cx, cy, suit, num, 36, colors["accent"])
    elif is_court:
        court_type = card_id.split("_")[-1]
        draw_court_card_element(draw, cx, cy, court_type, colors["accent"], size=45)
        symbol = SUIT_SYMBOLS.get(suit, "\u2B50")
        try:
            font_sym = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except OSError:
            font_sym = font_large
        bbox = draw.textbbox((0, 0), symbol, font=font_sym)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, cy - 20), symbol, fill=(255, 255, 255), font=font_sym)
    else:
        symbol = SUIT_SYMBOLS.get(suit, "\u2B50")
        bbox = draw.textbbox((0, 0), symbol, font=font_large)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, cy - 35), symbol, fill=(255, 255, 255), font=font_large)

    numeral = CARD_NUMERALS.get(idx, str(idx))
    if suit != "major" and not is_court:
        numeral = str(idx + 1) if idx + 1 <= 10 else numeral
    bbox = draw.textbbox((0, 0), numeral, font=font_numeral)
    tw = bbox[2] - bbox[0]
    numeral_y = cy + 90 if not is_numbered_minor else cy + 100
    numeral_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    numeral_draw = ImageDraw.Draw(numeral_layer)
    numeral_draw.rounded_rectangle(
        [cx - tw // 2 - 12, numeral_y - 5, cx + tw // 2 + 12, numeral_y + 35],
        radius=8, fill=(0, 0, 0, 80)
    )
    img = Image.alpha_composite(img, numeral_layer)
    draw = ImageDraw.Draw(img)
    draw.text((cx - tw // 2, numeral_y), numeral, fill=(255, 255, 255), font=font_numeral)

    name_ru = card.get("name_ru", card.get("name", "?"))
    words = name_ru.split()
    lines = []
    line = ""
    for w in words:
        test = f"{line} {w}".strip()
        bbox = draw.textbbox((0, 0), test, font=font_name)
        if bbox[2] - bbox[0] > width - 80:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)

    name_y = numeral_y + 45
    name_height = len(lines) * 24 + 12
    name_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    name_draw = ImageDraw.Draw(name_layer)
    name_draw.rounded_rectangle(
        [30, name_y - 5, width - 30, name_y + name_height],
        radius=8, fill=(0, 0, 0, 100)
    )
    img = Image.alpha_composite(img, name_layer)
    draw = ImageDraw.Draw(img)

    for ln in lines[:3]:
        bbox = draw.textbbox((0, 0), ln, font=font_name)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, name_y), ln, fill=(255, 255, 255), font=font_name)
        name_y += 24

    suit_labels = {
        "wands": "\u2694 \u0416\u0415\u0417\u041b\u042b",
        "cups": "\u2615 \u041a\u0423\u0411\u041a\u0418",
        "swords": "\u2694 \u041c\u0415\u0427\u0418",
        "pentacles": "\u2608 \u041f\u0415\u041d\u0422\u0410\u041a\u041b\u0418",
        "major": "\u2B50 \u0421\u0422\u0410\u0420\u0428\u0418\u0419 \u0410\u0420\u041a\u0410\u041d",
    }
    suit_label = suit_labels.get(suit, "")
    if suit_label:
        bbox = draw.textbbox((0, 0), suit_label, font=font_small)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, height - 60), suit_label, fill=colors["accent"], font=font_small)

    if is_reversed:
        reversed_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        reversed_draw = ImageDraw.Draw(reversed_layer)
        banner_y = height - 50
        reversed_draw.rounded_rectangle(
            [50, banner_y, width - 50, height - 20],
            radius=8, fill=(180, 40, 40, 220)
        )
        img = Image.alpha_composite(img, reversed_layer)
        draw = ImageDraw.Draw(img)
        reversed_text = "\u2B07 \u041F\u0415\u0420\u0415\u0412\u0401\u0420\u041d\u0423\u0422\u0410"
        bbox = draw.textbbox((0, 0), reversed_text, font=font_reversed)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, banner_y + 5), reversed_text, fill=(255, 255, 255), font=font_reversed)

    rgb_img = Image.new("RGB", (width, height), (255, 255, 255))
    rgb_img.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)

    buf = BytesIO()
    rgb_img.save(buf, format="PNG", quality=95)
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
        logger.error(f"Error generating card image: {e}", exc_info=True)
        return None
