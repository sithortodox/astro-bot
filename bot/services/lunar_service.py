import ephem
from datetime import datetime, date, timedelta

# Cache for lunar data
_lunar_cache: dict = {}

PHASE_NAMES = {
    "new": "Новолуние",
    "waxing_crescent": "Растущий серп",
    "first_quarter": "Первая четверть",
    "waxing_gibbous": "Растущая луна",
    "full": "Полнолуние",
    "waning_gibbous": "Убывающая луна",
    "third_quarter": "Последняя четверть",
    "waning_crescent": "Убывающий серп",
}

PHASE_EMOJI = {
    "new": "\U0001f311",
    "waxing_crescent": "\U0001f312",
    "first_quarter": "\U0001f313",
    "waxing_gibbous": "\U0001f314",
    "full": "\U0001f315",
    "waning_gibbous": "\U0001f316",
    "third_quarter": "\U0001f317",
    "waning_crescent": "\U0001f318",
}


def get_lunar_phase(target_date: date | None = None) -> tuple[str, str, float]:
    if target_date is None:
        target_date = date.today()

    cache_key = target_date.isoformat()
    if cache_key in _lunar_cache:
        return _lunar_cache[cache_key]

    moon = ephem.Moon()
    moon.compute(datetime.combine(target_date, datetime.min.time()))

    illumination = moon.phase

    prev_moon = ephem.Moon()
    prev_moon.compute(datetime.combine(target_date - timedelta(days=1), datetime.min.time()))
    is_waxing = moon.phase >= prev_moon.phase

    if illumination < 1:
        phase_key = "new"
    elif illumination < 25:
        phase_key = "waxing_crescent" if is_waxing else "waning_crescent"
    elif illumination < 50:
        phase_key = "first_quarter" if is_waxing else "third_quarter"
    elif illumination < 75:
        phase_key = "waxing_gibbous" if is_waxing else "waning_gibbous"
    elif illumination < 99:
        phase_key = "full"
    else:
        phase_key = "waning_gibbous"

    phase_name = PHASE_NAMES[phase_key]
    phase_emoji = PHASE_EMOJI[phase_key]

    result = (phase_name, phase_emoji, illumination)
    _lunar_cache[cache_key] = result
    return result


def get_moon_sign(target_date: date | None = None) -> str:
    if target_date is None:
        target_date = date.today()

    moon = ephem.Moon()
    moon.compute(datetime.combine(target_date, datetime.min.time()))

    constellations = [
        ("\u2648 Овен"), ("\u2649 Телец"), ("\u264a Близнецы"),
        ("\u264b Рак"), ("\u264c Лев"), ("\u264d Дева"),
        ("\u264e Весы"), ("\u264f Скорпион"), ("\u2650 Стрелец"),
        ("\u2651 Козерог"), ("\u2652 Водолей"), ("\u2653 Рыбы"),
    ]

    ra_hours = moon.ra * 12 / (2 * 3.14159)
    index = int(ra_hours / 2) % 12
    return constellations[index]


def get_next_full_moon(from_date: date | None = None) -> date:
    if from_date is None:
        from_date = date.today()

    moon = ephem.Moon()
    current = from_date

    for i in range(30):
        check_date = current + timedelta(days=i)
        moon.compute(datetime.combine(check_date, datetime.min.time()))
        if moon.phase > 98:
            return check_date

    return from_date + timedelta(days=14)


def get_next_new_moon(from_date: date | None = None) -> date:
    if from_date is None:
        from_date = date.today()

    moon = ephem.Moon()
    current = from_date

    for i in range(30):
        check_date = current + timedelta(days=i)
        moon.compute(datetime.combine(check_date, datetime.min.time()))
        if moon.phase < 2:
            return check_date

    return from_date + timedelta(days=14)


def get_lunar_calendar(days: int = 7) -> list[dict]:
    today = date.today()
    calendar = []

    for i in range(days):
        current_date = today + timedelta(days=i)
        phase_name, phase_emoji, illumination = get_lunar_phase(current_date)
        moon_sign = get_moon_sign(current_date)

        calendar.append({
            "date": current_date.isoformat(),
            "date_display": current_date.strftime("%d.%m"),
            "phase": phase_name,
            "emoji": phase_emoji,
            "illumination": round(illumination),
            "moon_sign": moon_sign,
        })

    return calendar


LUNAR_RECOMMENDATIONS = {
    "Новолуние": {
        "general": (
            "\U0001f311 Новолуние — время новых начинаний!\n\n"
            "Загадывай намерения на месяц вперёд. Медитируй над своими целями. "
            "Это мощное время для посадки семян новых проектов."
        ),
        "love": "Идеально для привлечения новой любви или обновления отношений.",
        "career": "Идеальное время для запуска новых проектов и постановки карьерных целей.",
        "finance": "Хорошее время для финансового планирования и накопления.",
        "health": "Отдыхай и восстанавливайся. Планируй новые режимы тренировок.",
    },
    "Растущий серп": {
        "general": (
            "\U0001f312 Растущий серп — энергия нарастает!\n\n"
            "Действуй согласно своим планам. Это время роста и расширения. "
            "Сосредоточься на личном развитии и обучении."
        ),
        "love": "Бери инициативу в любви. Открыто выражай свои чувства.",
        "career": "Двигайся вперёд с проектами. Появляются новые возможности.",
        "finance": "Хорошее время для инвестиций и приумножения средств.",
        "health": "Начинай новые тренировки. Уровень энергии растёт.",
    },
    "Первая четверть": {
        "general": (
            "\U0001f313 Первая четверть — могут возникнуть трудности!\n\n"
            "Будь настойчив и преодолевай препятствия. "
            "Это время для принятия решений и решения проблем."
        ),
        "love": "Прямо решай проблемы в отношениях. Общение — ключ ко всему.",
        "career": "Преодолевай профессиональные трудности. Доверяй своим силам.",
        "finance": "Пересмотри бюджет и внеси необходимые коррективы.",
        "health": "Преодолевай плато в тренировках. Будь постоянен.",
    },
    "Растущая луна": {
        "general": (
            "\U0001f314 Растущая луна — уточняй свой подход!\n\n"
            "Корректируй планы по мере необходимости. Сосредоточься на деталях. "
            "Терпение приведёт к прорыву."
        ),
        "love": "Углубляй связь через совместные занятия.",
        "career": "Дорабатывай проекты перед завершением. Внимание к деталям важно.",
        "finance": "Пересмотри инвестиции. Вноси небольшие коррективы.",
        "health": "Точечно настраивай свой режим для оптимальных результатов.",
    },
    "Полнолуние": {
        "general": (
            "\U0001f315 Полнолуние — завершение и празднование!\n\n"
            "Пожинай плоды своих трудов. Эмоции на высоте. "
            "Это время для общения и единения с близкими."
        ),
        "love": "Страстная романтическая энергия. Празднуй любовь.",
        "career": "Завершение проектов и признание. Делись своим успехом.",
        "finance": "Финансовый урожай. Наслаждайся плодами своего труда.",
        "health": "Высокая энергия. Отлично для интенсивных тренировок.",
    },
    "Убывающая луна": {
        "general": (
            "\U0001f316 Убывающая луна — время поделиться мудростью!\n\n"
            "Благодари и делись знаниями. Отпускай то, что тебе уже не нужно. "
            "Сосредоточься на обучении и наставничестве."
        ),
        "love": "Делись мудростью с партнёром. Размышляй об уроках отношений.",
        "career": "Наставляй других. Завершай документацию.",
        "finance": "Планируй будущее. Сокращай ненужные расходы.",
        "health": "Постепенно снижай нагрузку. Сосредоточься на восстановлении.",
    },
}


def get_lunar_recommendation(phase_name: str, category: str = "general") -> str:
    phase_data = LUNAR_RECOMMENDATIONS.get(phase_name, {})
    return phase_data.get(category, phase_data.get("general", "Следуй своей интуиции сегодня."))


def get_daily_lunar_summary() -> str:
    phase_name, phase_emoji, illumination = get_lunar_phase()
    moon_sign = get_moon_sign()
    next_full = get_next_full_moon()
    next_new = get_next_new_moon()

    days_to_full = (next_full - date.today()).days
    days_to_new = (next_new - date.today()).days

    rec = get_lunar_recommendation(phase_name, "general")

    lines = [
        f"{phase_emoji} Лунная сводка на {date.today().strftime('%d.%m.%Y')}",
        "",
        f"Фаза: {phase_name} ({illumination:.0f}%)",
        f"Луна в: {moon_sign}",
        "",
        f"Следующее полнолуние: {next_full.strftime('%d.%m')} (через {days_to_full} дн.)",
        f"Следующее новолуние: {next_new.strftime('%d.%m')} (через {days_to_new} дн.)",
        "",
        rec,
    ]

    return "\n".join(lines)
