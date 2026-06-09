import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.models import Base
from bot.database import engine
from bot.handlers import start, tarot, numerology, horoscope, lunar, history, premium, admin
from bot.middlewares.user import UserMiddleware, RateLimitMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

bot_instance = None


async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def main():
    global bot_instance

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    bot_instance = bot

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(UserMiddleware())
    dp.message.middleware(RateLimitMiddleware(max_free_requests=1))

    dp.include_routers(
        admin.router,
        start.router,
        tarot.router,
        numerology.router,
        horoscope.router,
        lunar.router,
        history.router,
        premium.router,
    )

    dp.startup.register(on_startup)

    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
