import json
from pathlib import Path


KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"


def test_tarot_major_exists():
    path = KB_DIR / "tarot_major.json"
    assert path.exists(), "tarot_major.json not found"


def test_tarot_minor_exists():
    path = KB_DIR / "tarot_minor.json"
    assert path.exists(), "tarot_minor.json not found"


def test_tarot_major_count():
    path = KB_DIR / "tarot_major.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 22, f"Expected 22 major arcana, got {len(data)}"


def test_tarot_minor_count():
    path = KB_DIR / "tarot_minor.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 56, f"Expected 56 minor arcana, got {len(data)}"


def test_card_fields():
    required = ["id", "name", "name_ru", "upright_meaning", "reversed_meaning", "keywords"]
    for filename in ["tarot_major.json", "tarot_minor.json"]:
        path = KB_DIR / filename
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for card in data:
            for field in required:
                assert field in card, f"Card {card.get('id', '?')} missing {field}"


def test_numerology_service():
    from bot.services.numerology_service import calculate_life_path, reduce_to_single

    assert reduce_to_single(123) == 6
    assert reduce_to_single(999) == 9
    assert calculate_life_path("01.01.2000") > 0


def test_horoscope_service():
    from bot.services.horoscope_service import get_daily_horoscope

    horoscope = get_daily_horoscope("Овен")
    assert len(horoscope) > 0


def test_lunar_service():
    from bot.services.lunar_service import get_lunar_phase, get_lunar_recommendation

    phase_name, emoji, illumination = get_lunar_phase()
    assert phase_name in ["New Moon", "Waxing Crescent", "First Quarter",
                          "Waxing Gibbous", "Full Moon", "Waning Gibbous"]
    assert 0 <= illumination <= 100

    rec = get_lunar_recommendation(phase_name)
    assert len(rec) > 0
