from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from sqlalchemy import select, func
from datetime import date

from bot.config import settings
from bot.database import async_session
from bot.models import User, History, Payment

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("\U0001f6e1\ufe0f Админ-панель доступна через кнопку \u00ab\U0001f6e1\ufe0f Админ\u00bb")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        premium_users = await session.scalar(
            select(func.count(User.id)).where(User.is_premium)
        )
        today = date.today()
        active_today = await session.scalar(
            select(func.count(User.id)).where(User.last_request_date == today)
        )
        total_requests = await session.scalar(select(func.sum(User.total_requests)))
        total_payments = await session.scalar(select(func.count(Payment.id)))

    text = (
        f"\U0001f4ca Статистика\n\n"
        f"\U0001f465 Всего пользователей: {total_users}\n"
        f"\U0001f48e Премиум: {premium_users}\n"
        f"\U0001f525 Активны сегодня: {active_today}\n"
        f"\U0001f4c8 Всего запросов: {total_requests or 0}\n"
        f"\U0001f4b3 Всего платежей: {total_payments or 0}"
    )
    await message.answer(text)


@router.message(Command("users"))
async def cmd_users(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).order_by(User.created_at.desc()).limit(20)
        )
        users = result.scalars().all()

    if not users:
        await message.answer("\U0001f4cb Пользователей пока нет")
        return

    lines = ["\U0001f465 Последние пользователи:\n"]
    for u in users:
        premium = "\U0001f48e" if u.is_premium else ""
        lines.append(
            f"  {u.telegram_id} | @{u.username or '?'} | "
            f"{u.first_name or '?'} | {u.zodiac_sign or '?'} {premium}"
        )

    await message.answer("\n".join(lines))


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return

    if not command.args:
        await message.answer("Используй: /broadcast Текст сообщения")
        return

    text = command.args

    async with async_session() as session:
        result = await session.execute(select(User.telegram_id))
        user_ids = [row[0] for row in result.all()]

    sent = 0
    failed = 0

    from bot.state import bot_instance
    if not bot_instance:
        await message.answer("\u26a0\ufe0f Бот не инициализирован")
        return
    for user_id in user_ids:
        try:
            await bot_instance.send_message(user_id, f"\U0001f4e2 Рассылка:\n\n{text}")
            sent += 1
        except Exception:
            failed += 1

    await message.answer(f"\u2705 Рассылка завершена\nОтправлено: {sent}\nОшибок: {failed}")


@router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return

    if not command.args:
        await message.answer("Используй: /ban USER_ID")
        return

    try:
        target_id = int(command.args)
    except ValueError:
        await message.answer("\u274c Неверный ID пользователя")
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == target_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.is_premium = False
            user.premium_until = None
            await session.commit()
            await message.answer(f"\U0001f6ab Пользователь {target_id} заблокирован")
        else:
            await message.answer("\u274c Пользователь не найден")


@router.message(Command("setpremium"))
async def cmd_setpremium(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return

    if not command.args:
        await message.answer("Используй: /setpremium USER_ID")
        return

    try:
        target_id = int(command.args)
    except ValueError:
        await message.answer("\u274c Неверный ID пользователя")
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == target_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.is_premium = True
            user.premium_until = "2030-12-31T23:59:59"
            await session.commit()
            await message.answer(f"\u2705 Премиум выдан пользователю {target_id}")
        else:
            await message.answer("\u274c Пользователь не найден")


@router.message(Command("revokepremium"))
async def cmd_revokepremium(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return

    if not command.args:
        await message.answer("Используй: /revokepremium USER_ID")
        return

    try:
        target_id = int(command.args)
    except ValueError:
        await message.answer("\u274c Неверный ID пользователя")
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == target_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.is_premium = False
            user.premium_until = None
            await session.commit()
            await message.answer(f"\u2705 Премиум отозван у пользователя {target_id}")
        else:
            await message.answer("\u274c Пользователь не найден")


@router.message(Command("logs"))
async def cmd_logs(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with async_session() as session:
        result = await session.execute(
            select(History).order_by(History.created_at.desc()).limit(10)
        )
        logs = result.scalars().all()

    if not logs:
        await message.answer("\U0001f4cb Логов пока нет")
        return

    lines = ["\U0001f4dc Последние действия:\n"]
    for log in logs:
        time = log.created_at.strftime("%d.%m %H:%M") if log.created_at else "?"
        lines.append(f"  [{time}] {log.command} (user: {log.user_id})")

    await message.answer("\n".join(lines))
