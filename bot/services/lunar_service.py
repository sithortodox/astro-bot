import ephem
from datetime import datetime, date, timedelta

# Cache for lunar data
_lunar_cache: dict = {}


def get_lunar_phase(target_date: date | None = None) -> tuple[str, str, float]:
    if target_date is None:
        target_date = date.today()

    cache_key = target_date.isoformat()
    if cache_key in _lunar_cache:
        return _lunar_cache[cache_key]

    moon = ephem.Moon()
    moon.compute(datetime.combine(target_date, datetime.min.time()))

    illumination = moon.phase

    if illumination < 1:
        phase_name = "New Moon"
        phase_emoji = "\U0001f311"
    elif illumination < 25:
        phase_name = "Waxing Crescent"
        phase_emoji = "\U0001f312"
    elif illumination < 50:
        phase_name = "First Quarter"
        phase_emoji = "\U0001f313"
    elif illumination < 75:
        phase_name = "Waxing Gibbous"
        phase_emoji = "\U0001f314"
    elif illumination < 99:
        phase_name = "Full Moon"
        phase_emoji = "\U0001f315"
    else:
        phase_name = "Waning Gibbous"
        phase_emoji = "\U0001f316"

    result = (phase_name, phase_emoji, illumination)
    _lunar_cache[cache_key] = result
    return result


def get_moon_sign(target_date: date | None = None) -> str:
    if target_date is None:
        target_date = date.today()

    moon = ephem.Moon()
    moon.compute(datetime.combine(target_date, datetime.min.time()))

    constellations = [
        ("Aries", "\u2648"), ("Taurus", "\u2649"), ("Gemini", "\u264a"),
        ("Cancer", "\u264b"), ("Leo", "\u264c"), ("Virgo", "\u264d"),
        ("Libra", "\u264e"), ("Scorpio", "\u264f"), ("Sagittarius", "\u2650"),
        ("Capricorn", "\u2651"), ("Aquarius", "\u2652"), ("Pisces", "\u2653"),
    ]

    ra_hours = moon.ra * 12 / (2 * 3.14159)
    index = int(ra_hours / 2) % 12
    name, emoji = constellations[index]
    return f"{emoji} {name}"


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
            "date_display": current_date.strftime("%d.%m (%a)"),
            "phase": phase_name,
            "emoji": phase_emoji,
            "illumination": round(illumination),
            "moon_sign": moon_sign,
        })

    return calendar


LUNAR_RECOMMENDATIONS = {
    "New Moon": {
        "general": (
            "\U0001f311 New Moon - Time for new beginnings!\n\n"
            "Set intentions for the coming month. Meditate on your goals. "
            "This is a powerful time for planting seeds of new projects."
        ),
        "love": "Perfect for manifesting new love or refreshing existing relationships.",
        "career": "Ideal for launching new projects or setting career goals.",
        "finance": "Good for financial planning and setting savings goals.",
        "health": "Rest and recharge. Plan new health routines.",
    },
    "Waxing Crescent": {
        "general": (
            "\U0001f312 Waxing Crescent - Energy is building!\n\n"
            "Take action on your plans. This is a time of growth and expansion. "
            "Focus on personal development and learning."
        ),
        "love": "Take initiative in love. Express your feelings openly.",
        "career": "Move forward with projects. New opportunities arise.",
        "finance": "Good time for investments and financial growth.",
        "health": "Start new exercise routines. Energy levels are rising.",
    },
    "First Quarter": {
        "general": (
            "\U0001f313 First Quarter - Challenges may arise!\n\n"
            "Stay persistent and face obstacles head-on. "
            "This is a time for decision-making and problem-solving."
        ),
        "love": "Address relationship challenges directly. Communication is key.",
        "career": "Overcome professional obstacles. Trust your abilities.",
        "finance": "Review budgets and make necessary adjustments.",
        "health": "Push through exercise plateaus. Stay consistent.",
    },
    "Waxing Gibbous": {
        "general": (
            "\U0001f314 Waxing Gibbous - Refine your approach!\n\n"
            "Adjust plans as needed. Focus on details and analysis. "
            "Patience will lead to breakthroughs."
        ),
        "love": "Deepen connections through shared activities.",
        "career": "Polish projects before completion. Attention to detail matters.",
        "finance": "Review investments. Make small adjustments.",
        "health": "Fine-tune your health routine for optimal results.",
    },
    "Full Moon": {
        "general": (
            "\U0001f315 Full Moon - Culmination and celebration!\n\n"
            "Harvest your efforts. Emotions run high. "
            "This is a time for sharing and community."
        ),
        "love": "Passionate romantic energy. Celebrate love.",
        "career": "Project completion and recognition. Share your success.",
        "finance": "Financial harvest. Enjoy the fruits of your labor.",
        "health": "High energy. Great for intensive workouts.",
    },
    "Waning Gibbous": {
        "general": (
            "\U0001f316 Waning Gibbous - Time to share wisdom!\n\n"
            "Give thanks and share knowledge. Release what no longer serves you. "
            "Focus on teaching and mentoring."
        ),
        "love": "Share wisdom with your partner. Reflect on relationship lessons.",
        "career": "Mentor others. Complete documentation.",
        "finance": "Plan for future. Reduce unnecessary expenses.",
        "health": "Gradual wind-down. Focus on recovery.",
    },
}


def get_lunar_recommendation(phase_name: str, category: str = "general") -> str:
    phase_data = LUNAR_RECOMMENDATIONS.get(phase_name, {})
    return phase_data.get(category, phase_data.get("general", "Follow your intuition today."))


def get_daily_lunar_summary() -> str:
    phase_name, phase_emoji, illumination = get_lunar_phase()
    moon_sign = get_moon_sign()
    next_full = get_next_full_moon()
    next_new = get_next_new_moon()

    days_to_full = (next_full - date.today()).days
    days_to_new = (next_new - date.today()).days

    rec = get_lunar_recommendation(phase_name, "general")

    lines = [
        f"{phase_emoji} Lunar Summary for {date.today().strftime('%d.%m.%Y')}",
        "",
        f"Phase: {phase_name} ({illumination:.0f}%)",
        f"Moon in: {moon_sign}",
        "",
        f"Next Full Moon: {next_full.strftime('%d.%m')} (in {days_to_full} days)",
        f"Next New Moon: {next_new.strftime('%d.%m')} (in {days_to_new} days)",
        "",
        rec,
    ]

    return "\n".join(lines)
