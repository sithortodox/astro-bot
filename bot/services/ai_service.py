import httpx
import logging
import time
import uuid

from bot.config import settings

logger = logging.getLogger(__name__)

_token_cache: dict = {"token": None, "expires_at": 0}

PROMPTS = {
    "tarot": (
        "Ты — мистический таролог. Адаптируй это расклад таро для личной консультации. "
        "Сохрани основной смысл, но сделай его тёплым, личным и проникновенным. "
        "Добавь имя пользователя, если оно есть. Не меняй значение карты и ключевые слова. "
        "Пиши на русском. Не более 150 слов. "
        "Не используй markdown-разметку, звёздочки, решётки и специальные символы. "
        "Пиши простым текстом с эмодзи.\n\n{context}\n\n{content}"
    ),
    "numerology": (
        "Ты — мудрый нумеролог. Адаптируй это нумерологическое чтение для личной консультации. "
        "Сделай его воодушевляющим и проникновенным. Добавь имя пользователя, если оно есть. "
        "Не меняй числа и их основные значения. "
        "Пиши на русском. Не более 100 слов. "
        "Не используй markdown-разметку, звёздочки, решётки и специальные символы. "
        "Пиши простым текстом с эмодзи.\n\n{context}\n\n{content}"
    ),
    "horoscope": (
        "Ты — дружелюбный астролог. Адаптируй этот ежедневный гороскоп, чтобы он был тёплым и личным. "
        "Добавь имя пользователя и знак зодиака, если они есть. "
        "Сохрани основное предсказание, но сделай его личным сообщением. "
        "Пиши на русском. Не более 80 слов. "
        "Не используй markdown-разметку, звёздочки, решётки и специальные символы. "
        "Пиши простым текстом с эмодзи.\n\n{context}\n\n{content}"
    ),
    "lunar": (
        "Ты — добрый лунный гид. Адаптируй эту лунную рекомендацию, чтобы она была успокаивающей и полезной. "
        "Сделай её советом от мудрого друга. "
        "Пиши на русском. Не более 80 слов. "
        "Не используй markdown-разметку, звёздочки, решётки и специальные символы. "
        "Пиши простым текстом с эмодзи.\n\n{context}\n\n{content}"
    ),
    "general": (
        "Адаптируй этот текст, чтобы он был тёплым, личным и полезным. "
        "Добавь имя пользователя, если оно есть. Сохрани основной смысл. "
        "Пиши на русском. "
        "Не используй markdown-разметку, звёздочки, решётки и специальные символы. "
        "Пиши простым текстом с эмодзи.\n\n{context}\n\n{content}"
    ),
}


def strip_markdown(text: str) -> str:
    import re
    text = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', text)
    text = re.sub(r'_{1,2}(.+?)_{1,2}', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text.strip()


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


async def _get_access_token() -> str:
    if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            settings.gigachat_oauth_url,
            headers={
                "Authorization": f"Basic {settings.gigachat_api_key}",
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

    try:
        access_token = await _get_access_token()
    except Exception as e:
        logger.error(f"Failed to get GigaChat access token: {e}")
        return text

    headers = {
        "Authorization": f"Bearer {access_token}",
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
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.gigachat_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if result and len(result) > 20:
                        return strip_markdown(result)
                    logger.warning(f"GigaChat вернул короткий ответ (попытка {attempt + 1})")
                elif response.status_code == 401:
                    _token_cache["token"] = None
                    _token_cache["expires_at"] = 0
                    try:
                        access_token = await _get_access_token()
                        headers["Authorization"] = f"Bearer {access_token}"
                    except Exception:
                        pass
                    logger.warning(f"GigaChat токен истёк, получен новый (попытка {attempt + 1})")
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
        access_token = await _get_access_token()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.gigachat_url}/models",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return response.status_code == 200
    except Exception:
        return False
