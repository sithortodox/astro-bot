import httpx
import logging

from bot.config import settings

logger = logging.getLogger(__name__)

PROMPTS = {
    "tarot": (
        "Ты — мистический таролог. Адаптируй это расклад таро для личной консультации. "
        "Сохрани основной смысл, но сделай его тёплым, личным и проникновенным. "
        "Добавь имя пользователя, если оно есть. Не меняй значение карты и ключевые слова. "
        "Пиши на русском. Не более 150 слов.\n\n{context}\n\n{content}"
    ),
    "numerology": (
        "Ты — мудрый нумеролог. Адаптируй это нумерологическое чтение для личной консультации. "
        "Сделай его воодушевляющим и проникновенным. Добавь имя пользователя, если оно есть. "
        "Не меняй числа и их основные значения. "
        "Пиши на русском. Не более 100 слов.\n\n{context}\n\n{content}"
    ),
    "horoscope": (
        "Ты — дружелюбный астролог. Адаптируй этот ежедневный гороскоп, чтобы он был тёплым и личным. "
        "Добавь имя пользователя и знак зодиака, если они есть. "
        "Сохрани основное предсказание, но сделай его личным сообщением. "
        "Пиши на русском. Не более 80 слов.\n\n{context}\n\n{content}"
    ),
    "lunar": (
        "Ты — добрый лунный гид. Адаптируй эту лунную рекомендацию, чтобы она была успокаивающей и полезной. "
        "Сделай её советом от мудрого друга. "
        "Пиши на русском. Не более 80 слов.\n\n{context}\n\n{content}"
    ),
    "general": (
        "Адаптируй этот текст, чтобы он был тёплым, личным и полезным. "
        "Добавь имя пользователя, если оно есть. Сохрани основной смысл. "
        "Пиши на русском.\n\n{context}\n\n{content}"
    ),
}


def build_context(user=None, extra: str = "") -> str:
    parts = []
    if user:
        if user.first_name:
            parts.append(f"Имя: {user.first_name}")
        if user.zodiac_sign:
            parts.append(f"Знак зодиака: {user.zodiac_sign}")
        if user.birth_date:
            parts.append(f"Дата рождения: {user.birth_date}")
    if extra:
        parts.append(extra)
    return "Информация о пользователе: " + ", ".join(parts) if parts else ""


async def adapt_text(
    text: str,
    user=None,
    context_type: str = "general",
    extra_context: str = "",
    temperature: float = 0.7,
    max_retries: int = 2,
) -> str:
    if not settings.gigachat_api_key:
        return text

    context = build_context(user, extra_context)
    prompt_template = PROMPTS.get(context_type, PROMPTS["general"])
    prompt = prompt_template.format(context=context, content=text)

    headers = {
        "Authorization": f"Bearer {settings.gigachat_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.gigachat_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "top_p": 0.9,
        "max_tokens": 200,
    }

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(
                    f"{settings.gigachat_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if result and len(result) > 20:
                        return result
                    logger.warning(f"GigaChat вернул короткий ответ (попытка {attempt + 1})")
                else:
                    logger.warning(f"GigaChat вернул статус {response.status_code}: {response.text[:200]}")
        except httpx.ConnectError:
            logger.warning(f"Не удалось подключиться к GigaChat: {settings.gigachat_url}")
            break
        except httpx.TimeoutException:
            logger.warning(f"GigaChat таймаут (попытка {attempt + 1})")
        except Exception as e:
            logger.error(f"GigaChat ошибка: {e}")
            break

    return text


async def check_gigachat_health() -> bool:
    if not settings.gigachat_api_key:
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.get(
                f"{settings.gigachat_url}/models",
                headers={"Authorization": f"Bearer {settings.gigachat_api_key}"},
            )
            return response.status_code == 200
    except Exception:
        return False
