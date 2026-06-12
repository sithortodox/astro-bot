from datetime import date as _date


def reduce_to_single(n: int) -> int:
    while n > 9 and n != 11 and n != 22:
        n = sum(int(d) for d in str(n))
    return n


def _extract_date_parts(birth_date: _date | str) -> tuple[int, int, int]:
    if isinstance(birth_date, _date):
        return birth_date.day, birth_date.month, birth_date.year
    parts = birth_date.split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])


def calculate_life_path(birth_date: _date | str) -> int:
    day, month, year = _extract_date_parts(birth_date)
    total = sum(int(d) for d in f"{day:02d}{month:02d}{year}")
    return reduce_to_single(total)


def calculate_birth_day_number(birth_date: _date | str) -> int:
    day, _, _ = _extract_date_parts(birth_date)
    return reduce_to_single(day)


def calculate_soul_number(birth_time: str | None) -> int | None:
    if not birth_time:
        return None
    try:
        h, m = birth_time.split(":")
        total = int(h) + int(m)
        return reduce_to_single(total)
    except (ValueError, IndexError):
        return None


def calculate_personality_from_place(birth_place: str | None) -> int | None:
    if not birth_place:
        return None
    values = {
        "а": 1, "б": 2, "в": 3, "г": 4, "д": 5, "е": 6, "ё": 7,
        "ж": 8, "з": 9, "и": 1, "й": 2, "к": 3, "л": 4, "м": 5,
        "н": 6, "о": 7, "п": 8, "р": 9, "с": 1, "т": 2, "у": 3,
        "ф": 4, "х": 5, "ц": 6, "ч": 7, "ш": 8, "щ": 9, "ъ": 0,
        "ы": 1, "ь": 0, "э": 2, "ю": 3, "я": 4,
    }
    total = sum(values.get(c.lower(), 0) for c in birth_place if c.isalpha())
    return reduce_to_single(total) if total > 0 else None


def calculate_destiny_number(name: str) -> int:
    values = {
        "а": 1, "б": 2, "в": 3, "г": 4, "д": 5, "е": 6, "ё": 7,
        "ж": 8, "з": 9, "и": 1, "й": 2, "к": 3, "л": 4, "м": 5,
        "н": 6, "о": 7, "п": 8, "р": 9, "с": 1, "т": 2, "у": 3,
        "ф": 4, "х": 5, "ц": 6, "ч": 7, "ш": 8, "щ": 9, "ъ": 0,
        "ы": 1, "ь": 0, "э": 2, "ю": 3, "я": 4,
    }
    total = sum(values.get(c.lower(), 0) for c in name if c.isalpha())
    return reduce_to_single(total)


def calculate_personality_number(name: str) -> int:
    consonants = set("бвгджзйклмнпрстфхцчшщ")
    values = {
        "б": 2, "в": 3, "г": 4, "д": 5, "ж": 8, "з": 9, "й": 2,
        "к": 3, "л": 4, "м": 5, "н": 6, "п": 8, "р": 9, "с": 1,
        "т": 2, "ф": 4, "х": 5, "ц": 6, "ч": 7, "ш": 8, "щ": 9,
    }
    total = sum(values.get(c.lower(), 0) for c in name if c.lower() in consonants)
    return reduce_to_single(total)
