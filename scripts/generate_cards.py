#!/usr/bin/env python3
"""
Скрипт генерации YAML-описаний карт Astralis Tarot через GigaChat API.

Использование:
    python scripts/generate_cards.py [--card-id w01] [--all] [--dry-run]

Требования:
    - GIGACHAT_API_KEY в .env или переменной окружения
    - Установленные зависимости: httpx, pyyaml, pydantic-settings
"""

import asyncio
import httpx
import json
import logging
import os
import re
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env
load_dotenv(Path(__file__).parent.parent / ".env")

import yaml

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Конфигурация
GIGACHAT_API_KEY = os.getenv("GIGACHAT_API_KEY", "")
GIGACHAT_URL = os.getenv("GIGACHAT_URL", "https://gigachat.devices.sberbank.ru/api/v1")
GIGACHAT_OAUTH_URL = os.getenv("GIGACHAT_OAUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat")

CATALOG_PATH = PROJECT_ROOT / "knowledge" / "astralis" / "cards_catalog.yaml"
OUTPUT_BASE = PROJECT_ROOT / "knowledge" / "astralis"

# Кэш токена
_token_cache = {"token": None, "expires_at": 0}


# ===========================
# ПРОМПТЫ
# ===========================

SYSTEM_PROMPT = """Ты — эксперт по таро и архетипам. Создай YAML-описание для карты авторской колоды Astralis Tarot.

Мир Astralis:
- Космическое пространство, где звёзды — живые сущности.
- Четыре Космических Потока: Огонь (Жезлы), Вода (Кубки), Воздух (Мечи), Земля (Пентакли).
- Старшие Арканы — Великие Звёзды и Звёзды Судьбы.
- Философия: каждый человек — звезда в теле, судьба — направление потока, выбор определяет траекторию.

Стиль трактовок: Практический, психологический. Конкретные советы без мистического жаргона.
Отвечай ТОЛЬКО валидным YAML. Никакого текста до или после YAML."""


def build_user_prompt(card: dict, world_context: str) -> str:
    return f"""Создай YAML-описание для карты:

ID: {card['id']}
Название: {card['name_ru']} ({card['name_en']})
Тип: {card.get('arcana', 'minor')}
Масть: {card.get('suit', 'none')}
Ранг: {card.get('rank', 'none')}
Тема: {card['theme']}
Стихия: {card.get('element', card.get('suit', 'ether'))}

{world_context}

Структура YAML (используй ТОЛЬКО эти поля, все числа — целые от 0 до 10):

id: "{card['id']}"
name_ru: "{card['name_ru']}"
name_en: "{card['name_en']}"
arcana: "{card.get('arcana', 'minor')}"
suit: "{card.get('suit', 'none')}"
rank: "{card.get('rank', 'none')}"
theme: "{card['theme']}"

archetypes:
  hero: 0
  sage: 0
  creator: 0
  ruler: 0
  explorer: 0
  lover: 0
  magician: 0
  rebel: 0
  caregiver: 0
  shadow: 0

metrics:
  activity: 0
  stability: 0
  intuition: 0
  transformation: 0
  spirituality: 0
  abundance: 0
  conflict: 0
  control: 0
  risk: 0
  creativity: 0
  leadership: 0
  harmony: 0
  communication: 0
  mystery: 0
  discipline: 0
  passion: 0
  wisdom: 0
  resilience: 0
  influence: 0
  destiny: 0

light_meaning: "Позитивное прямое значение"
shadow_meaning: "Негативное перевёрнутое значение"

love: "Трактовка в контексте любви и отношений"
career: "Трактовка в контексте карьеры"
money: "Трактовка в контексте финансов"
health: "Трактовка в контексте здоровья"
spirituality: "Трактовка в контексте духовного развития"

advice: "Практический совет"
warning: "Предупреждение"

symbols:
  - "Символ 1"
  - "Символ 2"
  - "Символ 3"

visual_markers:
  color: "Основной цвет"
  element: "Стихийный символ"
  number: "Числовое значение"

relations: null

jung:
  persona: "Внешнее проявление"
  shadow: "Теневая сторона"
  anima_animus: "Противоположное начало"
  self: "Интегрированное целое"

Заполни ВСЕ поля осмысленными значениями. Тексты на русском, 1-3 предложения."""


# ===========================
# GIGACHAT API
# ===========================

async def get_access_token() -> str:
    if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        response = await client.post(
            GIGACHAT_OAUTH_URL,
            headers={
                "Authorization": f"Basic {GIGACHAT_API_KEY}",
                "RqUID": str(uuid.uuid4()),
            },
            data={"scope": "GIGACHAT_API_PERS"},
        )
        response.raise_for_status()
        data = response.json()
        _token_cache["token"] = data["access_token"]
        _token_cache["expires_at"] = data["expires_at"] / 1000
        logger.info("GigaChat access token obtained")
        return _token_cache["token"]


async def generate_yaml_for_card(card: dict, world_context: str) -> dict | None:
    """Генерирует YAML-описание карты через GigaChat."""
    access_token = await get_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GIGACHAT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(card, world_context)},
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 2000,
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
                response = await client.post(
                    f"{GIGACHAT_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if result:
                        return parse_yaml_response(result)
                    logger.warning(f"Empty response for {card['id']} (attempt {attempt + 1})")
                elif response.status_code == 401:
                    _token_cache["token"] = None
                    _token_cache["expires_at"] = 0
                    access_token = await get_access_token()
                    headers["Authorization"] = f"Bearer {access_token}"
                    logger.warning(f"Token refreshed for {card['id']}")
                else:
                    logger.warning(f"GigaChat status {response.status_code} for {card['id']}: {response.text[:200]}")
        except httpx.ConnectError:
            logger.error(f"Connection error for {card['id']}")
            break
        except httpx.TimeoutException:
            logger.warning(f"Timeout for {card['id']} (attempt {attempt + 1})")
        except Exception as e:
            logger.error(f"Error for {card['id']}: {e}")
            break

    return None


def parse_yaml_response(text: str) -> dict | None:
    """Парсит YAML из ответа GigaChat."""
    # Убираем markdown-обёртку если есть
    text = re.sub(r'```yaml\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()

    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as e:
        logger.error(f"YAML parse error: {e}")
        # Пробуем исправить типичные ошибки
        text = text.replace('  - ', '  - "')
        text = text.replace('null', 'null')
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError:
            logger.error(f"Failed to parse YAML even after fixes")
            return None


def validate_card(card_data: dict, card_template: dict) -> bool:
    """Валидирует структуру YAML."""
    required_fields = ["id", "name_ru", "archetypes", "metrics", "light_meaning"]
    for field in required_fields:
        if field not in card_data:
            logger.warning(f"Missing field: {field}")
            return False

    # Валидация archetypes
    archetypes = card_data.get("archetypes", {})
    for key in ["hero", "sage", "creator", "ruler", "explorer"]:
        if key not in archetypes:
            logger.warning(f"Missing archetype: {key}")
            return False

    # Валидация metrics
    metrics = card_data.get("metrics", {})
    for key in ["activity", "stability", "intuition", "transformation", "spirituality"]:
        if key not in metrics:
            logger.warning(f"Missing metric: {key}")
            return False

    return True


# ===========================
# MAIN
# ===========================

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate Astralis Tarot card YAML descriptions")
    parser.add_argument("--card-id", help="Generate only this card (e.g., w01)")
    parser.add_argument("--all", action="store_true", help="Generate all cards")
    parser.add_argument("--dry-run", action="store_true", help="Don't save files")
    parser.add_argument("--start-from", help="Start from this card ID (for resuming)")
    args = parser.parse_args()

    if not GIGACHAT_API_KEY:
        logger.error("GIGACHAT_API_KEY not set. Set it in .env or environment.")
        sys.exit(1)

    # Загружаем каталог
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = yaml.safe_load(f)

    # Загружаем контекст мира
    world_path = OUTPUT_BASE / "mythology" / "world.yaml"
    with open(world_path, "r", encoding="utf-8") as f:
        world_data = yaml.safe_load(f)

    world_context = f"""Мифология мира:
- Поток Огня (Жезлы): созидание, воля, страсть. Управляющая звезда: Игнис.
- Поток Воды (Кубки): чувства, связи, интуиция. Управляющая звезда: Лунар.
- Поток Воздуха (Мечи): разум, истина, конфликт. Управляющая звезда: Зефир.
- Поток Земли (Пентакли): материя, ресурсы, тело. Управляющая звезда: Терра."""

    # Собираем все карты
    all_cards = list(catalog.get("major_arcana", []))
    for suit in ["wands", "cups", "swords", "pentacles"]:
        all_cards.extend(catalog.get(suit, []))

    # Фильтруем если нужно
    if args.card_id:
        all_cards = [c for c in all_cards if c["id"] == args.card_id]
        if not all_cards:
            logger.error(f"Card {args.card_id} not found in catalog")
            sys.exit(1)
    elif not args.all:
        # По умолчанию — все
        pass

    # Определяем стартовую позицию
    skip = args.start_from is not None
    start_id = args.start_from

    logger.info(f"Processing {len(all_cards)} cards...")

    generated = 0
    failed = 0
    skipped = 0

    for card in all_cards:
        if skip:
            if card["id"] == start_id:
                skip = False
            else:
                skipped += 1
                continue

        # Проверяем существует ли файл
        yaml_path = get_yaml_path(card)
        if yaml_path.exists() and not args.card_id:
            logger.info(f"Skipping {card['id']} ({card['name_ru']}) — file exists")
            skipped += 1
            continue

        logger.info(f"Generating {card['id']} ({card['name_ru']})...")
        card_data = await generate_yaml_for_card(card, world_context)

        if card_data is None:
            logger.error(f"Failed to generate {card['id']}")
            failed += 1
            continue

        if not validate_card(card_data, card):
            logger.error(f"Invalid structure for {card['id']}")
            failed += 1
            continue

        if args.dry_run:
            logger.info(f"[DRY RUN] Would save {card['id']} to {yaml_path}")
            print(yaml.dump(card_data, allow_unicode=True, default_flow_style=False))
        else:
            yaml_path.parent.mkdir(parents=True, exist_ok=True)
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(card_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved {card['id']} to {yaml_path}")

        generated += 1

        # Пауза чтобы не перегружать API
        await asyncio.sleep(1)

    logger.info(f"\nDone: {generated} generated, {failed} failed, {skipped} skipped")


def get_yaml_path(card: dict) -> Path:
    """Определяет путь для YAML-файла карты."""
    if card.get("arcana") == "major":
        return OUTPUT_BASE / "major_arcana" / f"{card['id']}_{card['name_en'].lower().replace(' ', '_')}.yaml"
    else:
        suit = card.get("suit", "unknown")
        return OUTPUT_BASE / "minor_arcana" / suit / f"{card['id']}_{card['name_en'].lower().replace(' ', '_')}.yaml"


if __name__ == "__main__":
    asyncio.run(main())
