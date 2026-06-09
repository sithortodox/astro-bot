import hashlib
from datetime import date


HOROSCOPES = {
    "Овен": [
        "Today is favorable for new beginnings. Trust your instincts.",
        "A surprise awaits you in the afternoon. Stay open to possibilities.",
        "Financial matters require attention. Avoid impulsive decisions.",
    ],
    "Телец": [
        "Stability is your strength today. Build on existing foundations.",
        "A conversation with a close friend brings clarity.",
        "Romance is in the air. Express your feelings openly.",
    ],
    "Близнецы": [
        "Communication is key. Express your ideas clearly.",
        "A creative project gains momentum. Keep pushing forward.",
        "Travel plans may shift. Be flexible and patient.",
    ],
    "Рак": [
        "Home and family take priority. Nurture your closest bonds.",
        "Financial growth is possible through careful planning.",
        "Your intuition is strong today. Trust your inner voice.",
    ],
    "Лев": [
        "Leadership opportunities arise. Step into the spotlight.",
        "A creative idea deserves attention. Share it with others.",
        "Health needs focus. Take time for self-care.",
    ],
    "Дева": [
        "Details matter today. Your analytical skills are sharp.",
        "A work project reaches completion. Celebrate your efforts.",
        "Relationships benefit from honest communication.",
    ],
    "Весы": [
        "Balance is essential. Weigh your options carefully.",
        "A partnership offers new possibilities. Explore them.",
        "Artistic pursuits bring joy. Induce your creative side.",
    ],
    "Скорпион": [
        "Transformation is underway. Embrace the changes.",
        "Deep conversations reveal hidden truths.",
        "Financial opportunities emerge from unexpected sources.",
    ],
    "Стрелец": [
        "Adventure calls. Say yes to new experiences.",
        "Learning and growth are highlighted today.",
        "A philosophical insight guides your decisions.",
    ],
    "Козерог": [
        "Discipline pays off. Stay focused on long-term goals.",
        "A mentor offers valuable advice. Listen carefully.",
        "Professional recognition is within reach.",
    ],
    "Водолей": [
        "Innovation drives you forward. Think outside the box.",
        "Community involvement brings satisfaction.",
        "A unique opportunity arises. Don't hesitate.",
    ],
    "Рыбы": [
        "Dreams and reality merge. Follow your intuition.",
        "A creative project flows effortlessly.",
        "Emotional healing is possible today. Be gentle with yourself.",
    ],
}


def get_daily_horoscope(zodiac_sign: str) -> str:
    today = date.today()
    seed = int(hashlib.md5(f"{zodiac_sign}{today.isoformat()}".encode()).hexdigest(), 16)
    horoscopes = HOROSCOPES.get(zodiac_sign, HOROSCOPES["Овен"])
    index = seed % len(horoscopes)
    return horoscopes[index]
