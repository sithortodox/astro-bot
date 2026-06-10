import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from bot.config import settings
from bot.models import Base
from bot.database import engine
from bot.handlers import start, tarot, numerology, horoscope, lunar, history, premium, admin
from bot.middlewares.user import UserMiddleware, RateLimitMiddleware
import bot.state as state

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    state.bot_instance = bot

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

    if settings.webhook_url:
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

        app = web.Application()
        SimpleRequestHandler(dp, bot, secret_token=settings.webhook_secret).register(app, path="/webhook")
        setup_application(app, dp, bot=bot)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        await site.start()

        await bot.set_webhook(
            url=f"{settings.webhook_url}/webhook",
            secret_token=settings.webhook_secret,
        )
        logger.info(f"Webhook set to {settings.webhook_url}/webhook")
        await asyncio.Event().wait()
    else:
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        finally:
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
