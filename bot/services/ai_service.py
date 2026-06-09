import httpx
import logging

from bot.config import settings

logger = logging.getLogger(__name__)

# Prompt templates for different contexts
PROMPTS = {
    "tarot": (
        "You are a mystical tarot reader. Adapt this tarot reading for a personal consultation. "
        "Keep the core meaning but make it warm, personal, and insightful. "
        "Add the user's name if provided. Do not change the card meaning or keywords. "
        "Write in Russian. Keep it under 150 words.\n\n{context}\n\n{content}"
    ),
    "numerology": (
        "You are a wise numerologist. Adapt this numerology reading for a personal consultation. "
        "Make it encouraging and insightful. Add the user's name if provided. "
        "Do not change the numbers or their core meanings. "
        "Write in Russian. Keep it under 100 words.\n\n{context}\n\n{content}"
    ),
    "horoscope": (
        "You are a friendly astrologer. Adapt this daily horoscope to be warm and personal. "
        "Add the user's name and zodiac sign if provided. "
        "Keep the core prediction but make it feel like a personal message. "
        "Write in Russian. Keep it under 80 words.\n\n{context}\n\n{content}"
    ),
    "lunar": (
        "You are a gentle lunar guide. Adapt this lunar recommendation to be soothing and helpful. "
        "Make it feel like advice from a wise friend. "
        "Write in Russian. Keep it under 80 words.\n\n{context}\n\n{content}"
    ),
    "general": (
        "Adapt this text to be warm, personal, and helpful. "
        "Add the user's name if provided. Keep the core meaning. "
        "Write in Russian.\n\n{context}\n\n{content}"
    ),
}


def build_context(user=None, extra: str = "") -> str:
    parts = []
    if user:
        if user.first_name:
            parts.append(f"Name: {user.first_name}")
        if user.zodiac_sign:
            parts.append(f"Zodiac: {user.zodiac_sign}")
        if user.birth_date:
            parts.append(f"Birth date: {user.birth_date}")
    if extra:
        parts.append(extra)
    return "User info: " + ", ".join(parts) if parts else ""


async def adapt_text(
    text: str,
    user=None,
    context_type: str = "general",
    extra_context: str = "",
    temperature: float = 0.7,
    max_retries: int = 2,
) -> str:
    if not settings.ollama_url:
        return text

    context = build_context(user, extra_context)
    prompt_template = PROMPTS.get(context_type, PROMPTS["general"])
    prompt = prompt_template.format(context=context, content=text)

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "top_p": 0.9,
                            "num_predict": 200,
                        },
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    result = data.get("response", "").strip()
                    if result and len(result) > 20:
                        return result
                    logger.warning(f"Ollama returned short response (attempt {attempt + 1})")
                else:
                    logger.warning(f"Ollama returned status {response.status_code}")
        except httpx.ConnectError:
            logger.warning(f"Cannot connect to Ollama at {settings.ollama_url}")
            break
        except httpx.TimeoutException:
            logger.warning(f"Ollama timeout (attempt {attempt + 1})")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            break

    return text


async def check_ollama_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_url}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def list_models() -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        pass
    return []
