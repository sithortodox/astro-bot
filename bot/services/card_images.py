from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import json
import math
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge_base"

SUIT_COLORS = {
    "wands": {"primary": (180, 60, 40), "secondary": (240, 160, 80), "accent": (255, 220, 150)},
    "cups": {"primary": (40, 100, 180), "secondary": (100, 180, 240), "accent": (200, 230, 255)},
    "swords": {"primary": (140, 130, 50), "secondary": (200, 190, 100), "accent": (255, 255, 180)},
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

SUIT_PATTERNS = {
    "wands": "wavy",
    "cups": "circles",
    "swords": "diagonal",
    "pentacles": "dots",
    "major": "stars",
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


def draw_gradient(draw, width, height, color1, color2, direction="vertical"):
    """Draw a gradient background"""
    for y in range(height):
        r = int(color1[0] + (color2[0] - color1[0]) * y / height)
        g = int(color1[1] + (color2[1] - color1[1]) * y / height)
        b = int(color1[2] + (color2[2] - color1[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def draw_pattern(draw, width, height, pattern_type, color, alpha=30):
    """Draw decorative pattern"""
    pattern_color = (*color, alpha)
    
    if pattern_type == "wavy":
        for y in range(0, height, 20):
            points = [(x, y + int(5 * math.sin(x / 20))) for x in range(0, width, 5)]
            if len(points) > 1:
                draw.line(points, fill=pattern_color, width=1)
    
    elif pattern_type == "circles":
        for y in range(30, height - 30, 40):
            for x in range(30, width - 30, 40):
                draw.ellipse([x - 8, y - 8, x + 8, y + 8], outline=pattern_color, width=1)
    
    elif pattern_type == "diagonal":
        for i in range(-height, width + height, 15):
            draw.line([(i, 0), (i + height, height)], fill=pattern_color, width=1)
    
    elif pattern_type == "dots":
        for y in range(20, height - 20, 25):
            for x in range(20, width - 20, 25):
                draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=pattern_color)
    
    elif pattern_type == "stars":
        for y in range(40, height - 40, 50):
            for x in range(40, width - 40, 50):
                # Draw a small star
                points = []
                for i in range(5):
                    angle = math.radians(i * 72 - 90)
                    px = x + int(8 * math.cos(angle))
                    py = y + int(8 * math.sin(angle))
                    points.append((px, py))
                    angle2 = math.radians(i * 72 + 36 - 90)
                    px2 = x + int(4 * math.cos(angle2))
                    py2 = y + int(4 * math.sin(angle2))
                    points.append((px2, py2))
                if len(points) > 2:
                    draw.polygon(points, outline=pattern_color)


def draw_ornate_border(draw, width, height, color, thickness=4):
    """Draw ornate border"""
    # Outer border
    draw.rectangle([4, 4, width - 5, height - 5], outline=color, width=thickness)
    
    # Inner border with gap
    draw.rectangle([10, 10, width - 11, height - 11], outline=color, width=2)
    
    # Corner ornaments
    corner_size = 15
    corners = [(10, 10), (width - 25, 10), (10, height - 25), (width - 25, height - 25)]
    for cx, cy in corners:
        draw.ellipse([cx, cy, cx + corner_size, cy + corner_size], fill=color)


def draw_symbol_circle(draw, cx, cy, radius, symbol, font, bg_color, text_color):
    """Draw symbol in a decorative circle"""
    # Shadow
    draw.ellipse([cx - radius + 3, cy - radius + 3, cx + radius + 3, cy + radius + 3], 
                 fill=(0, 0, 0, 50))
    
    # Circle gradient effect
    for r in range(radius, 0, -1):
        ratio = r / radius
        color = tuple(int(bg_color[i] * ratio + 255 * (1 - ratio)) for i in range(3))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    
    # Border
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], 
                 outline=(255, 255, 255), width=3)
    
    # Symbol
    bbox = draw.textbbox((0, 0), symbol, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 5), symbol, fill=text_color, font=font)


def generate_card_image(card: dict, is_reversed: bool = False) -> BytesIO:
    width, height = 400, 600
    suit = card.get("suit") or "major"
    colors = SUIT_COLORS.get(suit, SUIT_COLORS["major"])
    symbol = SUIT_SYMBOLS.get(suit, "\u2B50")
    pattern_type = SUIT_PATTERNS.get(suit, "stars")
    
    # Create image with transparency support
    img = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Background gradient
    draw_gradient(draw, width, height, colors["secondary"], colors["primary"])
    
    # Draw pattern
    pattern_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    pattern_draw = ImageDraw.Draw(pattern_layer)
    draw_pattern(pattern_draw, width, height, pattern_type, colors["accent"], alpha=40)
    img = Image.alpha_composite(img, pattern_layer)
    draw = ImageDraw.Draw(img)
    
    # Draw ornate border
    draw_ornate_border(draw, width, height, colors["accent"])
    
    # Load fonts
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_reversed = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except OSError:
        font_large = ImageFont.load_default()
        font_name = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_reversed = ImageFont.load_default()
    
    # Draw central symbol
    cx, cy = width // 2, height // 2 - 50
    radius = 90
    draw_symbol_circle(draw, cx, cy, radius, symbol, font_large, colors["secondary"], (255, 255, 255))
    
    # Draw card name
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
    
    # Draw name background
    name_y = cy + radius + 30
    name_height = len(lines) * 28 + 20
    name_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    name_draw = ImageDraw.Draw(name_layer)
    name_draw.rounded_rectangle(
        [30, name_y - 10, width - 30, name_y + name_height],
        radius=10,
        fill=(0, 0, 0, 100)
    )
    img = Image.alpha_composite(img, name_layer)
    draw = ImageDraw.Draw(img)
    
    # Draw name text
    for ln in lines[:3]:
        bbox = draw.textbbox((0, 0), ln, font=font_name)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, name_y), ln, fill=(255, 255, 255), font=font_name)
        name_y += 28
    
    # Draw suit label
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
        draw.text((cx - tw // 2, height - 80), suit_label, fill=colors["accent"], font=font_small)
    
    # Draw reversed indicator
    if is_reversed:
        reversed_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        reversed_draw = ImageDraw.Draw(reversed_layer)
        
        # Red banner at bottom
        banner_y = height - 50
        reversed_draw.rounded_rectangle(
            [50, banner_y, width - 50, height - 20],
            radius=8,
            fill=(180, 40, 40, 220)
        )
        img = Image.alpha_composite(img, reversed_layer)
        draw = ImageDraw.Draw(img)
        
        reversed_text = "\u2B07 \u041F\u0415\u0420\u0415\u0412\u0401\u0420\u041D\u0423\u0422\u0410"
        bbox = draw.textbbox((0, 0), reversed_text, font=font_reversed)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, banner_y + 5), reversed_text, fill=(255, 255, 255), font=font_reversed)
    
    # Convert to RGB for saving
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
