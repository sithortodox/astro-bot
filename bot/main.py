import asyncio
import logging
import subprocess
import sys
import os
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiohttp import web

from bot.config import settings
from bot.handlers import start, tarot_astralis as tarot, numerology, horoscope, lunar, history, premium, admin
from bot.middlewares.user import UserMiddleware, RateLimitMiddleware
import bot.state as state

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler("logs/bot.log", maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler(),
    ],
)

payment_handler = RotatingFileHandler("logs/payments.log", maxBytes=5*1024*1024, backupCount=3)
payment_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
payment_logger = logging.getLogger("payment")
payment_logger.addHandler(payment_handler)
payment_logger.setLevel(logging.INFO)

error_handler = RotatingFileHandler("logs/errors.log", maxBytes=5*1024*1024, backupCount=3)
error_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
error_handler.setLevel(logging.ERROR)
logging.getLogger().addHandler(error_handler)

logger = logging.getLogger(__name__)


async def on_startup():
    subprocess.run([sys.executable, "-m", "alembic", "-c", "/app/alembic.ini", "upgrade", "head"], check=False)
    logger.info("Database migrations applied")


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    state.bot_instance = bot

    storage = RedisStorage.from_url(settings.redis_url)
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
