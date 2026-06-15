"""
Semantic Engine для колоды Astralis Tarot.

Загружает YAML-базу знаний, анализирует параметры карт,
вычисляет связи и формирует контекст для GigaChat.
"""

import logging
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

ASTRALIS_DIR = Path(__file__).parent.parent.parent / "knowledge" / "astralis"


@dataclass
class Archetypes:
    hero: int = 0
    sage: int = 0
    creator: int = 0
    ruler: int = 0
    explorer: int = 0
    lover: int = 0
    magician: int = 0
    rebel: int = 0
    caregiver: int = 0
    shadow: int = 0

    def dominant(self, top_n: int = 3) -> list[tuple[str, int]]:
        d = vars(self)
        return sorted(d.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def intensity(self) -> float:
        d = vars(self)
        return sum(d.values()) / len(d) if d else 0


@dataclass
class Metrics:
    activity: int = 0
    stability: int = 0
    intuition: int = 0
    transformation: int = 0
    spirituality: int = 0
    abundance: int = 0
    conflict: int = 0
    control: int = 0
    risk: int = 0
    creativity: int = 0
    leadership: int = 0
    harmony: int = 0
    communication: int = 0
    mystery: int = 0
    discipline: int = 0
    passion: int = 0
    wisdom: int = 0
    resilience: int = 0
    influence: int = 0
    destiny: int = 0

    def dominant(self, top_n: int = 5) -> list[tuple[str, int]]:
        d = vars(self)
        return sorted(d.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def energy_profile(self) -> dict[str, float]:
        """Возвращает профиль энергии по категориям."""
        return {
            "dynamic": (self.activity + self.passion + self.risk) / 3,
            "stable": (self.stability + self.discipline + self.harmony) / 3,
            "intellectual": (self.wisdom + self.communication + self.influence) / 3,
            "spiritual": (self.spirituality + self.intuition + self.transformation) / 3,
            "material": (self.abundance + self.leadership + self.resilience) / 3,
        }


@dataclass
class CardData:
    id: str
    name_ru: str
    name_en: str
    arcana: str  # "major" или "minor"
    suit: str  # "wands", "cups", "swords", "pentacles", "none"
    rank: str  # "ace"-"ten", "page", "knight", "queen", "king", "none"
    theme: str
    archetypes: Archetypes
    metrics: Metrics
    light_meaning: str
    shadow_meaning: str
    love: str
    career: str
    money: str
    health: str
    spirituality: str
    advice: str
    warning: str
    symbols: list[str]
    visual_markers: dict
    jung: dict

    @property
    def is_major(self) -> bool:
        return self.arcana == "major"

    @property
    def element(self) -> str:
        elements = {"wands": "fire", "cups": "water", "swords": "air", "pentacles": "earth"}
        return elements.get(self.suit, "ether")


class AstralisEngine:
    """Движок трактовок Astralis Tarot."""

    def __init__(self):
        self.cards: dict[str, CardData] = {}
        self._loaded = False

    def load(self) -> None:
        """Загружает все YAML-файлы карт."""
        if self._loaded:
            return

        # Загружаем старшие арканы
        major_dir = ASTRALIS_DIR / "major_arcana"
        if major_dir.exists():
            for yaml_file in sorted(major_dir.glob("*.yaml")):
                self._load_card(yaml_file)

        # Загружаем младшие арканы
        for suit in ["wands", "cups", "swords", "pentacles"]:
            suit_dir = ASTRALIS_DIR / "minor_arcana" / suit
            if suit_dir.exists():
                for yaml_file in sorted(suit_dir.glob("*.yaml")):
                    self._load_card(yaml_file)

        self._loaded = True
        logger.info(f"Loaded {len(self.cards)} Astralis cards")

    def _load_card(self, path: Path) -> None:
        """Загружает один YAML-файл карты."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "id" not in data:
                logger.warning(f"Invalid card file: {path}")
                return

            arch = data.get("archetypes", {})
            met = data.get("metrics", {})
            markers = data.get("visual_markers", {})
            if isinstance(markers, str):
                markers = {}

            self.cards[data["id"]] = CardData(
                id=data["id"],
                name_ru=data.get("name_ru", ""),
                name_en=data.get("name_en", ""),
                arcana=data.get("arcana", "minor"),
                suit=data.get("suit", "none"),
                rank=data.get("rank", "none"),
                theme=data.get("theme", ""),
                archetypes=Archetypes(**{k: v for k, v in arch.items() if k in Archetypes.__dataclass_fields__}),
                metrics=Metrics(**{k: v for k, v in met.items() if k in Metrics.__dataclass_fields__}),
                light_meaning=data.get("light_meaning", ""),
                shadow_meaning=data.get("shadow_meaning", ""),
                love=data.get("love", ""),
                career=data.get("career", ""),
                money=data.get("money", ""),
                health=data.get("health", ""),
                spirituality=data.get("spirituality", ""),
                advice=data.get("advice", ""),
                warning=data.get("warning", ""),
                symbols=data.get("symbols", []),
                visual_markers=markers,
                jung=data.get("jung", {}),
            )
        except Exception as e:
            logger.error(f"Failed to load card {path}: {e}")

    def get_card(self, card_id: str) -> Optional[CardData]:
        """Получает карту по ID."""
        self.load()
        return self.cards.get(card_id)

    def get_cards_by_ids(self, card_ids: list[str]) -> list[CardData]:
        """Получает список карт по ID."""
        self.load()
        return [self.cards[cid] for cid in card_ids if cid in self.cards]

    def draw_random(self, count: int = 1) -> list[CardData]:
        """Вытасчивает случайные карты."""
        import random
        self.load()
        return random.sample(list(self.cards.values()), min(count, len(self.cards)))

    # ===========================
    # АНАЛИЗ СВЯЗЕЙ
    # ===========================

    def compute_compatibility(self, card1: CardData, card2: CardData) -> dict:
        """Вычисляет совместимость двух карт."""
        # Совместимость по стихиям
        element_compat = {
            ("fire", "air"): 0.8,
            ("fire", "fire"): 0.6,
            ("fire", "water"): 0.3,
            ("fire", "earth"): 0.4,
            ("water", "earth"): 0.8,
            ("water", "water"): 0.6,
            ("water", "air"): 0.3,
            ("air", "air"): 0.6,
            ("air", "earth"): 0.4,
            ("earth", "earth"): 0.8,
            ("ether", "fire"): 0.7,
            ("ether", "water"): 0.7,
            ("ether", "air"): 0.7,
            ("ether", "earth"): 0.7,
        }

        e1, e2 = card1.element, card2.element
        elem_score = element_compat.get((e1, e2), element_compat.get((e2, e1), 0.5))

        # Совместимость по архетипам
        a1, a2 = card1.archetypes.dominant(3), card2.archetypes.dominant(3)
        arch_names1 = {a[0] for a in a1}
        arch_names2 = {a[0] for a in a2}
        overlap = len(arch_names1 & arch_names2)
        arch_score = 0.5 + (overlap * 0.15)

        # Совместимость по метрикам (средняя разница)
        m1 = vars(card1.metrics)
        m2 = vars(card2.metrics)
        total_diff = sum(abs(m1.get(k, 0) - m2.get(k, 0)) for k in m1)
        max_diff = len(m1) * 10
        metric_score = 1.0 - (total_diff / max_diff) if max_diff > 0 else 0.5

        overall = (elem_score * 0.4 + arch_score * 0.3 + metric_score * 0.3)

        return {
            "overall": round(overall, 2),
            "element_score": round(elem_score, 2),
            "archetype_score": round(arch_score, 2),
            "metric_score": round(metric_score, 2),
            "compatibility_level": self._level_from_score(overall),
        }

    def _level_from_score(self, score: float) -> str:
        if score >= 0.8:
            return "Отличная совместимость"
        elif score >= 0.6:
            return "Хорошая совместимость"
        elif score >= 0.4:
            return "Нейтральная совместимость"
        else:
            return "Низкая совместимость"

    # ===========================
    # ФОРМИРОВАНИЕ КОНТЕКСТА
    # ===========================

    def build_reading_context(
        self,
        cards: list[CardData],
        positions: list[str] | None = None,
        question: str = "",
        spread_type: str = "single",
    ) -> str:
        """Формирует контекст для GigaChat на основе карт."""
        self.load()

        parts = ["Расклад колоды Astralis Tarot:\n"]

        for i, card in enumerate(cards):
            pos = positions[i] if positions and i < len(positions) else f"Карта {i + 1}"
            direction = "прямая"  # Пока все карты прямые

            parts.append(f"--- {pos} ({card.name_ru}) ---")
            parts.append(f"Стихия: {card.element}, Масть: {card.suit}")

            if direction == "перевёрнутая":
                parts.append(f"Значение (перевёрнутая): {card.shadow_meaning}")
            else:
                parts.append(f"Значение (прямая): {card.light_meaning}")

            parts.append(f"Тема: {card.theme}")

            # Доминирующие архетипы
            dom_arch = card.archetypes.dominant(3)
            arch_str = ", ".join(f"{name}({val})" for name, val in dom_arch)
            parts.append(f"Архетипы: {arch_str}")

            # Доминирующие метрики
            dom_met = card.metrics.dominant(5)
            met_str = ", ".join(f"{name}({val})" for name, val in dom_met)
            parts.append(f"Ключевые метрики: {met_str}")

            # Контекстные трактовки
            if card.love:
                parts.append(f"Любовь: {card.love}")
            if card.career:
                parts.append(f"Карьера: {card.career}")
            if card.money:
                parts.append(f"Финансы: {card.money}")

            parts.append(f"Совет: {card.advice}")
            parts.append(f"Предупреждение: {card.warning}")
            parts.append("")

        # Анализ связей между картами
        if len(cards) > 1:
            parts.append("--- Анализ связей ---")
            for i in range(len(cards)):
                for j in range(i + 1, len(cards)):
                    compat = self.compute_compatibility(cards[i], cards[j])
                    parts.append(
                        f"{cards[i].name_ru} + {cards[j].name_ru}: "
                        f"{compat['compatibility_level']} ({compat['overall']})"
                    )
            parts.append("")

        if question:
            parts.append(f"Вопрос: {question}")
            parts.append("")

        return "\n".join(parts)

    def build_interpretation_prompt(self, context: str, spread_type: str = "single") -> str:
        """Формирует промпт для GigaChat."""
        return (
            "Ты — опытный таролог, работающий с авторской колодой Astralis Tarot.\n"
            "Стиль: практический, психологический. Конкретные советы без мистического жаргона.\n"
            "Говори温暖но, но по делу.\n\n"
            "Используй ТОЛЬКО русский язык. Ни одного английского слова.\n\n"
            f"Тип расклада: {spread_type}\n\n"
            f"{context}\n\n"
            "Сформируй трактовку расклада. Не более 300 слов. "
            "Без markdown, простой текст с эмодзи."
        )

    # ===========================
    # АНАЛИЗ ВОПРОСА
    # ===========================

    def classify_question(self, question: str) -> str:
        """Определяет категорию вопроса для выбора контекстных трактовок."""
        question_lower = question.lower()

        love_keywords = [
            "любовь", "отношения", "пар", "муж", "жена", "partner",
            "семья", "брак", "свадьба", "роман", "чувства",
        ]
        career_keywords = [
            "работ", "карьер", "должност", "бизнес", "проект",
            "начальник", "коллег", "офис", "компания",
        ]
        money_keywords = [
            "денег", "деньг", "финанс", "зарплат", "доход",
            "инвестиц", "кредит", "долг", "покупк",
        ]
        health_keywords = [
            "здоров", "болезн", "врач", "лечени", "диагноз",
            "организм", "самочувстви",
        ]
        spiritual_keywords = [
            "духовн", "развити", "медитац", "йог", "сознан",
            "смысл жизни", "карма", "энерги",
        ]

        for kw in love_keywords:
            if kw in question_lower:
                return "love"
        for kw in career_keywords:
            if kw in question_lower:
                return "career"
        for kw in money_keywords:
            if kw in question_lower:
                return "money"
        for kw in health_keywords:
            if kw in question_lower:
                return "health"
        for kw in spiritual_keywords:
            if kw in question_lower:
                return "spirituality"

        return "general"

    def get_category_reading(self, card: CardData, category: str) -> str:
        """Возвращает контекстную трактовку для категории."""
        readings = {
            "love": card.love,
            "career": card.career,
            "money": card.money,
            "health": card.health,
            "spirituality": card.spirituality,
        }
        return readings.get(category, card.light_meaning)


# Глобальный экземпляр
engine = AstralisEngine()
