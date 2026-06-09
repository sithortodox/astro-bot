from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from sqlalchemy import select, func
from datetime import date

from bot.config import settings
from bot.database import async_session
from bot.models import User, History, Payment

router = Router()

ADMIN_IDS = [int(x) for x in settings.admin_ids] if settings.admin_ids else []


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Access denied.")
        return

    text = (
        " Admin Panel\n\n"
        " /stats - Statistics\n"
        " /users - User list\n"
        " /broadcast <text> - Broadcast message\n"
        " /ban <user_id> - Ban user\n"
        " /unban <user_id> - Unban user\n"
        " /setpremium <user_id> - Grant premium\n"
        " /revokepremium <user_id> - Revoke premium\n"
        " /logs - Recent logs"
    )
    await message.answer(text)


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        premium_users = await session.scalar(
            select(func.count(User.id)).where(User.is_premium)
        )
        today = date.today().isoformat()
        active_today = await session.scalar(
            select(func.count(User.id)).where(User.last_request_date == today)
        )
        total_requests = await session.scalar(select(func.sum(User.total_requests)))
        total_payments = await session.scalar(select(func.count(Payment.id)))

    text = (
        " Statistics\n\n"
        f" Total users: {total_users}\n"
        f" Premium users: {premium_users}\n"
        f" Active today: {active_today}\n"
        f" Total requests: {total_requests or 0}\n"
        f" Total payments: {total_payments or 0}"
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
        await message.answer("No users found.")
        return

    lines = [" Recent Users:\n"]
    for u in users:
        premium = "\U0001f451" if u.is_premium else ""
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
        await message.answer("Usage: /broadcast <text>")
        return

    text = command.args

    async with async_session() as session:
        result = await session.execute(select(User.telegram_id))
        user_ids = [row[0] for row in result.all()]

    sent = 0
    failed = 0

    from bot.main import bot_instance
    for user_id in user_ids:
        try:
            await bot_instance.send_message(user_id, f" Broadcast:\n\n{text}")
            sent += 1
        except Exception:
            failed += 1

    await message.answer(f"Broadcast complete.\nSent: {sent}\nFailed: {failed}")


@router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return

    if not command.args:
        await message.answer("Usage: /ban <user_id>")
        return

    try:
        target_id = int(command.args)
    except ValueError:
        await message.answer("Invalid user ID.")
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
            await message.answer(f"User {target_id} has been banned.")
        else:
            await message.answer("User not found.")


@router.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return

    if not command.args:
        await message.answer("Usage: /unban <user_id>")
        return

    try:
        target_id = int(command.args)
    except ValueError:
        await message.answer("Invalid user ID.")
        return

    await message.answer(f"User {target_id} has been unbanned.")


@router.message(Command("setpremium"))
async def cmd_setpremium(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return

    if not command.args:
        await message.answer("Usage: /setpremium <user_id>")
        return

    try:
        target_id = int(command.args)
    except ValueError:
        await message.answer("Invalid user ID.")
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
            await message.answer(f"Premium granted to {target_id}.")
        else:
            await message.answer("User not found.")


@router.message(Command("revokepremium"))
async def cmd_revokepremium(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return

    if not command.args:
        await message.answer("Usage: /revokepremium <user_id>")
        return

    try:
        target_id = int(command.args)
    except ValueError:
        await message.answer("Invalid user ID.")
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
            await message.answer(f"Premium revoked from {target_id}.")
        else:
            await message.answer("User not found.")


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
        await message.answer("No logs found.")
        return

    lines = [" Recent Logs:\n"]
    for log in logs:
        time = log.created_at.strftime("%d.%m %H:%M") if log.created_at else "?"
        lines.append(f"  [{time}] {log.command} (user: {log.user_id})")

    await message.answer("\n".join(lines))
